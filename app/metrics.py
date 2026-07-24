from pathlib import Path

from app.engine import load_retros, load_tactics


def _format_ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "—"
    return f"%{numerator / denominator * 100:.0f}"


def render_dashboard(vault_dir: Path | str = "vault") -> str:
    """Render vault/05-Metrikler/dashboard.md content from retro + tactic frontmatter."""
    vault_dir = Path(vault_dir)
    retros = load_retros(vault_dir)
    tactics = load_tactics(vault_dir)

    total_cases = len(retros)
    closed = [r for r in retros if r.sonuc == "kapandi"]
    win_rate = _format_ratio(len(closed), total_cases)
    avg_savings = (
        f"{sum(r.tasarruf for r in closed) / len(closed):.0f} {closed[0].tasarruf_para_birimi}"
        if closed
        else "—"
    )
    avg_rounds = f"{sum(r.tur_sayisi for r in retros) / total_cases:.1f}" if total_cases else "—"

    lines = [
        "# Metrikler",
        "",
        "| Metrik | Değer |",
        "|---|---|",
        f"| Toplam vaka | {total_cases} |",
        f"| Kapanan | {len(closed)} |",
        f"| Kazanma oranı | {win_rate} |",
        f"| Ortalama tasarruf | {avg_savings} |",
        f"| Ortalama tur sayısı | {avg_rounds} |",
        "",
        "## Taktik skorları",
        "Kütüphaneci her retro sonrası frontmatter'lardan derler.",
        "",
        "| Taktik | Kullanım | Başarı | Oran |",
        "|---|---|---|---|",
    ]
    for tactic in sorted(tactics, key=lambda t: t.taktik_id):
        oran = _format_ratio(tactic.basari_sayisi, tactic.kullanilma_sayisi)
        lines.append(f"| {tactic.taktik_id} | {tactic.kullanilma_sayisi} | {tactic.basari_sayisi} | {oran} |")
    lines.append("")

    return "\n".join(lines)


def write_dashboard(vault_dir: Path | str = "vault") -> Path:
    """Render the dashboard and write it to vault/05-Metrikler/dashboard.md."""
    vault_dir = Path(vault_dir)
    output_path = vault_dir / "05-Metrikler" / "dashboard.md"
    output_path.write_text(render_dashboard(vault_dir), encoding="utf-8")
    return output_path
