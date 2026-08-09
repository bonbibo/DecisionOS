# Luupie — Revizyon Listesi 01

Build: `luupie-toy-factory.gomooo.chatgpt.site` · 5 ekran incelendi
(Fabrika, Luupies, Karakter modalı, Şehir, Perfect Seam, Stitch Bench çekmecesi)

Durağan görsellerden inceleme — hareket ve animasyon yargılanmadı.

---

## A. Bloke edenler — önce bunlar

Bunlar tasarım tercihi değil, ekranların birbiriyle çelişmesi.

### A1. "4/4 İstasyon dolu" ile "ÇARPAN ×0.30" çelişiyor

**Şimdi:** Luupies sekmesi *4/4 İstasyon dolu* diyor. Stitch Bench çekmecesi
aynı anda *ÇARPAN ×0.30* gösteriyor — bu, spesifikasyondaki **"işçi yok"**
çarpanı.

**Olmalı:** İkisinden biri yanlış. Ya çarpan işçiyi saymıyor, ya "4/4" yanlış
sayıyor. Karar: çarpanın bileşenleri çekmecede **açık** yazılsın —
`işçi 0.95 × yatkınlık 1.35 × moral 0.88 = ×1.13`. Tek bir birleşik sayı,
hatayı görünmez yapıyor.

### A2. Darboğazın tamponu boş — bu tanım gereği mümkün değil

**Şimdi:** STITCH `DARBOĞAZ` rozetli, ama `TAMPON 0/25`.

**Olmalı:** Darboğazın **girdi tamponu dolu** olur; boş tamponlu istasyon
darboğaz değil, aç kalmış istasyondur. Üç ihtimal, üçü de düzeltme istiyor:

1. Etiket çıktı tamponunu gösteriyorsa → `GİRDİ TAMPONU` / `ÇIKTI TAMPONU`
   diye ikiye ayrılsın.
2. Simülasyon üst istasyondan besleme yapmıyorsa → zincir kopuk, motor hatası.
3. STITCH gerçekten aç kalıyorsa → darboğaz PRESS'te, rozet yanlış istasyonda.

Bu, sahnede tampon çizilmediği için gözden kaçıyor. Yığınlar çizilseydi
"darboğaz ama önü boş" hatası ilk bakışta görünürdü.

---

## B. İstasyon çekmecesi — en büyük tasarım kaybı

Luupies sekmesi *"Her karakter sahnedeki gerçek bir istasyonu çalıştırır"*
diye söz veriyor. İstasyon çekmecesinde **o karakter yok.**

### B1. İşçi slotu eklenmeli

**Şimdi:** Çekmecede kimlik + makine görseli + 3 salt-okunur kutu var.
Kimin çalıştığı yazmıyor, değiştirilemiyor.

**Olmalı:** Ortada yatay işçi şeridi. Her kart: yüz, isim, sevgi barı ve
**o istasyondaki tahmini süre**. Yatkın türler başa, `×1.35` rozetiyle.
Dokun → anında atanır, şerit kapanmaz, süre sayarak değişir.

### B2. Yükseltme düğmesi yok

**Şimdi:** Darboğaz istasyonunun çekmecesinde yükseltme yok. Oyunun tek
gerçek kararı ekranda değil.

**Olmalı:** Sağ blokta tek düğme + fiyat + **satın almadan önce delta**:
`YÜKSELT · 340 🪙 / 19.3 → 16.1 sn`.

### B3. Aynı sayı iki kez

**Şimdi:** `3.1 parça/dk` ve `19.3 sn` — aynı bilgi (60 ÷ 19.3 = 3.1).

**Olmalı:** Tek birim seçin. Öneri: **saniye/parça** kalsın, çünkü yükseltme
deltası bu birimde okunuyor. `parça/dk` yalnızca hat toplamında (`186/sa`)
kullanılsın.

### B4. Makine fotoğrafı sahneyi tekrarlıyor

**Şimdi:** Çekmecenin yarısını "CANLI MAKİNE" görseli kaplıyor — arkada zaten
duran makinenin kopyası.

**Olmalı:** Görsel çıksın, yeri işçi şeridine verilsin. Sahne zaten canlı;
çekmece sahneyi tekrar etmemeli, üstüne eylem koymalı.

### B5. Çekmece sahneyi kapatıyor

**Şimdi:** Krem modal ekranın ~%55'ini kaplıyor, fabrika karartılıyor.

**Olmalı:** Alttan yükselen **≤%38 (164 px)** kontrol çubuğu; zincir bandı
açık kalsın. İşçi değiştirince bandın hızlandığını *aynı anda* görmek şart —
kapalı sahnede bu imkânsız.

---

## C. Mini oyun (Perfect Seam)

### C1. İki girdi yöntemi aynı anda

**Şimdi:** "ALANDA KAYDIR" yazıyor **ve** altta 4 yön düğmesi var.

**Olmalı:** Tek yöntem. Öneri: **swipe kalsın, düğmeler çıksın** — düğmeler
yatayda alt kenarı işgal ediyor ve mekaniği tap oyununa çeviriyor. Erişilebilirlik
için düğme isteniyorsa ayarlarda seçenek olsun, ikisi birden ekranda olmasın.

### C2. Görsel vaat ile mekanik uyuşmuyor

**Şimdi:** Kesikli çizgi "bu yolu çiz" diyor; mekanik ise ayrık yön girdisi.

**Olmalı:** Ya çizgi takibi gerçekten sürekli olsun (parmağı yoldan ayırmadan),
ya çizgi ayrık düğümlere bölünsün — her düğümde bir yön oku.

### C3. Süre, ilerleme ve bahis görünmüyor

**Şimdi:** Kaç adım var, ne kadar sürem kaldı, başarısızlıkta ne olur — hiçbiri
yok.

**Olmalı:** Üstte adım göstergesi (`3/6`), daralan süre çubuğu, ve somut bahis:
`7 hatalı ürün paketlemeyi tıkıyor` — soyut "kalite" yerine sayı.

### C4. Karakter dekor

**Şimdi:** Kedi solda duruyor, dikişi yapan o değil.

**Olmalı:** Dikişi karakter yapsın; her başarılı adımda iğne bir düğüm ilerlesin.
Fabrika olayının kahramanı işçi olmalı.

---

## D. Luupies sekmesi

### D1. Başlık bloğu ekranın üçte birini yiyor

**Şimdi:** "Luupies" başlığı + 3 istatistik çipi + alt satır ≈ 250 px.
730 px'lik yatay ekranda kartlar için 1,5 sıra kalıyor, dikey kaydırma gerekiyor.

**Olmalı:** Başlık tek satıra insin (`GECE EKİBİ · 6 Luupie · Moral %77`),
çipler o satıra rozet olarak girsin. Kazanılan ~180 px kartlara gitsin.

### D2. Kart isimleri kesiliyor

**Şimdi:** `Mos…`, `Bun…`, `Mis…`, `Pato`, `Griz` — isimler okunmuyor.
Görev alanı daha kötü: `Hat …`, `Pai…`, `Diki…`, `Clo…`, `Kali…`, `Gec…`

**Olmalı:** Kart oranı yatayda **dikey değil yatay** olsun (yaklaşık 2:1):
solda portre, sağda isim + istasyon + sevgi barı. Metin kesilmesin.
İstasyon adı kartın en önemli bilgisi — kısaltılacak son şey o.

### D3. Kaydırma yönü yanlış

**Şimdi:** Dikey kaydırma, yatay ekranda.

**Olmalı:** Tek sıra **yatay kaydırma**. 6–10 kart yatayda doğal akar,
başparmak hareketi de yatay.

### D4. Rozetler etiketsiz

**Şimdi:** Kalp, madeni para ve `!` rozetleri açıklamasız.

**Olmalı:** En fazla iki rozet: **atanmamış** (`!`) ve **psycho** (mor).
Diğerleri kart gövdesinde yazıyla. `!` sayısı sekme ikonunda da görünsün.

### D5. Sevgi barı görünmüyor

**Şimdi:** Kartın altında 20 px'lik turuncu çizgi.

**Olmalı:** Kart genişliğince bar + yüzde. Sevgi artık verim çarpanı;
en görünür ikinci bilgi olmalı.

---

## E. Karakter modalı (Grizz)

### E1. Öncelik ters — psycho karakterde ana içerik kozmetik

**Şimdi:** `36% sevgi · Psycho ruh hali` tek satır alt bilgi; modalin gövdesi
"Sahnede görünen eklemeler" (kozmetikler).

**Olmalı:** Durum kötüyse modal **eylem modalı** olur:
- Üstte: `PSYCHO · %36 sevgi` uyarı bloğu + ne yaptığı (`×2 hız, %18 hatalı`)
- Hemen altında iki düğme: **Besle** (Yemekhane) ve **Zapt et** (Oyuncak Krizi)
- Kozmetikler aşağı iner, katlanmış bölüm olur

Karakter sağlıklıysa mevcut düzen kalabilir — kozmetik üstte, bilgi altta.

### E2. Karakterin işi yazmıyor

**Şimdi:** Hangi istasyonda çalıştığı, ne kadar verim verdiği yok.

**Olmalı:** İsmin altında: `Dikiş Tezgahı · ×1.35 yatkın · 6.8 sn`.
Ve istasyonu değiştirme kısayolu.

### E3. "Ay tacı · LV 3" kilit sebebi belirsiz

**Şimdi:** `LV 3` yazıyor ama neyin seviyesi belli değil.

**Olmalı:** `Grizz LV 3'te açılır` veya `Fabrika LV 3'te açılır` — hangisi ise.

---

## F. Şehir sekmesi

### F1. Kilitli bölgeler "×" ile gösteriliyor

**Şimdi:** Kilitli düğümlerde `×` — hata/iptal işareti gibi okunuyor.

**Olmalı:** `×` yerine **gereksinim**: `🔒 12 plan` veya `Repair Alley · 0/3`.
Kilit bir engel değil, hedef olarak sunulmalı.

### F2. Restorasyon aşamaları görünmüyor

**Şimdi:** Bölgeler ikili — açık veya kapalı.

**Olmalı:** Plandaki çok aşamalı yapı: her düğüm `0/3` gibi aşama sayacı
taşısın, tamamlandıkça **binanın kendisi kademeli inşa olsun**. İlerleme
çubuğu değil, binanın hâli.

### F3. Alt kart yalnızca "geri dön" diyor

**Şimdi:** Seçili düğüm zaten Toy Factory; tek eylem "FABRİKAYA DÖN" —
navigasyonun zaten yaptığı şey.

**Olmalı:** Alt kart seçili bölgenin **restorasyon eylemini** taşısın:
`Repair Alley · 2/3 aşama · 8 plan ile sonraki aşamayı başlat`.
Fabrika düğümü seçiliyken kart hat özetini göstersin.

### F4. Plan bakiyesi ile ihtiyaç yan yana değil

**Şimdi:** HUD'da `3` var (plan?), haritada ne kadar gerektiği yok.

**Olmalı:** Her düğümde `8 / 3` biçiminde gereken/eldeki. Yetiyorsa düğüm
parlasın.

### F5. Metin kesilmesi ve etiket örtüşmesi

**Şimdi:** `…buradan çıkı…` kesik; `Shipping Bay` etiketi alt kartın altında
kalıyor.

**Olmalı:** Kopya kısalsın; alt kart açıkken harita `~60 px` yukarı kaysın.

---

## G. Sistem geneli

### G1. Krem modal sistemi gece vardiyası dünyasını kırıyor

**Şimdi:** Sahne koyu mor gece fabrikası; her modal (karakter, mini oyun,
istasyon) açık krem. Sert kopuş.

**Olmalı:** İki yol var, birini seçin:
- **Tercih edilen:** Modaller koyu zemine geçsin, krem yalnızca vurgu ve
  düğmelerde kalsın. Dünya bütünlüğü korunur.
- Alternatif: Krem kalsın ama yalnızca **mini oyunlarda** — "atölye ışığı
  yanıyor" gibi kasıtlı bir anlam taşısın. İstasyon ve karakter yüzeyleri
  koyu olsun.

### G2. Her şey tam kaplama modal; çekmece yok

**Şimdi:** İstasyon, karakter ve mini oyun — üçü de sahneyi kapatan overlay.

**Olmalı:** Kural: **sahne durumu taşıyan yüzeyler çekmece, sahneden bağımsız
yüzeyler modal.**
- İstasyon → alttan çekmece ≤%38
- Karakter → alttan çekmece ≤%38
- Mini oyun → modal olabilir, ama arkada fabrika bulanık görünsün ve çıkışta
  aynı kameraya dönülsün

### G3. Metin kesilmesi yaygın bir sorun

Beş ekranın dördünde kesik metin var: kart isimleri, istasyon adları, şehir
açıklaması, vardiya kartları. Tek kural: **hiçbir birincil bilgi kesilmez.**
Sığmıyorsa kopya kısalır, kutu büyür veya bilgi düşer — üç nokta çözüm değil.

### G4. Sevkiyat hâlâ vardiya kartlarında değil

Önceki incelemeden devam: sipariş `22/22 SEVKİYAT HAZIR` iken üç vardiya
kartında sevkiyat yok. **1. öncelikli kart** olmalı.

### G5. Navigasyon ile vardiya kartları yer değiştirmeli

Nav sağ altta (sağ başparmağın en iyi noktası) ama nadiren kullanılıyor;
kartlar solda ve ortada. Nav sola, kartlar sağa.

---

## H. Uygulama sırası

| # | İş | Neden önce |
|---|---|---|
| 1 | **A1 + A2 çelişkilerini çöz** | Motor doğru çalışmıyorsa arayüz düzeltmesi anlamsız |
| 2 | **Sahneye tampon yığını ve bant üstü ürün** | Önceki incelemenin 1. maddesi; A2'yi de görünür kılar |
| 3 | **İstasyon çekmecesi: işçi şeridi + yükseltme + delta** (B1–B5) | Oyunun tek gerçek kararı şu an ekranda yok |
| 4 | **Sevkiyatı 1. karta al, nav ↔ kart yer değiştir** (G4, G5) | Tek para kaynağı erişilemez bölgede |
| 5 | **Modal → çekmece dönüşümü ve koyu tema** (G1, G2) | Sahne bağlantısı bu olmadan kurulmuyor |
| 6 | **Metin kesilmelerini temizle** (G3, D2, F5) | Ucuz, her ekranda görünür |
| 7 | **Luupies sekmesi yatay düzen** (D1–D5) | Kendi başına iyi, ama hattı etkilemiyor |
| 8 | **Şehir aşamalandırma** (F1–F4) | Meta katman; çekirdek oturduktan sonra |

---

## Korunmalı olanlar

Bunlara dokunmayın:

- **Sanat yönü.** Gece fabrikası, mor-amber palet, izometrik derinlik — tutmuş.
- **Zincir sırası.** PRESS → STITCH → PAINT → PACK doğru.
- **Şehir haritası kompozisyonu.** Bölge yerleşimi ve isimlendirme iyi.
- **Türkçe kopya.** "Vardiya zekâsı", "hat canlı", "darboğaz", "Şehri yeniden
  dik" — dile yerleşmiş, çeviri kokmuyor.
- **Mini oyunun fabrikaya bağlanması.** *"Başarılı dikiş hatalı ürünleri
  temizler"* — mini oyunun sonucu somut. Doğru fikir, uygulaması düzeltilmeli.
- **"Her karakter sahnedeki gerçek bir istasyonu çalıştırır."** Doğru vaat;
  B1 bu vaadi arayüzde tutmakla ilgili.
