import shutil
from pathlib import Path

from app.engine import load_profiles, load_retros
from app.metrics import render_dashboard, write_dashboard

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"


def test_load_profiles_reads_all_archetypes_from_the_vault():
    profiles = load_profiles(VAULT_DIR)
    ids = {p.profile_id for p in profiles}
    assert ids == {"A1", "A2", "A3"}

    a2 = next(p for p in profiles if p.profile_id == "A2")
    assert a2.ad == "Bireysel ev sahibi (tek mülk)"
    assert "TK-003" in a2.body


def test_load_retros_is_empty_on_the_real_vault():
    # 03-Retros/ has no case history yet; the loader must not choke on that.
    assert load_retros(VAULT_DIR) == []


def test_load_retros_parses_frontmatter(tmp_path):
    retros_dir = tmp_path / "03-Retros"
    retros_dir.mkdir()
    (retros_dir / "r1.md").write_text(
        """---
retro_id: RT-001
case: "[[case-0001]]"
sonuc: kapandi
tasarruf: 5000
tasarruf_para_birimi: AED
tur_sayisi: 3
sure_gun: 4
yazan: kutuphaneci-agent
guncelleme: 2026-07-24
---

# Retro: case-0001
""",
        encoding="utf-8",
    )

    retros = load_retros(tmp_path)
    assert len(retros) == 1
    retro = retros[0]
    assert retro.retro_id == "RT-001"
    assert retro.sonuc == "kapandi"
    assert retro.tasarruf == 5000
    assert retro.tur_sayisi == 3


def test_render_dashboard_matches_committed_file_for_the_real_vault():
    # Regression check: the generator's output for the current (retro-less)
    # vault must match what's actually committed at vault/05-Metrikler/dashboard.md.
    expected = (VAULT_DIR / "05-Metrikler" / "dashboard.md").read_text(encoding="utf-8")
    assert render_dashboard(VAULT_DIR) == expected


def test_render_dashboard_computes_aggregates_from_retros(tmp_path):
    shutil.copytree(VAULT_DIR / "01-Playbooks", tmp_path / "01-Playbooks")
    retros_dir = tmp_path / "03-Retros"
    retros_dir.mkdir()
    (retros_dir / "r1.md").write_text(
        """---
retro_id: RT-001
case: "[[case-0001]]"
sonuc: kapandi
tasarruf: 5000
tasarruf_para_birimi: AED
tur_sayisi: 3
sure_gun: 4
yazan: kutuphaneci-agent
guncelleme: 2026-07-24
---
""",
        encoding="utf-8",
    )
    (retros_dir / "r2.md").write_text(
        """---
retro_id: RT-002
case: "[[case-0002]]"
sonuc: walk
tasarruf: 0
tasarruf_para_birimi: AED
tur_sayisi: 2
sure_gun: 1
yazan: kutuphaneci-agent
guncelleme: 2026-07-24
---
""",
        encoding="utf-8",
    )

    dashboard = render_dashboard(tmp_path)
    assert "| Toplam vaka | 2 |" in dashboard
    assert "| Kapanan | 1 |" in dashboard
    assert "| Kazanma oranı | %50 |" in dashboard
    assert "| Ortalama tasarruf | 5000 AED |" in dashboard
    assert "| Ortalama tur sayısı | 2.5 |" in dashboard


def test_write_dashboard_writes_to_vault_05_metrikler(tmp_path):
    shutil.copytree(VAULT_DIR / "01-Playbooks", tmp_path / "01-Playbooks")
    (tmp_path / "05-Metrikler").mkdir()

    output_path = write_dashboard(tmp_path)

    assert output_path == tmp_path / "05-Metrikler" / "dashboard.md"
    assert output_path.read_text(encoding="utf-8") == render_dashboard(tmp_path)
