"""VaultReader: the single gateway for reading vault/ content (draft).

Per SYSTEM UPDATE v2 ("Vault-Driven Decision Engine"): no subagent or module
should open a vault file directly — every read goes through VaultReader, and
which folders a role may see is declared in vault/_manifest.md, not hardcoded
here. Hot-reload: every call re-reads the manifest and documents from disk
(no caching in V1), so a vault change takes effect on the next call/turn.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_VAULT_DIR = Path("vault")
MANIFEST_FILENAME = "_manifest.md"

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a vault note into its YAML frontmatter dict and markdown body.

    Frontmatter-less notes get an empty dict, not None, so callers can keep
    doing `if "key" not in meta` without a None-check; VaultReader converts
    an empty dict to None when building a VaultDocument, matching the
    documented `frontmatter: dict | None` contract for that structure.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    raw_meta, body = match.groups()
    meta = yaml.safe_load(raw_meta) or {}
    return meta, body.strip()


@dataclass
class VaultDocument:
    path: str  # relative to the vault root, e.g. "01-Playbooks/kira-bae.md"
    frontmatter: dict | None
    body: str


@dataclass
class VaultContext:
    documents: list[VaultDocument] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def exclude_inactive_decisions(self) -> "VaultContext":
        """A copy with any vault/06-Kararlar/*.md note dropped unless it's
        `durum: aktif` — a draft or cancelled decision shouldn't influence a
        live subagent call, even if its folder is in the caller's manifest scope."""
        kept = [
            d
            for d in self.documents
            if not d.path.startswith("06-Kararlar/") or (d.frontmatter or {}).get("durum") == "aktif"
        ]
        return VaultContext(documents=kept, warnings=list(self.warnings))

    def to_dict(self) -> dict:
        """JSON-serializable form for embedding in a subagent payload."""
        return {
            "documents": [
                {"path": d.path, "frontmatter": d.frontmatter, "body": d.body}
                for d in self.documents
            ],
            "warnings": self.warnings,
        }


class VaultReader:
    """Reads vault/ content per the role -> folder mapping in vault/_manifest.md."""

    def __init__(self, vault_dir: Path | str = DEFAULT_VAULT_DIR):
        self.vault_dir = Path(vault_dir)

    def _read_manifest_roles(self) -> dict[str, list[str]]:
        manifest_path = self.vault_dir / MANIFEST_FILENAME
        if not manifest_path.exists():
            logger.warning("vault manifest not found at %s", manifest_path)
            return {}
        meta, _ = parse_frontmatter(manifest_path.read_text(encoding="utf-8"))
        roles = meta.get("roles")
        if not roles:
            logger.warning("vault manifest at %s has no 'roles' frontmatter key", manifest_path)
            return {}
        return roles

    def read_for_role(self, role: str) -> VaultContext:
        """Read every document across all folders assigned to `role` in the manifest."""
        roles = self._read_manifest_roles()
        folders = roles.get(role)

        if folders is None:
            message = f"unknown role '{role}' — not listed in {MANIFEST_FILENAME}"
            logger.warning(message)
            return VaultContext(warnings=[message])

        context = VaultContext()
        for folder in folders:
            sub = self.read_folder(folder, recursive=True)
            context.documents.extend(sub.documents)
            context.warnings.extend(sub.warnings)

        context.documents.sort(key=lambda d: d.path)
        return context

    def read_folder(self, folder: str, recursive: bool = True) -> VaultContext:
        """Read every *.md document directly under (or, if recursive, nested within) `folder`."""
        folder_path = self.vault_dir / folder
        context = VaultContext()

        if not folder_path.exists():
            message = f"vault path not found: {folder}"
            logger.warning(message)
            context.warnings.append(message)
            return context

        pattern = "**/*.md" if recursive else "*.md"
        paths = sorted(folder_path.glob(pattern)) if folder_path.is_dir() else [folder_path]

        for path in paths:
            meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            context.documents.append(
                VaultDocument(
                    path=str(path.relative_to(self.vault_dir)),
                    frontmatter=meta or None,
                    body=body,
                )
            )

        context.documents.sort(key=lambda d: d.path)
        return context
