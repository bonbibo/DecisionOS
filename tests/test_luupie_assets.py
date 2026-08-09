"""Luupie oyununun sprite varlıklarının bütünlük testi.

Oyun JS tarafında koştuğu için davranış testleri tarayıcıda yapılır;
burada asset sözleşmesini doğruluyoruz: manifest ↔ dosya tutarlılığı.
"""
import json
from pathlib import Path

LUUPIE = Path(__file__).resolve().parent.parent / "luupie"
SPRITES = LUUPIE / "assets" / "sprites"

EXPECTED_SPECIES = {
    "wolf", "punk", "unicorn", "pig", "duck", "bunny", "robot", "cat", "bear",
}


def _manifest():
    return json.loads((SPRITES / "manifest.json").read_text())


def test_manifest_covers_all_species():
    assert set(_manifest().keys()) == EXPECTED_SPECIES


def test_every_species_has_head_sweet_psycho():
    for species, forms in _manifest().items():
        assert {"head", "sweet", "psycho"} <= set(forms.keys()), species


def test_manifest_files_exist_and_nonempty():
    for species, forms in _manifest().items():
        for form, meta in forms.items():
            f = SPRITES / meta["file"]
            assert f.is_file(), f
            assert f.stat().st_size > 500, f
            assert meta["w"] > 40 and meta["h"] > 40, (species, form)


def test_game_entry_points_exist():
    assert (LUUPIE / "index.html").is_file()
    for js in ["data", "assets", "input", "factory", "ponchiq",
               "minigames", "ui", "game", "main"]:
        assert (LUUPIE / "js" / f"{js}.js").is_file(), js
