# Luupie — Canlı Build Test Raporu 01

**Hedef:** `luupie-toy-factory.gomooo.chatgpt.site`
**Yöntem:** Headless Chromium, yatay görünüm, gerçek dokunuş simülasyonu.
İstekler curl üzerinden aynalandı (ortam proxy'si tarayıcıyı doğrudan
geçirmiyor). Test edilen çözünürlükler: 932×430, 926×428, 844×390, 740×360,
1024×768.

**JavaScript hatası:** Tüm akış boyunca **sıfır**. Konsolda yalnızca
Cloudflare'in `405` challenge isteği var, oyunla ilgisi yok.

---

## 🔴 Kritik — yayını engeller

### K1. Navigasyonun iki sekmesi ekran dışında

Ölçümler (viewport yüksekliği 430):

| Sekme | üst | alt | Durum |
|---|---|---|---|
| FABRİKA | 348 | 397 | ✓ görünür |
| ŞEHİR | 402 | 451 | ⚠ etiketi kesik, ikonun 28 px'i görünür |
| LUUPIES | 456 | 505 | ❌ **tamamen ekran dışında** |

Her telefon boyutunda aynı:

| Cihaz | Çözünürlük | Sonuç |
|---|---|---|
| iPhone 14 Pro | 932×430 | ŞEHİR + LUUPIES kesik |
| iPhone 13 Pro Max | 926×428 | ŞEHİR + LUUPIES kesik |
| iPhone 14 | 844×390 | ŞEHİR + LUUPIES kesik |
| Küçük Android | 740×360 | ŞEHİR + LUUPIES kesik |
| iPad | 1024×768 | ✓ sorunsuz |

**Kök neden:** Navigasyon dikey bir sütun ve alta demirlenmiş, ama çocuklar
demirden **aşağı doğru** diziliyor. FABRİKA'nın alt kenarı ekranın 33 px
üstünde (430−397 = 33; 390−357 = 33 — sabit), diğer ikisi bu noktadan sonra
taşıyor.

**Düzeltme:** Sütun yerine **yatay sıra** (3 × 56 = ~180 px, alt sağ köşeye
rahat sığar), veya sütun kalacaksa son öğe alta demirlensin (`flex-end`),
ilk öğe değil.

### K2. Psycho karakter yönetimine telefonda hiçbir yol yok

Sahnede bir karaktere dokununca **istasyon paneli** açılıyor (İŞÇİ sekmesi),
karakter paneli değil. Karakter detayı yalnızca LUUPIES sekmesinden
erişilebiliyor — o da K1 yüzünden telefonda açılamıyor.

Sonuç: Grizz `♥ %28` ile psycho eşiğinde, işçi listesinde `!` ile işaretli,
ama **Besle / Zapt Et eylemlerine ulaşılamıyor.** İki ayrı sorun birleşip
çıkmaz sokak üretiyor.

K1 çözülünce bu da açılır, ama sahnedeki karaktere dokununca karakter
panelinin açılması yine de doğru davranış olurdu.

---

## 🟠 Yüksek

### Y1. "iyileştir" kartı geliştirme sekmesine götürmüyor

Üstteki `DARBOĞAZ · 6.1 sn · iyileştir` kartına dokununca doğru istasyon
(`Paint & Charm`) açılıyor — bu iyi. Ama panel **ÜRETİM** sekmesinde
açılıyor, GELİŞTİR'de değil. Kart "iyileştir" diyor, oyuncu bir dokunuş daha
yapmak zorunda.

**Düzeltme:** Kart, hedef istasyonu doğrudan GELİŞTİR sekmesinde açsın.

### Y2. Darboğaz kartı okunmuyor

Kart üst-ortada, koyu mor zemin üzerine soluk gri metin. `6.1 sn · iyileştir`
satırı ekranda neredeyse görünmez. Ayrıca yatayda üst-orta başparmakla en zor
erişilen bölge.

**Düzeltme:** Kontrastı yükseltin; kartı alt köşelerden birine taşıyın veya
darboğaz uyarısını makinenin üstünde diegetic baloncuğa çevirin (V3 bölüm 5).

---

## 🟡 Orta

### O1. Panel neredeyse tam ekran

Ölçülen panel dış çerçevesi ekranın **%95 genişliğinde**, arkadaki sahne çok
koyu karartılmış. V3 spec'i **%66 genişlik ve %35 karartma** diyordu.

Şu an "geri döndüm" hissini veren kenar payı yok denecek kadar az. Sahne
görünmediği için panel kapanınca değişimi fark etmek zorlaşıyor — ki dönüş
deltasının işe yaraması buna bağlı.

### O2. ÜRETİM sekmesinin alt yarısı boş

Panel yüksekliği sabit; ÜRETİM sekmesinde içerik çarpan satırında bitiyor ve
altında panel yüksekliğinin ~%40'ı boş kalıyor. Panel içeriğe göre küçülsün
ya da sekme içeriği zenginleşsin.

### O3. GELİŞTİR düğmesi panel çerçevesini taşıyor

`YÜKSELT · 120 / HIZI +%18 ARTIR` düğmesinin alt kenarı panelin iç
çerçevesinin dışına çıkıyor. Küçük ama her açılışta görünüyor.

### O4. Escape tuşu paneli kapatmıyor

Panel dışına dokunma çalışıyor ✓, ⊗ düğmesi çalışıyor ✓, Escape çalışmıyor.
Masaüstü/tablet klavyeli kullanımda beklenen davranış.

### O5. "MEKÂNI SÜRÜKLE" ipucu ve kamera sürükleme

Alt-ortadaki `↔ MEKÂNI SÜRÜKLE` ipucu çok soluk ve ekranın en alt kenarında,
yarı kesik duruyor.

Ayrıca bu bir tasarım sorusu: **kamera sürüklenebilir hale gelmiş.** V3'te
"kamera sabit, tüm hat tek bakışta görünür" kuralı vardı. Şu an sahne
ekrandan geniş olduğu için sürükleme gerekiyor — yani hattın tamamı aynı anda
görünmüyor. Darboğaz okuması "solda yığılma, sağda açlık" ilkesine dayanıyor;
ikisi aynı anda görünmezse okuma bozulur.

Karar sizin, ama sürükleme kalacaksa hattın **tamamı sığacak bir uzak
konum** varsayılan olmalı; sürükleme yalnızca detaya yaklaşmak için.

---

## ✅ Doğrulanan iyi işler

Bunlar test sırasında çalışır halde görüldü:

- **Çarpan formülü:** `İşçi ×1.00 × Yatkınlık ×1.35 × Moral ×1.14 = ×1.53`
  — bileşenler açık, sonuç ayrı çipte. Rev-01 A1 kapandı.
- **Girdi/çıktı tamponu ayrımı:** `GİRDİ TAMPONU: HAMMADDE` ·
  `ÇIKTI TAMPONU: 4/20`. Rev-01 A2 kapandı.
- **İşçi şeridi:** her kartta sevgi yüzdesi ve **o istasyondaki süre**
  (`Miso ♥%78 · 3.9 sn`, `Moss ♥%86 · 4.4 sn`), yatkın türlerde `×1.35`
  rozeti, psycho adayında `!` işareti. Rev-01 B1 kapandı.
- **Yükseltme delta önizlemesi:** `MEVCUT 3.9 sn → SONRA 3.3 sn`,
  `YÜKSELT · 120`, `HIZI +%18 ARTIR`. Rev-02 B1 kapandı.
- **Dönüş deltası sözü panelde yazılı:** *"Makine seviyesi yükseldiğinde panel
  kapanınca değişimi doğrudan hat üzerinde göreceksin."* V3'ün zorunlu
  parçası benimsenmiş.
- **Sahne temizlendi:** büyük daire ikonlar gitmiş, istasyon adları makinenin
  altında küçük pill olmuş, vardiya kartı şeridi kalkmış. V3 bölüm 2 uygulanmış.
- **Karakterler istasyonlarda** ve erişilebilirlik etiketleri doğru
  (`"Miso, Cloud Press istasyonunda"`).
- **Tamponlar bantta görünüyor** (istasyonlar arası küçük kutucuklar).
- **Panel dışına dokunma kapatıyor.**
- **Sıfır JavaScript hatası.**

---

## Öncelik sırası

| # | Madde | Neden |
|---|---|---|
| 1 | **K1** · Navigasyonu yatay sıraya al | Oyunun üçte biri telefonda erişilemez |
| 2 | **K2** · Karaktere dokununca karakter paneli | Psycho yönetimi çıkmaz sokakta |
| 3 | **Y1** · "iyileştir" → GELİŞTİR sekmesi | Kart sözünü tutmuyor |
| 4 | **Y2** · Darboğaz kartı kontrastı / konumu | Ana sinyal okunmuyor |
| 5 | **O1** · Panel %95 → %66, karartmayı azalt | Dönüş deltası buna bağlı |
| 6 | **O5** · Varsayılan kamera tüm hattı göstersin | Darboğaz okuması buna bağlı |
| 7 | **O2, O3, O4** · Panel boşluğu, taşan düğme, Escape | Ucuz düzeltmeler |

---

## Test edilemeyenler

Bu turda kapsam dışında kaldı, bir sonraki turda bakılmalı:

- Mini oyun akışı (Perfect Seam) — tetikleyici bir olay oluşmadı
- Sevkiyat akışı — test sırasında hazır sipariş yoktu
- Offline dönüş / kasa toplama
- Şehir bölge restorasyonu (panel açıldı, aşama başlatma denenmedi)
- Öneri motorunun atanmamış işçileri sayıp saymadığı (Rev-02 A1) — test
  sırasında tüm istasyonlarda işçi vardı, boşta işçi senaryosu oluşmadı
