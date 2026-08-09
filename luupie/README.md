# Luupie — Cute Meets Crazy 🧸💢

"Ponchiqs: Cute Meets Crazy" konsept dokümanından uyarlanan, **dikey tam ekran**
mobil idle-management oyunu. Kod bağımlılığı yoktur; saf HTML5 Canvas + DOM.

## Çalıştırma

```bash
cd luupie
python3 -m http.server 8080
# tarayıcıda: http://localhost:8080
```

Mobilde tam deneyim için telefonu dik tutun; masaüstünde pencere otomatik
letterbox'lanır. Swipe = fare sürüklemesi ile de çalışır.

## Oynanış

- **İzometrik fabrika:** Luupie'ler fabrika içinde serbestçe dolaşır
  (sprite animasyonu: yürüme salınımı, squash & stretch, gölge, derinlik sırası).
- **Sevgi Barı:** İlgilenilmeyen Luupie'nin sevgisi zamanla düşer; %25'in
  altında **Psycho**'ya dönüşür (2x üretim ama arkadaşlarına bulaşıcı!).
- **Oyuncak Krizi (Toy Trouble):** Psycho'ya dokun → daralan süre penceresinde
  yön oklarına doğru swipe. Push-your-luck: 1x → 2x → 4x → 8x; istediğin an
  "Sakinleştir" ile kazancı al. Kaçırırsan kayıp yok, sadece fırsat kaçar
  (istasyon 45 sn kilitlenir).
- **Tamir İstasyonu:** Konveyör arızalanınca banda dokun → parçaları doğru
  yöne swipe ile tak, ardından dikiş adımlarını takip et.
- **Yemekhane:** Tatlıyı canı çeken Luupie'ye doğru kaydır (refleks testi).
  Doğru servis sevgiyi yükseltir; Psycho'ları Sweet'e döndürmenin yoludur.
- **Nüfus:** Maks 10 Luupie. 48 saat sonra mezun olurlar (ölmezler, bir çocuk
  tarafından sahiplenilirler) → **Mezunlar Albümü** + bonus.
- **Offline birikim:** Kapalıyken üretim düşük hızda sürer (4 saat tavan);
  dönünce "Tekrar Hoş Geldin" özeti.
- **Haftalık Üretim Ligi:** Toplam servet değil, sadece o haftanın üretim
  hacmi yarışır.
- **Enerji duvarı yok** — geri çağıran şey dolan kova merakıdır.

## Sprite üretimi

`assets/sprites/` içindeki 27 sprite, `assets/character-sheet.jpeg` konsept
sayfasından (9 karakter × kafa / sweet / psycho) chroma-key + bağlı bileşen
analiziyle otomatik kesilmiştir. Yeniden üretmek için:

```bash
pip install pillow numpy scipy
python3 luupie/tools/extract_sprites.py luupie/assets/character-sheet.jpeg
```

`manifest.json` tür → dosya/boyut eşlemesini tutar; `js/assets.js` bu manifesti
okuyarak yükler. Sayfada psycho formu bulunmayan tek tür (unicorn) için script
sıcak tonlu bir varyant sentezler.

## Mimari

| Dosya | Sorumluluk |
|---|---|
| `js/data.js` | Tür verileri, ekonomi sabitleri (CONFIG) |
| `js/assets.js` | Manifest tabanlı sprite yükleyici |
| `js/input.js` | Dokunma/swipe algılama + WebAudio efektleri |
| `js/factory.js` | İzometrik oda: duvar, pencere, konveyör, fırın, pres |
| `js/ponchiq.js` | Karakter varlığı: yürüme, animasyon, sevgi/psycho |
| `js/minigames.js` | 3 swipe mini oyunu |
| `js/ui.js` | HUD, paneller (albüm/lig/sahiplenme), popup, toast |
| `js/game.js` | Ekonomi, offline birikim, mezuniyet, lig, localStorage |
| `js/main.js` | Boot, oyun döngüsü, ölçekleme, olaylar |

Kayıt: `localStorage["luupie_save_v1"]` — silmek yeni oyun başlatır.
