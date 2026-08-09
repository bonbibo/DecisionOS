"""Konsept karakter sayfasından şeffaf sprite'ları üretir.

Kullanım:
    python3 luupie/tools/extract_sprites.py <karakter_sayfasi.jpg>

Sayfa düzeni sabittir (9 karakter × kafa/sweet/psycho). Kutular elle
kalibre edilmiştir; kaynak görsel değişirse BOXES güncellenmelidir.
Çıktı: luupie/assets/sprites/*.png + manifest.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent.parent / "assets" / "sprites"
BG = np.array([99, 82, 101])          # sayfa arka plan rengi
KEY_TOLERANCE = 60                     # bu mesafenin altı arka plan sayılır
ALPHA_KNEE, ALPHA_RAMP = 28, 50        # yumuşak alfa geçişi

BOXES = {
    "wolf":    {"head": (63, 58, 192, 157),    "sweet": (18, 148, 152, 338),   "psycho": (148, 148, 272, 340)},
    "punk":    {"head": (368, 38, 482, 152),   "sweet": (314, 143, 438, 338),  "psycho": (438, 143, 557, 340)},
    "unicorn": {"head": (598, 43, 697, 157),   "sweet": (583, 148, 712, 338)},
    "pig":     {"head": (743, 53, 892, 162),   "sweet": (713, 153, 853, 332),  "psycho": (846, 148, 992, 332)},
    "duck":    {"head": (1053, 53, 1162, 157), "sweet": (998, 148, 1116, 322), "psycho": (1104, 148, 1262, 322)},
    "bunny":   {"head": (83, 358, 217, 482),   "sweet": (43, 468, 167, 657),   "psycho": (155, 453, 292, 657)},
    "robot":   {"head": (373, 363, 467, 462),  "sweet": (338, 478, 462, 652),  "psycho": (448, 453, 572, 657)},
    "cat":     {"head": (698, 358, 822, 472),  "sweet": (618, 478, 762, 657),  "psycho": (743, 468, 897, 657)},
    "bear":    {"head": (998, 358, 1112, 482), "sweet": (923, 453, 1067, 652), "psycho": (1053, 448, 1227, 657)},
}


def build(sheet_path: Path) -> dict:
    img = Image.open(sheet_path).convert("RGB")
    rgb = np.asarray(img).astype(int)
    dist = np.abs(rgb - BG).sum(axis=2)
    alpha = np.clip((dist - ALPHA_KNEE) / ALPHA_RAMP, 0, 1)

    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}

    for name, parts in BOXES.items():
        entry = {}
        for form, (x0, y0, x1, y1) in parts.items():
            crop = rgb[y0:y1, x0:x1].astype(np.uint8)
            al = (alpha[y0:y1, x0:x1] * 255).astype(np.uint8)
            crop, al = _drop_stray_fragments(crop, al)
            crop, al = _trim(crop, al)
            fn = f"{name}_{form}.png"
            Image.fromarray(np.dstack([crop, al]), "RGBA").save(OUT / fn)
            entry[form] = {"file": fn, "w": int(crop.shape[1]), "h": int(crop.shape[0])}
        manifest[name] = entry

    _synthesize_psycho(manifest, "unicorn")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def _drop_stray_fragments(crop, al, keep_ratio=0.10):
    """Komşu karakterden taşan kopuk lekeleri siler."""
    lab, n = ndimage.label(al > 20, structure=np.ones((3, 3)))
    if n <= 1:
        return crop, al
    sizes = ndimage.sum(al > 20, lab, range(1, n + 1))
    keep = [i + 1 for i, s in enumerate(sizes) if s >= sizes.max() * keep_ratio]
    al = al.copy()
    al[~np.isin(lab, keep)] = 0
    return crop, al


def _trim(crop, al, thr=20):
    ys = np.nonzero(al.max(axis=1) > thr)[0]
    xs = np.nonzero(al.max(axis=0) > thr)[0]
    if not len(ys) or not len(xs):
        return crop, al
    sl = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
    return crop[sl], al[sl]


def _synthesize_psycho(manifest, species):
    """Sayfada psycho formu olmayan tür için sıcak tonlu varyant üretir."""
    if "psycho" in manifest[species]:
        return
    src = np.asarray(Image.open(OUT / manifest[species]["sweet"]["file"])).astype(float)
    r, g, b, a = src[..., 0], src[..., 1], src[..., 2], src[..., 3]
    out = np.dstack([
        np.clip(r * 1.45 + 25, 0, 255),
        np.clip(g * 0.62, 0, 255),
        np.clip(b * 0.72, 0, 255),
        a,
    ]).astype(np.uint8)
    fn = f"{species}_psycho.png"
    Image.fromarray(out, "RGBA").save(OUT / fn)
    manifest[species]["psycho"] = {"file": fn, "w": out.shape[1], "h": out.shape[0]}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    m = build(Path(sys.argv[1]))
    print(f"{sum(len(v) for v in m.values())} sprite üretildi → {OUT}")
