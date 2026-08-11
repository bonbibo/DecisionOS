# Luupie — Canlı Build Test Raporu 02

**Hedef:** `luupie-toy-factory.gomooo.chatgpt.site`
**Yöntem:** Headless Chromium, yatay, gerçek dokunuş; istekler curl üzerinden
aynalandı. Çözünürlükler: 932×430, 926×428, 844×390, 740×360, 1024×768.

**JavaScript hatası: sıfır** (tüm akış boyunca, yine).

---

## ✅ Rapor 01'den kapananlar

| # | Madde | Doğrulama |
|---|---|---|
| K1 | Navigasyon ekran dışında | **Yatay sıraya alınmış.** Beş çözünürlükte de üç sekme tam görünür (430 px'te alt kenar 415). |
| K2 | Karaktere dokununca istasyon açılıyordu | **Karakter paneli açılıyor.** `"Miso karakter yönetimini aç"` · `PRES USTASI / Cloud Press · ×1.35 yatkın · 3.9 sn / İSTASYONU DEĞİŞTİR › / SWEET %78 sevgi` |
| Y1 | "iyileştir" yanlış sekme açıyordu | **GELİŞTİR sekmesinde açılıyor:** `Paint & Charm` · `MEVCUT 6.1 sn → SONRA 5.2 sn` |
| Y2 | Darboğaz kartı okunmuyordu | **Kontrast düzelmiş**, kart artık işaretçi kuyruklu baloncuk. |
| O3 | Yükselt düğmesi çerçeveyi taşıyordu | Taşma yok. |
| O4 | Escape kapatmıyordu | Kapatıyor. |
| O5 | Kamera hattın tamamını göstermiyordu | `TÜM HAT GÖRÜNÜYOR · DETAY İÇİN SÜRÜKLE` — dört istasyon aynı karede. |

Ayrıca istenmeden gelen iyileştirmeler: kozmetik bölümü katlanabilir (`⌄`)
olmuş, kilit sebebi açık yazılmış (`Ay tacı · Fabrika LV 3'te açılır`),
karakter kartlarında erişilebilirlik etiketleri eklenmiş.

---

## 🔴 Yeni kritik bulgu

### Y-K1. Sipariş düğmesi navigasyonun altında kalıyor

```
öğe:     ▣ 1/8
aria:    "Sipariş durumunu aç"
konum:   (719, 343)  60×43 px
üstünde: ⌂ FABRİKA ⌁ ŞEHİR ♥ 2 LUUPIES
```

`elementFromPoint` düğmenin merkezinde **navigasyonu** döndürüyor — yani
dokunuş navigasyona gidiyor, sipariş düğmesine değil. Programatik olarak
tıklandığında da hiçbir panel açılmıyor.

Sonuç: **ekonominin tek satış noktasına ulaşan hiçbir yol yok.** Rapor 01'de
LUUPIES sekmesi için tespit ettiğimiz örtüşme hatası, bu kez sipariş
düğmesinde tekrarlıyor — nav yatay hale gelirken bir öğenin üstüne oturmuş.

**Düzeltme:** Sipariş göstergesi nav kümesinin dışına çıkarılsın. V3'e göre
zaten sahnede kamyonun üstünde diegetic baloncuk olmalıydı; en temizi orası.
Kalacaksa nav'ın solunda en az 16 px boşlukla ayrı dursun.

---

## 🟠 Yeni yüksek bulgular

### Y-Y1. Görev paneli içeriği kesiliyor, kaydırma yok

```
scrollHeight: 435   clientHeight: 428   overflow-y: hidden
```

7 px taşma var ama kap `overflow: hidden`. Ekranın altında kalan içerik:
`×250`, `×500`, `×15`, `×10`, `×1` — yani **ödül çarpanları görünmüyor**.

Panelin yüksekliği ekranın **%100'ü** olduğu için içerik sığmadığında
kırpılıyor. Spec %90 diyordu; o %10 tam da bu yüzden vardı.

**Düzeltme:** Panel yüksekliği %90'a insin **ve** içerik kabı
`overflow-y: auto` olsun.

### Y-Y2. Sahnede dokunma hedefleri çakışıyor

| Çakışan | Örtüşme |
|---|---|
| `STITCH` etiketi ⨯ Bunbun karakteri | 24 × 28 px |
| `PAINT` etiketi ⨯ Zip karakteri | 25 × 26 px |
| `PACK` etiketi ⨯ `⌁` rozeti | 35 × 32 px |

Bu bölgelere dokunmak belirsiz: istasyon paneli mi karakter paneli mi
açılacağı piksel farkına kalıyor. İkisi de farklı ekran açtığı için yanlış
açılış kullanıcıyı geri dönmeye zorluyor.

**Düzeltme:** İstasyon adı etiketi makinenin altına, karakterin dokunma
kutusunun dışına kaydırılsın; ya da etiket tamamen dokunulamaz yapılsın
(`pointer-events: none`) ve istasyon dokunuşu yalnızca makine gövdesinden
alınsın.

---

## 🟡 Orta

### O-1. Panel ölçüsü hâlâ spec dışı

Ölçülen: **762 × 428 = %82 × %100** (spec: %66 × %90).

Rapor 01'deki %95'ten iyileşmiş ama yükseklik %100 olduğu için:
- dikeyde nefes payı yok → Y-Y1'deki kırpılma oluşuyor
- arkadaki sahne üstte ve altta hiç görünmüyor → "geri döndüm" hissi zayıf

### O-2. Şehirde plan formatı karışık

Ekranda görünenler:

```
Clocktower    🔒 12/0 plan
Candy Hall    🔒 18/0 plan
Repair Alley  0/3 · 1/0 plan
Psycho Lab    🔒 24/0 plan
```

`12/0` bozuk kesir gibi okunuyor (gerekli/eldeki). Daha kötüsü Repair
Alley'de iki farklı anlamda kesir yan yana: `0/3` aşama, `1/0` plan.

**Düzeltme:** Aşama için kesir (`0/3 aşama`), kaynak için düz ifade
(`1 plan gerekli · sende 0 var`). İki kesir yan yana durmasın.

### O-3. Karşılanamayan aşama düğmesi tamamen kayboluyor

0 plan varken `AŞAMAYI BAŞLAT` düğmesi hiç görünmüyor. Oyuncu ne yapması
gerektiğini değil, yapacak bir şey olmadığını görüyor.

**Düzeltme:** Düğme **pasif** halde dursun ve gereksinimi yazsın:
`AŞAMAYI BAŞLAT · 1 plan gerekli`.

---

## ⚪ Hâlâ açık: öneri motoru (Rev-02 A1)

`Görevleri aç` düğmesi **Vardiya günlüğü**'ne gidiyor: günlük/haftalık yan
hedefler (`Bir sipariş sevk et 0/1`, `Bir istasyonu yükselt 0/1`,
`GÜNLÜK SANDIK`, `7 günlük vardiya serisi`). Bunlar iyi, ama
**"şimdi ne yapmalı?"** listesi değil.

Şu anki tek öneri sinyali darboğaz baloncuğu ve o **her zaman yükseltme**
öneriyor (`6.1 sn · iyileştir`, 120 ●). Oysa test anında:

- Sahnede 4 istasyonda 4 işçi var
- İşçi listesinde **6 karakter**: Miso, Grizz, Moss, Zip, Bunbun, Patch
- LUUPIES sekmesinde `2` rozeti → **2 karakter boşta**
- Grizz `♥ %28` ve `!` işaretli — psycho eşiğinde, hiçbir yere atanmamış

Yani boştaki işçiyi değerlendirme önerisi hiçbir yerde çıkmıyor. Rev-02 A1
maddesi özü itibarıyla açık: **öneri, hat hızına en çok katkı yapan eylemi
göstermeli** — bazen bu yükseltme değil, atama olur.

---

## Öncelik sırası

| # | Madde | Neden |
|---|---|---|
| 1 | **Y-K1** · Sipariş düğmesini nav'ın altından çıkar | Tek para kaynağına erişim yok |
| 2 | **Y-Y1** · Panel %90 yükseklik + `overflow-y: auto` | İçerik kırpılıyor |
| 3 | **Y-Y2** · Etiket/karakter dokunma çakışması | Yanlış panel açılıyor |
| 4 | **A1** · Öneri motoru boştaki işçileri saysın | Yanlış eylem öneriliyor |
| 5 | **O-2, O-3** · Şehir plan formatı ve pasif düğme | Ucuz okunabilirlik |
| 6 | **O-1** · Panel genişliği %82 → %66 | Dönüş deltası buna bağlı |

---

## Hâlâ test edilemeyenler

- **Mini oyun akışı** — tetikleyecek bir olay (arıza/kalite) oluşmadı
- **Sevkiyat** — sipariş düğmesi erişilemediği için denenemedi (Y-K1)
- **Offline dönüş / kasa toplama**
- **Şehir aşama tamamlama** — 0 plan olduğu için düğme yok

Bu dördü için tetikleyici bir hata ayıklama modu (örn. `?debug=1` ile olay
zorlama, plan/para verme) çok işe yarardı; bir sonraki turda hepsini tek
geçişte gezebilirim.
