# Luupie — Revizyon Listesi 02

İkinci tur inceleme · 5 ekran (Fabrika, Packing Gate çekmecesi, Şehir,
Luupies listesi, Moss çekmecesi)

---

## Kapanan maddeler

Revizyon 01'den çözülenler:

| Madde | Durum |
|---|---|
| A1 · Çarpan çelişkisi | ✅ Bileşenler açık: `İşçi ×0.30 × Yatkınlık ×1.00 × Moral ×1.00 = ×0.30` |
| A2 · Darboğazın boş tamponu | ✅ `GİRDİ TAMPONU 35/35` — darboğaz için doğru okuma |
| B1 · İşçi slotu | ✅ İşçi şeridi + kişi başı süre (`Zip %80 · 3.2 sn`) + `×1.35` rozeti |
| B4 · Makine fotoğrafı | ✅ Kaldırılmış |
| B5 · Çekmece sahneyi kapatıyor | ✅ Alt kontrol çubuğu oldu |
| D1 · Başlık bloğu | ✅ Tek satır + rozetler |
| D2 · Kart oranı ve kesik metin | ✅ Yatay kart, isim ve istasyon okunuyor |
| E1 · Karakter modali önceliği | ✅ Durum öne çıktı, kozmetik sağa indi |
| E2 · Karakterin işi | ✅ `Atanmamış · istasyon bekliyor` + `İSTASYONU DEĞİŞTİR` |
| F1 · Kilitli bölgeler "×" | ✅ 🔒 + gereksinim |
| F3 · Alt kartın eylemi | ✅ `AŞAMAYI BAŞLAT` |
| F4 · Plan bakiyesi | ✅ `1 plan gerekiyor · sende 3 var` |
| G1 · Krem modal | ✅ Çekmeceler koyu temaya geçti |

Ayrıca istenmeden gelen iyi eklemeler: sekme üstündeki `3` atanmamış rozeti,
Toy Factory düğümündeki kademeli bina görseli, `Süre canlı güncellenir` kopyası.

---

## A. Bu turun en önemli bulgusu

### A1. Vardiya Zekâsı küçük kazancı öneriyor

**Şimdi:** PACK darboğaz, `LV 1 · 16.7 sn/parça`, çarpan `×0.30` — yani
**işçisi yok**. Aynı anda `! 3 atanmamış` Luupie var ve çekmecedeki işçi
şeridi diyor ki: Zip atanırsa **3.2 sn**.

Vardiya kartı ise `PACK'i hızlandır · +%18 hat hızı hedefi` öneriyor.

Hesap:

| Eylem | PACK süresi | Yeni darboğaz | Hat hızı |
|---|---|---|---|
| Şimdi | 16.7 sn | PACK | 215/sa |
| Kartın önerisi (yükseltme) | ~14.2 sn | PACK | ~254/sa · **+%18** |
| Zip'i ata (tek dokunuş) | 3.2 sn | STITCH 5.5 sn | ~654/sa · **+%204** |

**Olmalı:** Öneri motoru **atanmamış işçileri hesaba katmıyor.** Oyun bunu
zaten biliyor — sekme rozetinde `3` yazıyor. Öncelik kuralı:

1. Darboğazda işçi yoksa **ve** atanmamış işçi varsa → kart:
   `PACK'e Zip'i ata · 16.7 → 3.2 sn`
2. Ancak bundan sonra yükseltme önerilsin.

Genel kural: **kartlar her zaman en yüksek getirili eylemi göstermeli**, ve
getiri hat hızı cinsinden hesaplanmalı — istasyon hızı cinsinden değil.

### A2. Sevkiyat hâlâ kartlarda değil

**Şimdi:** Sipariş `22/22 SEVKİYAT HAZIR`, ödül `+460`. Üç vardiya kartı:
hızlandır / takım / kalite. Sevkiyat yok.

+460 bu ekrandaki her şeyden değerli ve tek para kaynağı. Revizyon 01'de de
vardı, hâlâ açık. **1. öncelikli kart olmalı.**

---

## B. İstasyon çekmecesi

### B1. Yükseltme düğmesi hâlâ yok

**Şimdi:** Çekmecede kimlik + tamponlar + çarpan + işçi şeridi var.
Yükseltme yok.

Ama vardiya kartı `PACK'i hızlandır` diyor — bu kart nereye gidiyor? Eğer
çekmeceye götürüyorsa oyuncu yükseltme bulamıyor; başka bir yere götürüyorsa
istasyon yönetimi iki ayrı yere bölünmüş demektir.

**Olmalı:** İşçi şeridinin sağına tek düğme:
`YÜKSELT · 340 🪙 / 16.7 → 14.2 sn`. Delta işçi kartlarında zaten var,
aynı dili yükseltmede de kullanın.

### B2. `ÇIKTI TAMPONU: SEVKİYAT` — sayı yerine kelime

**Şimdi:** `GİRDİ TAMPONU 35/35` sayı, `ÇIKTI TAMPONU SEVKİYAT` kelime.
İki kutu aynı görünüp farklı şey söylüyor.

**Olmalı:** Ya ikisi de sayı (`ÇIKTI 12/25`), ya çıktı kutusu hedefi gösteren
farklı bir bileşen olsun (`→ Sevkiyata gidiyor`), kutu olmasın.

### B3. `İşçi ×0.30` etiketi yanıltıcı

**Şimdi:** Çip `İşçi ×0.30` diyor — "işçinin katkısı 0.30" gibi okunuyor.
Oysa 0.30 **işçi olmadığı için** uygulanan ceza.

**Olmalı:** İşçi yokken `İşçi yok ×0.30` (kırmızı), atandığında
`Zip ×1.05` (isimle). Ceza ile katkı görsel olarak ayrılsın.

### B4. İşçi kartlarında mevcut görev yazmıyor

**Şimdi:** Zip, Moss, Bunbun kartlarında sevgi ve süre var; **şu an nerede
çalıştıkları** yok. Zip'i PACK'e atarsam Stitch Bench boşalıyor mu?

**Olmalı:** Kartta küçük satır: `boşta` veya `Stitch Bench'ten alınır`.
Dolu bir işçiyi taşıyorsa dokunuşta kısa onay: `Stitch 5.5 → 19.3 sn olacak`.

### B5. Çekmece istasyon etiketlerini kesiyor

**Şimdi:** Çekmece açıkken `PRESS` etiketi yarıya kesiliyor; zincir bandının
alt kenarı örtülüyor.

**Olmalı:** Çekmece ≤%38'de kalsın **ve** açılırken sahne ~40 px yukarı
kaysın. Şu an kaydırma yok, sadece örtüyor.

---

## C. Sahne

### C1. Tampon sayı olarak var, yığın olarak yok

**Şimdi:** `20/20`, `25/25`, `35/35` etiketleri bantta duruyor. Doğru veri,
ama yine **metin**.

**Olmalı:** Sayı kalsın (teyit için), yanına gerçek yığın gelsin: doluluk
arttıkça kutular üst üste birikip yükselsin, %100'de zemine taşsın.
Oyuncu sayıyı okumadan bilmeli.

### C2. Üç tampon da dolu ama dört istasyon da çalışıyor gibi

**Şimdi:** `20/20`, `25/25`, `35/35` — üçü de %100. Bu, PRESS, STITCH ve
PAINT'in **tıkalı** olduğu anlamına gelir; çıktılarını koyacak yer yok.
Ama dördü de aynı şekilde aktif görünüyor.

**Olmalı:** Çıktı tamponu dolan istasyon görünür şekilde **dursun**:
makine animasyonu yavaşlayıp kilitlensin, işçi kollarını indirsin, üstünde
küçük `TIKALI` işareti çıksın. Darboğazın asıl bedeli budur ve şu an
görünmüyor.

---

## D. Şehir

### D1. `12/3 plan` bozuk kesir gibi okunuyor

**Şimdi:** Clocktower `🔒 12/3 plan`, Candy Hall `🔒 18/3 plan`,
Psycho Lab `🔒 24/3 plan`, Shipping Bay `🔒 32/3 plan`.

`12/3` "3'te 12" gibi okunuyor. Muhtemelen "12 plan, 3 aşama" demek.

**Olmalı:** `🔒 3 aşama · 12 plan` veya sadece `🔒 12 plan`.
Eğik çizgi yalnızca gerçek kesirlerde (`0/3 aşama`) kullanılsın.

### D2. Alt kart ile düğme farklı fiyat söylüyor

**Şimdi:** Kart `1 plan gerekiyor · sende 3 var` diyor.
Düğme `AŞAMAYI BAŞLAT · 140 ● + 1 ⟋` diyor — yani 140 altın da istiyor.

**Olmalı:** Kart metni tam maliyeti söylesin: `140 altın + 1 plan gerekiyor ·
ikisi de sende var`. Fiyatı düğmede saklamayın.

### D3. Başlık bloğu harita düğümlerini örtüyor

**Şimdi:** `Şehri yeniden dik` başlığı Repair Alley etiketinin üstüne biniyor
(`…epair Alley` okunuyor). Shipping Bay etiketi de alt kartın kenarında.

**Olmalı:** Başlık tek satıra insin (`STITCHWICK · Şehri yeniden dik`) veya
harita düğümleri başlık alanından uzağa yerleşsin. Alt kart açıkken harita
yukarı kaysın.

---

## E. Luupies sekmesi

### E1. Altı Luupie var, ikisi görünüyor

**Şimdi:** Rozet `6 Luupie` diyor. Ekranda Moss ve Zip var, Zip'in kartı sağ
kenardan kesiliyor. Kartların altında ve sağında geniş boş alan duruyor —
ekranın yaklaşık %30'u.

**Olmalı:** İki yoldan biri:
- **Tek sıra yatay kaydırma:** kart genişliği ~300 px'e insin, 4 kart tam
  görünsün, 5.'si yarım görünüp kaydırma olduğunu belli etsin.
- **İki sıralı ızgara:** 3×2 = 6 kart, kaydırma yok. Boş alan zaten var.

İkincisi bu nüfus için daha iyi — maksimum 10 Luupie ise 5×2 hep sığar.

### E2. Kart çekmecesi listenin üstünü örtüyor

**Şimdi:** Moss çekmecesi açılınca kartların alt yarısı çekmecenin altında
kalıyor; Zip'in kartı ortadan kesiliyor.

**Olmalı:** Çekmece açılırken liste yukarı kaysın ve **seçili kart görünür
kalsın** — istasyon çekmecesinde uyguladığınız "sahne açık kalır" kuralının
aynısı.

### E3. Kozmetik bölümü sağ kenardan kesiliyor

**Şimdi:** `Sahnede görünen ekl…` başlığı ve tek kozmetik kutusu ekran
kenarında sıkışmış.

**Olmalı:** Kozmetikler çekmecenin alt şeridine yatay dizilsin, ya da
katlanmış bölüm olsun (`Görünüm ▾`). Sağ kenara sıkıştırmayın.

---

## F. Devam eden maddeler

Revizyon 01'den hâlâ açık:

- **G4 · Sevkiyat vardiya kartlarında değil** (bu listede A2)
- **G5 · Navigasyon ile vardiya kartları yer değiştirmeli.** Nav hâlâ sağ
  altta — sağ başparmağın en iyi noktasında ve nadiren kullanılıyor.
  Kartlar solda ve ortada.
- **G3 · Metin kesilmesi.** Vardiya kartları: `PACK'i hızlan…`, `Takımı …`,
  `Kalite …`. Kozmetik başlığı: `Sahnede görünen ekl…`

---

## G. Uygulama sırası

| # | İş | Etki |
|---|---|---|
| 1 | **Öneri motoruna atanmamış işçileri ekle** (A1) | Oyuncuya %204 yerine %18 öneriliyor — en büyük kayıp |
| 2 | **Sevkiyatı 1. karta al** (A2) | Tek para kaynağı listede yok |
| 3 | **Yükseltme düğmesi** (B1) | Çekirdek karar hâlâ ekranda değil |
| 4 | **Tıkalı istasyon durumu** (C2) | Darboğazın bedeli görünmüyor |
| 5 | **Tampon yığınları** (C1) | Sayıdan görsele geçiş |
| 6 | **Nav ↔ kart yeri** (F) | Ucuz, ergonomik kazanç |
| 7 | **Şehir etiket ve fiyat düzeltmeleri** (D1–D3) | Ucuz, okunabilirlik |
| 8 | **Luupies ızgara + çekmece kayması** (E1–E3) | Ekranın %30'u boş duruyor |

---

## Korunmalı

- **Çarpan bileşen çipleri.** `İşçi × Yatkınlık × Moral = sonuç` — bu, çoğu
  idle oyunun gizlediği şeyi açıkça gösteriyor. Etiketi düzeltin ama yapıyı
  bozmayın.
- **İşçi kartlarındaki kişi başı süre.** `Zip %80 · 3.2 sn` — seçimi tahminden
  hesaba çeviriyor. Aynı dil yükseltmede de kullanılmalı.
- **`Süre canlı güncellenir`** kopyası — beklentiyi doğru kuruyor.
- **Şehirdeki kademeli bina görseli** (Toy Factory düğümü). Diğer bölgelere de
  aynı muamele.
- **Sekme rozetleri** (`3` atanmamış). Doğru yerde, doğru sayı.
- **Koyu çekmece teması.** Dünya bütünlüğü geri geldi.
