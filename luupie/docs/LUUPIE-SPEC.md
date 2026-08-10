# Luupie — Ana Spec

**Tek yetkili tasarım dokümanı.** `CEKIRDEK-DONGU.md`, `FACTORY-HOME-V2.md`,
`EKRAN-MODELI-V3.md` ve `EKONOMI-V4.md` burada birleştirildi; o dosyalar
tarihsel kayıt olarak duruyor. Test raporları (`TEST-RAPORU-*.md`) ayrı kalır.

---

## 0. Ürün tanımı

> Canlı karakterlerin çalıştığı, darboğazları gözle okuyabildiğin, siparişlerle
> büyüyen **yatay izometrik oyuncak fabrikası**.

Referans cihaz `932 × 430` yatay. Yalnız yatay; iki yönelim desteklenmez.

**Tasarım anayasası — her karara üstün gelir:**

> Fabrikanın durumu hakkındaki hiçbir bilgi, önce sahnede görünmeden bir
> panelde sayı olarak gösterilemez. Panel sahnede görüneni *doğrular ve
> ölçer*; asla ilk kaynak olmaz.

---

## 1. Çekirdek döngü

```
1. Şehre git, dolu kaynak depolarını topla         ~10 sn
2. Hattı oku: hangi istasyon aç, hangisi tıkalı     ~5 sn
3. Müdahale: işçi ata · overdrive ver · tamir et  30–60 sn
4. Biriken L1'leri birleştir → L2/L3               ~20 sn
5. Siparişi sevk et → coin                          ~5 sn
6. Coin'i darboğaza veya kaynak binasına yatır     ~10 sn
7. Çık — depolar dolmaya devam eder
```

**Geri dönme sebebi üç tane:** dolan kaynak deposu, biten sipariş, dolan
enerji.

---

## 2. Üretim zinciri

Dört istasyon, soldan sağa. Aralarında tampon. **Fabrika hızı = en yavaş
istasyon.**

```
 ┌───────┐   ┌────────┐   ┌───────┐   ┌──────┐
─┤ PRESS ├─▪─┤ STITCH ├▓▓▓┤ PAINT ├───┤ PACK ├──▶ L1 oyuncak
 └───────┘   └────────┘   └───────┘   └──────┘
              tampon dolu ▲   ▲ tampon boş
                      DARBOĞAZ
```

Oyuncuya öğretilen tek okuma kalıbı:

> **Dolu yığın ile boş bandın arasındaki istasyon suçludur.**

### İstasyon hız çarpanı

```
İşçi × Yatkınlık × Moral × Hızlanma = sonuç
```

| Etken | Aralık | Not |
|---|---|---|
| İşçi | ×0.30 – ×1.00 | İşçi yoksa ×0.30 (istasyon durmaz, sürünür) |
| Yatkınlık | ×1.00 / ×1.35 | Tür istasyonla eşleşirse |
| Moral (sevgi) | ×0.55 – ×1.30 | `0.55 + sevgi/100 × 0.75` — sürekli, eşiksiz |
| Hızlanma | ×1.00 / ×2.00 | Enerji overdrive veya Psycho |

Çarpan bileşenleri panelde **ayrı ayrı** gösterilir, tek birleşik sayı olarak
değil.

### Tür yatkınlığı

| İstasyon | Yatkın türler |
|---|---|
| Press | Şefo (domuz), Ponpon (ayı) |
| Stitch | Pofu (tavşan), Mırmır (kedi) |
| Paint | Uni (tek boynuz), Çako (punk) |
| Pack | Vako (ördek), Cıvata (robot) |
| Serbest | Rako (kurt) — her istasyonda ×1.15, gece ×1.4 |

---

## 3. Kaynaklar ve depo kuralı

Üç kaynak, her biri Şehir'de bir bina:

| Kaynak | Bina | Başlangıç üretim | Periyot | Maks seviye |
|---|---|---|---|---|
| 🧶 Wool | Yün Çiftliği | 45 | 40 sn | 50 |
| 🛢 Oil | Yağhane | 35 | 40 sn | 50 |
| ⛏ Mine | Maden | 28 | 40 sn | 50 |

**Üç kural:**

1. Bina depo miktarına kadar üretir, **sonra durur**.
2. Oyuncu toplayana kadar kaynak fabrikaya gitmez.
3. Seviye yükseltme sırasında bir alt seviyeden üretim devam eder.

Aynı kural hatta da geçerli: **çıktı tamponu dolan istasyon durur.** Sevk
etmezsen PACK tıkanır, PACK tıkanınca PAINT tıkanır, zincir geriye doğru
kilitlenir. **Sevkiyat, hattı açan zorunlu eylemdir.**

### İstasyon girdi maliyeti (L1 oyuncak başına)

| İstasyon | Wool | Oil | Mine |
|---|---|---|---|
| Press | 3 | 1 | — |
| Stitch | 2 | — | 1 |
| Paint | — | 2 | 2 |
| Pack | 1 | 1 | 1 |

Kaynağı biten istasyon **aç kalır** — mevcut "aç kalma" görsel dili artık
gerçek bir sebebe bağlanır.

---

## 4. Upgrade matrix

Altı parametre, hem istasyonlara hem kaynak binalarına uygulanır:

| Parametre | Ne yapar |
|---|---|
| `STARTER` | Seviye 1'deki üretim miktarı |
| `PRODUCTION` | Seviyeye bağlı üretim oranı |
| `UPGRADE MATRIX` | Seviyeye bağlı **logaritmik** artan üretim çarpanı |
| `UPGRADE MULTIPLIER` | Yükseltme maliyetinin artış çarpanı |
| `PRODUCTION LIMIT` | Depo / tampon üst sınırı |
| `TIME MULTIPLIER` | Yükseltme ve enerji sürelerinin seviyeye bağlı değişimi |
| `DEPOT MULTIPLIER` | Depo miktarının üretim oranına bağlı hesabı |

| Bina tipi | Maks seviye | Up Mltp | Time Mltp |
|---|---|---|---|
| Kaynak binaları | 50 | 0.22 | 0.11 |
| Hat istasyonları | 16 | 0.22 | 0.11 |
| Koleksiyon atölyesi | 8 | 0.41 | 0.33 |

> **Değişmez kural:** `UPGRADE MULTIPLIER > UPGRADE MATRIX`. Maliyet üretimden
> hızlı büyümezse tek istasyona sonsuz yatırım optimal olur ve darboğaz oyunu
> ölür.

Yükseltme düğmesi **satın almadan önce** sonucu gösterir:
`YÜKSELT · 120 ● / 3.9 → 3.3 sn / +%18`.

---

## 5. Oyuncaklar ve birleştirme

Hat **yalnızca Seviye 1** oyuncak üretir. Değer birleştirmeden gelir.

| Kural | Sonuç |
|---|---|
| Aynı türden **3** oyuncak | 1 üst seviye, **aynı tür** |
| Karışık türden **5** oyuncak | 1 üst seviye, **rastgele tür** |
| Maksimum seviye | 3 |
| Depo limiti | Tüm seviyeler toplam 100 |

Oyuncak türleri **karakter kadrosuyla aynıdır** (9 tür): Pofu Ayıcık, Mırmır
Kedisi, Şefo Domuzu, Vako Ördeği, Cıvata Robotu, Uni Tek Boynuzu, Çako
Punkı, Ponpon Ayısı, Rako Kurdu.

**Neden hat sadece L1 üretiyor:** Üretim hızı (darboğaz oyunu) ile ürün değeri
(merge oyunu) ayrılır. Hızlı hat çok L1 verir; akıllı oyuncu onları L3'e
çıkarıp aynı emekle daha çok kazanır. İki farklı beceri, tek ekonomi.

---

## 6. Sipariş ekonomisi

**Sipariş tek para kaynağıdır.** Hat doğrudan coin üretmez.

| Sipariş | İçerik | Ödeme | Ham değere göre |
|---|---|---|---|
| Standart | 8 × L1 | 160 ● | — |
| Kaliteli | 4 × L2 | 480 ● | 12 L1 eder → **+33% prim** |
| Butik | 2 × L3 | 1.100 ● | 18 L1 eder → **+53% prim** |
| Acele | 6 × L1, yarı süre | 290 ● | **+81%**, kaçarsa kaybolur |

Prim, birleştirmeye harcanan zamanın karşılığıdır. Aynı anda **bir aktif + bir
sıradaki** sipariş; üçüncüsü yoktur.

Sevkiyat anı ekonominin en önemli anıdır ve **görsel olarak kutlanmalıdır**:
kamyon yanaşır → kutular yüklenir → paralar HUD'a uçar → sayaç sayarak artar →
işçiler el sallar → yeni sipariş düşer.

---

## 7. Enerji ve hızlanma

**Enerji duvar değil, yakıttır.** Üretimi engellemez, hızlandırır.

| | Nasıl |
|---|---|
| Kazanılır | Zamanla dolar (tavan = fabrika seviyesi × 20) + geri dönüşümden |
| Harcanır | Bir istasyonu **30 sn ×2** çalıştırmak: **10 enerji** |

İki hızlanma yolu — biri güvenli ve maliyetli, diğeri bedava ve riskli:

| Yol | Hız | Bedel | Risk |
|---|---|---|---|
| ⚡ Enerji overdrive | ×2 | 10 enerji | Yok |
| 💢 Psycho | ×2 | Bedava | Ürünün **%18'i hatalı**, paketlemeyi tıkar |

"Cute Meets Crazy" ikiliğinin ekonomik karşılığı budur.

---

## 8. Geri dönüşüm — Sökme Tezgahı

| Dönüşüm | Sonuç |
|---|---|
| Alt seviyeye | Seviye N → **3×** Seviye N−1 (rastgele tür), enerji harcanır |
| Enerjiye | Seviye N → 1× Seviye N−1 + **enerji deposu dolar** |
| Kaynağa | Seviye N → 1× Seviye N−1 + yükseltmede harcanan kaynak iade |

Oyunun emniyet valfi. Idle oyunlarda en sık bırakma sebebi "elimde işe yaramaz
yığın var" hissidir; bu üç kural onu ortadan kaldırır.

---

## 9. Koleksiyon atölyesi

Üst seviye çıkış kapısı. **Tamamen oyun içi denge amaçlıdır** — zincir üstü
varlık, cüzdan veya harici ticaret yoktur.

| Girdi | Çıktı |
|---|---|
| 3 × L3 **aynı tür** | O türün nadir koleksiyon parçası |
| 5 × L3 **karışık** | Rastgele nadir parça |

- Üretim süresi uzun (başlangıç 1200 sn), maks seviye 8, enerji harcar
- Çıktı oyuna geri girmez — **kalıcı bonus** verir: her parça global üretim
  hızına **+%2**
- Mezunlar Albümü ile aynı vitrinde yaşar

Bu, ekonominin nihai **sink**'idir: fazla üretimi soğurur ve enflasyonu
engeller.

---

## 10. Karakterler

| Sistem | Kural |
|---|---|
| Nüfus | Maksimum 10 |
| Sevgi | Zamanla düşer (~%8/saat); verim çarpanına doğrudan girer |
| Psycho | Sevgi %25 altında dönüşür: ×2 hız, %18 hatalı ürün |
| Psycho'dan çıkış | Besle (Yemekhane) · Zapt et (Oyuncak Krizi) · bırak çalışsın |
| Mezuniyet | 48 saat sonra bir çocuk sahiplenir → Mezunlar Albümü + bonus |
| Yatkınlık | §2'deki tabloya göre ×1.35 |

Boşta işçi varken hat yavaş çalışıyorsa oyun bunu **sahnede** göstermeli:
işçi elleri cebinde dolaşır, üstünde `👤?` baloncuğu durur.

---

## 11. Ekran modeli

Üç bölge, sınırları katı:

```
┌──────────────────────────────────────────────────────────────┐
│ ⭐11 🪙145                                   💎34  🎁4   ⚙   │ ← KÖŞE KROMU
│                  ╭──────╮                                    │
│                  │ 9:55 │      ← GÖK ŞERİDİ                 │
│   ┌────┐   ┌────┐└──┬───┘  ┌────┐                           │
│  ─┤    ├─▪─┤    ├───┤    ├─┤    ├──   YAŞAM ALANI           │
│   └────┘   └────┘   └────┘ └────┘     krom giremez          │
│      ●        ●        ●       ●      ← karakterler         │
│ 📋                                        [🏭][🏙][💜]       │ ← KÖŞE KROMU
└──────────────────────────────────────────────────────────────┘
```

| Bölge | Ne girer | Ne giremez |
|---|---|---|
| Köşe kromu (~%9) | Para, seviye, navigasyon, görev düğmesi | Oyun durumu anlatan hiçbir şey |
| Gök şeridi | Makineye ait diegetic baloncuk | Buton, panel, kart |
| Yaşam alanı `798 × 276` | Makine, bant, tampon, ürün, karakter | **Hiçbir arayüz öğesi** |

**Ölçüler (932 × 430, güvenli alan 59 yan / 21 alt):**

| Öğe | Konum | Maks boyut |
|---|---|---|
| Sol üst küme | (67, 10) | 210 × 56 |
| Sağ üst küme | sağdan 67 | 250 × 56 |
| Sol alt düğme | (67, alttan 24) | 56 × 56 |
| Sağ alt navigasyon | sağdan 67 | 210 × 56 |
| Yaşam alanı | (67, 76)–(865, 352) | **dokunulmaz** |

Diegetic baloncuk makinenin tepesine demirlenir, alt kenarı bant şeridinin
en az `24 px` üstünde durur. Karakter altından geçerse **karakter üstte
çizilir** — sahne her zaman kazanır.

### Panel sistemi

Bütün alt yüzeyler ortalanmış büyük panel: **%66 genişlik × %90 yükseklik**,
arkada sahne **%35 karartılmış ama görünür**. Tam kaplama yapılmaz — o kenar
payı "geri döndüm" hissini veren şeydir.

- Başlık levhası üst kenara biner · ⊗ sağ üst köşeye biner, min `56 × 56`
- En fazla 3 sekme, alt sekme yok
- Alt eylem sırasında en fazla 2 geniş düğme
- İçerik kabı `overflow-y: auto`
- Üç kapatma yolu: ⊗ · panel dışına dokunma · Escape

**Bilgi diegetic, karar panelde.** Sevk etme istisnadır: kamyon baloncuğundan
tek dokunuş, panel açmadan.

### Dönüş deltası — zorunlu

Panel kapanırken:

| ms | Olay |
|---|---|
| 0 | Panel, ait olduğu makineye doğru küçülerek kapanır (180 ms) |
| 180 | Makine kısa parlama |
| 220 | Makine üstünde delta çipi: `19.3 → 3.2 sn` |
| 220–1000 | Bant hızı **rampayla** yeni değere çıkar |
| 220–1200 | Tampon yığını gözle görülür şekilde erir |
| 1700 | Çip solar; darboğaz değiştiyse yeni baloncuk pop ile gelir |

Hiçbir şey değişmediyse koreografi çalışmaz, panel sessizce kapanır.

---

## 12. Darboğaz görsel dili

| Durum | Bant | Tampon | İşçi | Ek sinyal |
|---|---|---|---|---|
| Akışta | Düzenli aralıklı ürünler | %0–40 alçak yığın | Ritmik çalışma | — |
| Yığılma | Sol taraf tıka basa | %80+, yere taşar | Hızlı ama yetişemiyor | Çerçeve kalınlaşır |
| Aç kalma | Sağ taraf boş | 0 | Esneme, saate bakma | — |
| Tıkalı | Bant durur | Çıktı dolu | Kollarını indirir | `⛔` baloncuğu |
| Arıza | Bant durur | Dondurulur | İki adım geri çekilir | Duman + kırmızı flaş + titreme |
| Psycho | 2× hızlı | Hatalılar farklı siluet | Mor aura, titrek | Hatalılar bantta ayırt edilir |
| İşçisiz | Çok seyrek ürün | Yavaş dolar | Boş tezgah | `👤?` baloncuğu |

Hiçbir durum yalnızca renkle anlatılmaz; her birinin ikinci kanalı var.
**Arıza için tam ekran modal yoktur.**

Aynı anda en fazla **iki baloncuk**; üçüncüsü sol alt görev düğmesindeki
sayıya yazılır.

---

## 13. Mini oyunlar

Üç kural:

1. **Giriş her zaman sahneden** — tıkanan makine, psycho işçi, düşen ürün,
   sipariş kasası. Listeden asla.
2. **Geçiş konumu öğretir** — kamera önce o noktaya yaklaşır, sonra panel açılır.
3. **Çıkışta değişim görünür** — düzelttiğin şey **1 saniye içinde** gözle
   görülür.

| Olay | Mekanik | Fabrika sonucu | Süre |
|---|---|---|---|
| Perfect Seam | Çizgi izleme | Hatalı ürünleri temizler | 20–30 sn |
| Dance-Off | Yönlü ritim swipe | Tüm işçilere süreli moral | 30–40 sn |
| Conveyor Run | Şerit değiştirme | Düşen ürünleri kurtarır | 15–25 sn |
| Cargo Sort | Sürükle-bırak | Acil siparişi bonusla yollar | 25–35 sn |
| Pressure Chamber | Tut–bırak risk | Psycho'yu overdrive'a sokar | 20–30 sn |
| Memory Loom | Desen / hafıza | Plan veya hikâye parçası açar | 30–40 sn |

**Ödül kuralı:** Hiçbir mini oyun yalnızca coin ve XP vermez. Önce ekranda
görünen somut bir problemi çözer. Başarısızlık kaynak yakmaz — fırsatı
kaçırır ve istasyonu kısa süre kilitler.

Dikey swipe eşiği yatayınkinin **yarısı** olmalı (430 px'te yukarı/aşağı
hareket payı ~180 px, sol/sağ ~800 px).

---

## 14. Şehir

Kaynak binaları ve bölge restorasyonu burada yaşar.

| Bölge | Hedef açılış | Eklediği kural |
|---|---|---|
| Repair Alley | 1–2. gün | Arıza ve kalite |
| Candy District | 3–5. gün | Moral ve enerji |
| Psycho Lab | 7–10. gün | Risk ve overdrive |
| Shipping Bay | 14–21. gün | Sipariş yönlendirme |
| Clocktower | 30. gün+ | Prestij / yeni vardiya |

Bölgeler seviye kapısıyla değil **çok aşamalı projelerle** açılır. Aşamalar
inşaat halinde bina olarak gösterilir — ilerleme çubuğu değil, binanın kendisi
kademeli tamamlanır. Her yeni bölge hattı **uzatır**, katlamaz.

Kilit gösterimi: `🔒 3 aşama · 12 plan` biçiminde. Kaynak için kesir
kullanılmaz; kesir yalnızca aşama içindir (`0/3 aşama`). Karşılanamayan
aşama düğmesi **gizlenmez, pasif gösterilir** ve gereksinimi yazar.

---

## 15. Görevler

Vardiya günlüğü — yan hedefler, ana akışı örtmez:

- Bina / istasyon seviye artırımı
- Farklı seviyelerde **ilk** oyuncak üretimi
- Farklı seviyelerde **x adet** oyuncak üretimi
- Koleksiyon parçası üretimi
- Toplam kaynak üretimi / harcaması
- Toplam enerji harcaması

Ödüller: enerji deposunun yenilenmesi, kaynak, coin, plan.

**Öneri motoru kuralı:** Görev/öneri listesi her zaman **hat hızına en çok
katkı yapan** eylemi başa koyar — istasyon hızına değil. Darboğazda işçi yoksa
ve boşta işçi varsa, öneri "yükselt" değil **"ata"** olmalıdır.

---

## 16. İlk 10 dakika

| Süre | Adım | Gizli |
|---|---|---|
| 0:00–0:30 | Bant soldan sağa akar; ilk oyuncak alt-orta bölgeden toplanır | nav, görevler, sipariş |
| 0:30–1:30 | Bir istasyon yavaşlar; solunda tampon dolar, sağı boşalır | nav, sipariş |
| 1:30–3:00 | İlk işçi ataması; süre iner, bant hızlanır — ilk "ben yaptım" | yükseltme |
| 3:00–5:00 | İlk sipariş iner; tek seçenek, seçim yok | sipariş sınıfları |
| 5:00–7:00 | Kontrollü arıza; kısa tamir oyunu çözer, bant 1 sn içinde başlar | diğer mini oyunlar |
| 7:00–9:00 | İlk sevkiyat; para ilk kez HUD'a akar | — tam görünür olmalı |
| 9:00–10:00 | Repair Alley restorasyonu başlar | Luupies sekmesi, kozmetikler |

**İlk beş dakikada asla görünmeyecekler:** kozmetikler · lig · haftalık ·
albüm · tüm oyuncak seviyeleri · dört istasyonun tam istatistik tablosu ·
koleksiyon · geri dönüşüm.

---

## 17. Seans modeli

| Varsayım | Değer |
|---|---|
| Günlük oturum | 2–3 |
| Oturum süresi | 4–12 dk |
| Oturum başına karar | 4–6 |
| Offline tavan | 6–8 saat |
| Hızlı sipariş | 10–20 dk |
| Standart sipariş | 60–120 dk |
| Hikâye siparişi | 8–24 sa |

Yatay yönelim 40 saniyelik bakışları öldürür; ekonomi buna göre ayarlanmıştır.

Dönüş deneyimi popup değil **sahnedeki kamyon ve kasalar**: kamyon sağdan
girer, kasalar rampada yığılır, dokununca patlar, para HUD'a uçar. Vardiya
raporu modal değil kart olur.

---

## 18. Açık işler

Test raporları ve revizyon listelerinden birleştirilmiş tek yığın.

| # | İş | Kaynak | Öncelik |
|---|---|---|---|
| 1 | **Sipariş düğmesini nav'ın altından çıkar** — oyun 45 sn'de kilitleniyor | Rapor 03 | 🛑 Bloke |
| 2 | Panel yüksekliği %90 + içerik `overflow-y: auto` — görev paneli kırpılıyor | Rapor 02/03 | 🔴 |
| 3 | Sahnede dokunma çakışmaları (istasyon etiketi ⨯ karakter) | Rapor 02/03 | 🔴 |
| 4 | Sevkiyat anına kutlama koreografisi | Rapor 03 | 🔴 |
| 5 | Psycho sistemini aç (dönüşüm, ×2, %18 hatalı, üç seçenek) | Rapor 03 | 🔴 |
| 6 | Sevgi düşüşü + rastgele arıza — mini oyunlar hâlâ hiç tetiklenmiyor | Rapor 03 | 🔴 |
| 7 | Öneri motoru boştaki işçileri saysın | Rev-02 A1 | 🟠 |
| 8 | Çıktı tamponu dolan istasyon **dursun** | Ekonomi V4 | 🟠 |
| 9 | Üç kaynak + depo/dolunca durma kuralı | Ekonomi V4 | 🟠 |
| 10 | Upgrade matrix'i tabloya bağla | Ekonomi V4 | 🟠 |
| 11 | Birleştirme paneli (3 aynı / 5 karışık) | Ekonomi V4 | 🟠 |
| 12 | Sipariş seviyeleri + prim | Ekonomi V4 | 🟠 |
| 13 | Enerji + overdrive | Ekonomi V4 | 🟡 |
| 14 | Geri dönüşüm (Sökme Tezgahı) | Ekonomi V4 | 🟡 |
| 15 | Sipariş çeşitliliği (acele / VIP / toplu) | Rapor 03 | 🟡 |
| 16 | Mikro geri bildirim (`+1` parçacıkları, istasyon efektleri) | Rapor 03 | 🟡 |
| 17 | Yürüme sprite'ları kullanılsın — yükleniyor ama karakterler sabit | Rapor 03 | 🟡 |
| 18 | İlerleme çubuğu + sonraki hedef | Rapor 03 | 🟡 |
| 19 | Şehir plan formatı ve pasif aşama düğmesi | Rev-02 D1/D2 | 🟡 |
| 20 | Panel genişliği %82 → %66 | Rapor 02 | 🟡 |
| 21 | Kaynak binaları Şehir sekmesine | Ekonomi V4 | ⚪ |
| 22 | Koleksiyon atölyesi + görev genişlemesi | Ekonomi V4 | ⚪ |
| 23 | Ses tasarımı | Rapor 03 | ⚪ |

---

## 19. Kabul ölçütleri

| Ölçüt | Hedef |
|---|---|
| Arayüz kaplaması | ≤ %22 |
| Yaşam alanı bütünlüğü | Örten arayüz öğesi sayısı **0** |
| Üst kenarda dokunulabilir eylem | **0** |
| Panel ölçüsü | %66 × %90, hiçbiri kırpılmıyor |
| Karar mesafesi | Açılıştan ilk anlamlı karara ≤ 2 dokunuş |
| Katalogdan açılabilen mini oyun | **0** |
| Oturum | Medyan 4–12 dk, günde 2–3 |
| JS hatası | **0** |

**Tek cümlelik kabul testi:** Oyunu hiç görmemiş birine telefonu yatay uzatın,
hiçbir şey söylemeyin. **30 saniye içinde "şurada bir sorun var" deyip doğru
istasyonu işaret edebiliyorsa** tasarım çalışıyor demektir.

**Ekran görüntüsü testi:** Ana ekranın görüntüsünü alın ve arayüzü kırpın.
Kalan görüntü tek başına şunları anlatabilmeli: hangi istasyon yavaş, nerede
yığılma nerede boşluk, kim nerede çalışıyor, sipariş hazır mı.
