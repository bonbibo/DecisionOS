import warnings
from pathlib import Path

import pytest

from app.engine import load_playbooks, load_profiles
from app.vault import VaultReader

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"


def test_read_for_role_yazici_gets_only_taktikler():
    ctx = VaultReader(VAULT_DIR).read_for_role("yazici")
    assert ctx.warnings == []
    paths = [d.path for d in ctx.documents]
    assert paths == [
        "01-Playbooks/taktikler/TK-001-rakip-teklif.md",
        "01-Playbooks/taktikler/TK-002-kosul-takasi.md",
        "01-Playbooks/taktikler/TK-003-sessizlik-deadline.md",
    ]


def test_read_for_role_stratejist_gets_playbook_and_taktikler():
    ctx = VaultReader(VAULT_DIR).read_for_role("stratejist")
    paths = {d.path for d in ctx.documents}
    assert "01-Playbooks/kira-bae.md" in paths
    assert "01-Playbooks/taktikler/TK-001-rakip-teklif.md" in paths
    # 06-Kararlar/, 07-Fiyatlama/ are also in stratejist's manifest scope.
    assert "07-Fiyatlama/kira-bae.md" in paths


def test_read_for_role_analist_gets_karsi_taraf():
    ctx = VaultReader(VAULT_DIR).read_for_role("analist")
    paths = [d.path for d in ctx.documents]
    # 08-Musteri-Profilleri has real content as of PR-D (segmentler.md).
    assert paths == ["04-Karsi-Taraf/profiller.md", "08-Musteri-Profilleri/segmentler.md"]
    profiller = next(d for d in ctx.documents if d.path == "04-Karsi-Taraf/profiller.md")
    assert profiller.frontmatter is None  # profiller.md has no frontmatter


def test_read_for_role_unknown_role_returns_empty_context_with_warning():
    ctx = VaultReader(VAULT_DIR).read_for_role("does-not-exist")
    assert ctx.documents == []
    assert len(ctx.warnings) == 1
    assert "does-not-exist" in ctx.warnings[0]


def test_read_folder_missing_path_warns_without_crashing(tmp_path):
    (tmp_path / "_manifest.md").write_text(
        "---\nroles:\n  stratejist: [\"01-Playbooks\", \"99-Missing\"]\n---\n", encoding="utf-8"
    )
    (tmp_path / "01-Playbooks").mkdir()
    (tmp_path / "01-Playbooks" / "a.md").write_text("---\nplaybook_id: PB-x\n---\nbody", encoding="utf-8")

    ctx = VaultReader(tmp_path).read_for_role("stratejist")

    assert len(ctx.documents) == 1
    assert any("99-Missing" in w for w in ctx.warnings)


def test_read_folder_mixed_frontmatter_and_plain_files(tmp_path):
    folder = tmp_path / "mixed"
    folder.mkdir()
    (folder / "with-fm.md").write_text("---\nkey: value\n---\nbody text", encoding="utf-8")
    (folder / "without-fm.md").write_text("just plain markdown, no frontmatter", encoding="utf-8")

    ctx = VaultReader(tmp_path).read_folder("mixed")

    by_name = {Path(d.path).name: d for d in ctx.documents}
    assert by_name["with-fm.md"].frontmatter == {"key": "value"}
    assert by_name["with-fm.md"].body == "body text"
    assert by_name["without-fm.md"].frontmatter is None
    assert by_name["without-fm.md"].body == "just plain markdown, no frontmatter"


def test_documents_are_sorted_deterministically(tmp_path):
    folder = tmp_path / "order"
    folder.mkdir()
    for name in ["zzz.md", "aaa.md", "mmm.md"]:
        (folder / name).write_text("no frontmatter", encoding="utf-8")

    ctx = VaultReader(tmp_path).read_folder("order")

    assert [Path(d.path).name for d in ctx.documents] == ["aaa.md", "mmm.md", "zzz.md"]


def test_load_playbooks_wrapper_matches_vaultreader_and_warns():
    with pytest.warns(DeprecationWarning):
        playbooks = load_playbooks(VAULT_DIR)

    assert len(playbooks) == 1
    assert playbooks[0].playbook_id == "PB-kira-bae"

    direct = VaultReader(VAULT_DIR).read_folder("01-Playbooks", recursive=False)
    assert len(direct.documents) == 1
    assert direct.documents[0].frontmatter["playbook_id"] == playbooks[0].playbook_id


def test_load_profiles_wrapper_matches_vaultreader_and_warns():
    with pytest.warns(DeprecationWarning):
        profiles = load_profiles(VAULT_DIR)

    assert {p.profile_id for p in profiles} == {"A1", "A2", "A3"}

    direct = VaultReader(VAULT_DIR).read_folder("04-Karsi-Taraf", recursive=False)
    assert len(direct.documents) == 1
    assert direct.documents[0].frontmatter is None


def test_load_playbooks_and_load_profiles_do_not_warn_by_default_outside_pytest_warns():
    # Sanity check that the warning is a real DeprecationWarning, not silently swallowed.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_playbooks(VAULT_DIR)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
