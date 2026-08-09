# Luupie — Factory Home V2 · UX/UI Planı

Çekirdek mekanik doğru, yeri yanlış. Bu plan darboğazlı üretim zincirini
istatistik panelinden çıkarıp izometrik sahnenin kendisine taşıyan ekran
hiyerarşisini, bileşen anatomilerini ve etkileşim kurallarını tanımlar.

---

## 0. Tek cümlelik ilke

> **Fabrikanın durumu hakkındaki hiçbir bilgi, önce sahnede görünmeden bir
> panelde sayı olarak gösterilemez.**

Panel sahnede görüneni *doğrular ve ölçer*; asla ilk kaynak olmaz. Oyuncu bir
sorunu ancak fabrikaya bakarak fark edebilmeli, paneli sadece "ne kadar kötü?"
sorusuna cevap için açmalı.

Bu ilke tek başına brief'teki sekiz kırılma noktasının yedisini kapatır. Geri
kalanı ekonominin tek satış noktasına indirgenmesidir.

---

## 1. Ekran anatomisi

Referans cihaz `430 × 932`. Güvenli alan düşüldükten sonra kullanılabilir
yükseklik `839 px`.

```
┌──────────────────────────────┐
│   güvenli alan · 59 px       │
├──────────────────────────────┤
│ 🪙 1,240   🧸 86      [KASA 3]│  Kaynak HUD
│                              │  64 px · %8 — sabit, min 56
├──────────────────────────────┤
│ (◕) Peluş Tavşan ×20         │  Aktif sipariş şeridi
│     ▓▓▓▓▓▓▓░░░ 14/20 ~12 dk  │  68 px · %8 — sabit, min 52
├──────────────────────────────┤
│                              │
│         ╱▔▔▔▔▔╲              │
│      ┌──┐   ┌──┐             │  CANLI İZOMETRİK FABRİKA
│    ●─┤  ├───┤  ├──●          │  520 px · %62 — esnek
│      └──┘   └━━┛ ▓▓          │
│              ▲   ▓▓          │  ⚠ garanti: asla < 420 px
│           darboğaz           │
│    [kasa]                    │  istasyon · işçi · tampon · kasa
│                              │
├──────────────────────────────┤
│ ┌────────┐┌────────┐┌───────┐│  Vardiya kartları
│ │TIKANDI ││        ││       ││  104 px · %12 — kart yoksa 0
│ └────────┘└────────┘└───────┘│
├──────────────────────────────┤
│  [FABRİKA]   ŞEHİR   LUUPIES │  Navigasyon
│                              │  84 px · %10 — üç sekme
├──────────────────────────────┤
│   home indicator · 34 px     │
└──────────────────────────────┘
```

**Daralma sırası.** Yüzdeler referans cihazdaki hedeftir; uygulamada bantlar
sabit piksel, fabrika esnek olmalı. Saf yüzde küçük ekranlarda fabrikayı 372
px'e düşürür ve izometrik sahne okunmaz hale gelir. Küçük ekranda önce vardiya
kartları tek satıra iner (104 → 56), sonra sipariş şeridi (68 → 52).
**Fabrika bandı en son daralır.**

### Fabrika bandının kuralları

1. **Kamera sabit.** Serbest pan/zoom yok. Tüm hat tek bakışta görünür;
   oyuncu bir şey aramak için sürüklemek zorunda kalmaz.
2. **Her istasyon bir hotspot.** Dokunma hedefi minimum `44 × 44 px`,
   istasyonun görsel sınırından bağımsız olarak.
3. **Ürünler gerçekten hareket eder.** Bant üstündeki oyuncaklar sahte döngü
   animasyonu değil, gerçek üretim sayacına bağlı olmalı — hat hızlanınca ürün
   aralığı gözle görülür şekilde sıklaşır.
4. **Hiçbir durum yalnızca renkle anlatılmaz.** Her durumun ikinci bir kanalı
   var: yoğunluk, hareket, duruş veya duman.

---

## 2. Darboğaz görsel dili

Planın kalbi. Oyuncu fabrikaya baktığında **tek kelime okumadan** ne olduğunu
anlamalı.

```
   AKIŞTA                YIĞILMA · DARBOĞAZ         AÇ KALIYOR
 ▪   ▪   ▪   ▪          ▪▪▪▪▪▪                    — boş bant —
 ━━━━━━━━━━━━━          ━━━━━━━━━━━━━             ━━━━━━━━━━━━━
 ▫▫                     ▓▓▓                        (tampon yok)
      (●)                ▓▓▓ (●)!                       (○) zZ
                         ▓▓
 düzenli aralık          giriş bandı tıkalı        tampon 0
 tampon %30              tampon taşıyor            işçi bekliyor
 işçi ritmik             ürünler yere düşer        saate bakıyor

 → Darboğaz hep bu ikilinin arasındadır: solunda yığılma, sağında açlık.
```

| Durum | Bant | Tampon | İşçi | Ek sinyal |
|---|---|---|---|---|
| Akışta | Düzenli aralıklı ürünler | %0–40, alçak yığın | Ritmik çalışma döngüsü | — |
| Yığılma | Giriş bandı tıka basa dolu | %80+, ürünler yere taşar | Hızlı ama yetişemiyor | İstasyon çerçevesi kalınlaşır |
| Aç kalma | Çıkış bandı boş | 0 | Bekleme: esneme, saate bakma | — |
| Arıza | Bant durur | Dondurulur | İki adım geri çekilir | Duman + kırmızı yanıp sönme + titreme |
| Psycho overdrive | 2× hızlı akış | Hatalı ürünler farklı siluet | Mor aura, titrek duruş | Hatalılar bantta ayırt edilir |
| İşçisiz | Çok seyrek ürün | Yavaş dolar | Boş tezgah + soluk hayalet | — |

> **Yasak:** Arıza için tam ekran uyarı modalı yok. Modal, oyuncuyu sahneden
> koparır ve sorunun nerede olduğunu öğretmez. Arıza yalnızca makinenin
> kendisinde görünür; aciliyet vardiya kartı ve hafif titreşimle iletilir.

---

## 3. İstasyon çekmecesi

Bir istasyona dokununca açılan yüzey. Amacı tek: *bu istasyonu hızlandırmak
için elimde ne var?*

```
┌──────────────────────────────┐
│                              │
│    fabrika görünür kalır     │  ← karartılır, seçili istasyon
│         ┌────┐               │    spot ışıkla vurgulanır
│    ░░░░░│ ▓▓ │░░░░░          │
│         └────┘               │
│      seçili istasyon         │
├══════════════════════════════┤  ← maks %33
│         ▬▬▬                  │
│ Boya & Süsleme       9.0 sn  │
│ ┌──────────┐ ┌─────────────┐ │
│ │(●) Uni   │ │YÜKSELT · 340│ │
│ │    ▓▓▓░░ │ │ 9.0 → 7.6 sn│ │
│ └──────────┘ └─────────────┘ │
│ Sv 3 · tampon 30    kapat ↓  │
└──────────────────────────────┘
```

**Çekmecede olacaklar**
- ✓ İstasyon adı + güncel süre (büyük)
- ✓ İşçi slotu — dokun, listeyi aç, değiştir
- ✓ Tek yükseltme düğmesi + fiyat
- ✓ Delta önizlemesi: `9.0 → 7.6 sn`
- ✓ Seviye ve tampon kapasitesi (küçük)

**Çekmecede olmayacaklar**
- ✕ Diğer istasyonların istatistikleri
- ✕ Hammadde / bileşen listeleri
- ✕ Sekme, alt sekme, kaydırmalı liste
- ✕ Sipariş bilgisi
- ✕ İkinci bir yükseltme yolu

**Geri bildirim zinciri.** İşçi değişti → çekmecedeki sayı `9.0`'dan `6.8`'e
sayarak iner + aynı anda sahnede bant hızlanır + tampon gözle görülür şekilde
erimeye başlar. Çekmece açıkken fabrikanın görünür kalması zorunlu — yaptığın
değişikliğin etkisini *aynı anda* görmezsen, panel yine sahneden kopmuş olur.

**İşçi değiştirme.** Slot'a dokununca yeni ekran değil, çekmecenin içinde yatay
Luupie şeridi açılır. Her kart: yüz, isim, sevgi barı, bu istasyondaki tahmini
süre. Yatkın türler önce sıralanır ve `×1.35` rozeti taşır. Dokun → anında
atanır, şerit kapanır, çekmece açık kalır.

**Delta kuralı.** Her yükseltme düğmesi sonucu *satın almadan önce* gösterir.
Oyuncu parayı harcamadan getiriyi bilir. Bu, "şimdi neyi geliştirmeliyim?"
kararını tahminden hesaba çevirir — idle oyunun tek gerçek kararı budur.

---

## 4. Sipariş şeridi

Fabrikanın hemen üstünde, her zaman görünür. "Şu an ne için üretiyorum?"
sorusu asla cevapsız kalmaz.

| Bileşen | İçerik | Davranış |
|---|---|---|
| Müşteri | Yüz + isim | Hikâye siparişlerinde tanıdık karakter döner |
| Ürün | Model ikonu × adet | Üretilen model hattakinden farklıysa uyarı rozeti |
| İlerleme | `14/20` + bar | Her hazır üründe tık sesiyle artar |
| Süre | `~12 dk` | Mevcut hat hızından hesaplanır, darboğaz değişince canlı güncellenir |
| Ödül | Para + ikincil | Şeridin sağ ucunda sabit çip |

**Tamamlandığında şerit dönüşür.** Tüm bant genişliğinde tek bir **SEVK ET**
düğmesi olur, yeşile döner ve hafifçe nabız atar. Oyundaki en önemli dokunuş
budur — çünkü ekonominin tek satış noktası burasıdır.

Şeride dokunmak sipariş çekmecesini açar (aynı %33 kuralı): aktif sipariş,
sıradaki sipariş, varsa değiştirme seçeneği. Oyuncu aynı anda **bir aktif +
bir sıradaki** sipariş yönetir; üçüncüsü yoktur.

| Sınıf | Süre | Rolü |
|---|---|---|
| Hızlı sipariş | 5–10 dk | Seans içinde kapanır; "şimdi gitme" sebebi |
| Standart sipariş | 30–90 dk | Gün içinde geri dönme sebebi |
| Hikâye siparişi | 6–24 sa | Ertesi gün geri dönme sebebi + bölge ilerlemesi |

---

## 5. Vardiya kartları

Ekranın %12'si, en fazla **üç kart**. Görevi: "şimdi ne yapmalıyım?" sorusuna
sıralı cevap vermek. Her kart bir ikon, tek satır metin ve tek eylem düğmesi.

| Öncelik | Tetikleyici | Kart metni | Eylem |
|---|---|---|---|
| 1 | Arıza / tıkanma | "Boya tıkandı — 2 dk'dır duruyor" | Tamir mini oyununu aç |
| 2 | Sipariş hazır | "20 Peluş Tavşan hazır" | Sevk et |
| 3 | Toplanmamış kasa | "3 kasa bekliyor" | Kamerayı kasaya götür |
| 4 | İşçisiz istasyon | "Paketleme'de kimse yok" | İşçi şeridini aç |
| 5 | Yükseltme karşılanabilir | "Darboğazı 340 ile hızlandır" | İstasyon çekmecesini aç |
| 6 | Sevgi düşük | "Uni'nin morali düştü" | Yemekhane olayını aç |

**Boş durum ödülü.** Hiç kart yoksa bant tamamen kapanır ve o 104 px fabrikaya
eklenir. Temiz bir fabrikanın ödülü, fabrikayı daha büyük görmektir.

---

## 6. Dönüş deneyimi

Offline kazanç popup değil, **sahnedeki fiziksel nesne**.

1. **Kamyon gelir** (1,5 sn). Oyuncu hiçbir şeye dokunmadan fabrikayı görür.
2. **Kasalar rampada yığılır.** Kasa sayısı ≈ offline süresi; üçten fazlaysa
   yığın büyür ama sayı üçte kalır.
3. **Dokununca patlar** — para ve ürün ikonları HUD'a uçar. Toplam üç dokunuş.
4. **Vardiya raporu kart olur.** "Boya 2 sa 10 dk tıkalı kaldı" bilgisi modal
   değil, vardiya bandındaki bir karttır — ve kartın eylemi doğrudan o
   istasyonu açar.

> **Neden popup değil:** Popup, oyuncunun gördüğü ilk şeyi bir *rapor* yapar.
> Kasa ise ilk şeyi *fabrika* yapar. Aradaki fark, oyunun "tablo yöneticisi"
> mi yoksa "fabrika sahibi" mi hissettirdiğidir.

---

## 7. Navigasyon ve taşınma haritası

Beş eşit sekme, beş eşit öncelik demektir — oyuncuya hangisinin ana oyun
olduğunu söylemez. Üçe iniyor:

1. **Fabrika** — Üretim, siparişler, müdahaleler, çevrimdışı kazanç. Oyuncunun
   aktif zamanının %60–70'i burada. Açılış sekmesi her zaman budur.
2. **Şehir** — Bölge haritası ve restorasyon projeleri. Fabrikanın *sonucu*.
3. **Luupies** — Sahiplenme, koleksiyon, kozmetik, karakter ilişkileri.

| Eski yer | Yeni yer | Gerekçe |
|---|---|---|
| Orders sekmesi | Fabrikadaki sipariş şeridi + çekmecesi | Sipariş üretimin hedefi; ayrı ekranda bakılan liste değil |
| Games / Arcade | Sahnedeki bağlamsal olaylar | Katalogdan açılan mini oyun ayrı üründür; olaydan doğan mini oyun oynanıştır |
| Daily / Weekly | HUD'daki küçük görev ikonu → yan panel | Yön gösterici yan hedef; ana nav ağırlığını hak etmiyor |
| Workshop | Fabrika içinde destek tezgahı | İkinci üretim oyunu olmaktan çıkıp ana hattı besleyen tek işleve iner |
| Map | Şehir sekmesi | İsim değil rol değişikliği: harita artık üretimin sonucu |

> **Hammadde sadeleştirmesi.** Kumaş, dişli, iplik, düğme, stuffing ve charm
> ayrı ayrı takip edilmemeli. Çekirdek döngü dokümanı bunu bilerek dışarıda
> bırakmıştı; geri gelmesi ana hattın yanına ikinci bir üretim oyunu kurmuş.
> **Tek ara kaynak yeterli:** Workshop yalnızca *bileşen* üretir, o da yalnızca
> üst model oyuncaklar için gerekir. Altı kaynak → bir kaynak.

---

## 8. Mini oyunların giriş–çıkış koreografisi

1. **Giriş her zaman sahneden.** Tıkanan makine, psycho işçi, düşen ürün,
   sipariş kasası. Listeden asla.
2. **Geçiş konumu öğretir.** Kamera önce o noktaya yaklaşır, sonra mini oyun
   yüzeyi yükselir. Oyuncu *nerede* olduğunu bilir.
3. **Çıkışta değişim görünür.** Aynı kameraya dönülür ve düzelttiğin şey
   **1 saniye içinde** gözle görülür: bant yeniden başlar, hatalılar kaybolur,
   işçiler sevinir.

| Olay | Mekanik | Fabrika sonucu | Süre |
|---|---|---|---|
| Perfect Seam | Çizgi izleme / hassasiyet | Hatalı ürünleri temizler | 20–30 sn |
| Dance-Off | Yönlü ritim swipe | Tüm işçilere süreli moral ve hız | 30–40 sn |
| Conveyor Run | Şerit değiştirme / refleks | Düşmek üzere olan ürünleri kurtarır | 15–25 sn |
| Cargo Sort | Sürükle-bırak sınıflandırma | Acil siparişi bonusla yollar | 25–35 sn |
| Pressure Chamber | Basılı tut–bırak risk kontrolü | Psycho işçiyi overdrive'a sokar | 20–30 sn |
| Memory Loom | Desen / hafıza | Blueprint veya hikâye parçası açar | 30–40 sn |

> **Ödül kuralı.** Hiçbir mini oyun *yalnızca* coin ve XP vermez. Önce ekranda
> gördüğümüz somut bir problemi çözer, ödül ondan sonra gelir. Başarısızlık
> hiçbir zaman kaynak yakmaz — sadece fırsatı kaçırır ve istasyonu kısa süre
> kilitler.

---

## 9. Ekonominin yeni rolleri

En büyük yapısal hata: hat üretirken para kazandırıyor, sipariş teslimi de para
veriyor. İki satış noktası, oyuncunun siparişi önemsemesini engelliyor.

| Sistem | Yeni görevi | Para üretir mi? |
|---|---|---|
| Üretim hattı | Ürün ve ara stok üretir | **Hayır** |
| Siparişler | Ürünü paraya çeviren tek mekanik | **Evet — tek kaynak** |
| Coins | Makine yükseltme, fabrika genişletme | — |
| Blueprints | Bölge restorasyonu | — |
| Ribbons | Kozmetik ve etkinlik koleksiyonları | — |
| Bakım / Sevgi | Süreli, sayısal görünen işçi verimi | — |
| Workshop | Ana hattı destekleyen sınırlı bileşen üretimi | **Hayır** |
| Daily / Weekly | Yön gösterici yan hedefler | Dolaylı |

UI'daki karşılığı: **hattan çıkan ürün HUD'da para değil, ürün sayacını
artırır.** Para yalnızca *SEVK ET* anında, gözle görülür bir akışla HUD'a
girer. Oyuncu iki şeyi aynı anda öğrenir: üretim yetmez, satmak gerekir.

---

## 10. İlk 10 dakika

Her adımda ne *gösterildiği* kadar ne **gizlendiği** de tasarımın parçası.

| Süre | Adım | Ne olur | Gizli |
|---|---|---|---|
| 0:00–0:30 | Bant hareket eder | Oyuncu ilk oyuncağı doğrudan sahneden toplar. Hiç metin yok. | nav, vardiya kartları, sipariş şeridi |
| 0:30–1:30 | Boya yavaşlar | Tampon dolar, sonraki bant boşalır. Darboğazın iki imzası ilk kez birlikte görünür. | nav, sipariş şeridi |
| 1:30–3:00 | İlk işçi ataması | Süre `9.0 → 6.8` iner, bant gözle görülür şekilde hızlanır. İlk "ben yaptım" anı. | yükseltme düğmesi (henüz para yok) |
| 3:00–5:00 | İlk sipariş | Sipariş şeridi yukarıdan iner. Sadece hızlı sipariş; seçim yok. | sipariş sınıfları, sıradaki slot |
| 5:00–7:00 | Kontrollü arıza | Makine titrer, duman çıkar. Vardiya kartı belirir, kısa tamir oyunu çözer, bant 1 sn içinde başlar. | diğer mini oyunlar |
| 7:00–9:00 | İlk sevkiyat | Şerit *SEVK ET*'e döner. Para ilk kez HUD'a akar. Ekonominin kuralı burada öğretilir. | — bu an tam görünür olmalı |
| 9:00–10:00 | Repair Alley | Şehir sekmesi ilk kez açılır, ilk aşama başlar, anlamlı bekleme süresi bırakılır. | Luupies sekmesi, kozmetikler |

**İlk beş dakikada asla görünmeyecekler:** Wardrobe · League · Weekly · Alumni ·
tüm ürün modelleri · dört istasyonun tam istatistik tablosu · prestij ·
koleksiyon setleri.

---

## 11. Bölge restorasyonu

Bölgeler seviye kapısıyla değil, **çok aşamalı projelerle** açılır.

| Bölge | Hedef açılış | Eklediği kural | UI'da görünümü |
|---|---|---|---|
| Repair Alley | 1–2. gün | Arıza ve kalite | Fabrikada tamir tezgahı belirir |
| Candy District | 3–5. gün | Moral ve enerji | Yemekhane sahneye eklenir, sevgi barları görünür |
| Psycho Lab | 7–10. gün | Risk ve overdrive | İstasyon çekmecesine overdrive anahtarı gelir |
| Shipping Bay | 14–21. gün | Sipariş yönlendirme | Sipariş şeridi ikinci slot kazanır |
| Clocktower | 30. gün+ | Prestij / yeni vardiya | Fabrika Devri arayüzü açılır |

Restorasyon aşamaları Şehir sekmesinde **inşaat halinde bina** olarak
gösterilir — ilerleme çubuğu değil, binanın kendisi kademeli tamamlanır. Her
aşama tamamlandığında fabrikaya bir şey eklenir; harita böylece dekor olmaktan
çıkıp üretimin sonucu olur.

Bu tarihler telemetriyle ayarlanacak başlangıç hedefleridir.

---

## 12. Uygulama sırası ve kabul ölçütleri

İlk yapılacak şey yeni içerik değil. Mevcut üretim motoru, izometrik harita,
yürüyen karakterler ve mini oyunlar korunur — hepsi tek bir akışın içine
yeniden yerleştirilir.

| Sıra | Paket | Kabul ölçütü |
|---|---|---|
| 1 | **Factory Home V2 dikey dilimi** | Fabrika ekranın ≥%60'ını kaplıyor · istasyon hotspot'ları çalışıyor · çekmece ≤%33 · sipariş şeridi sabit · tampon fiziksel olarak görünüyor · offline kasa toplanıyor · bir bağlamsal mini oyun bağlı |
| 2 | **Ekonomi birleştirme** | Hattan doğrudan para gelmiyor · sipariş tek satış noktası · hammadde altıdan bire indi · XP eğrisi artan |
| 3 | **FTUE ve dönüş** | İlk 10 dk beat'leri sırayla tetikleniyor · ilk 5 dk'da yasak ekranlar görünmüyor · dönüşte popup yok, kasa var · vardiya kartları önceliğe göre sıralanıyor |
| 4 | **Bölge restorasyonu** | Bölgeler seviyeyle değil aşamalı projeyle açılıyor · her bölge fabrikaya görünür bir şey ekliyor |
| 5 | **Meta derinlik** | Kozmetikler karakterde görünüyor · koleksiyon setleri · Fabrika Devri · sezon yapısı |

### Ölçülebilir başarı sinyalleri

- **Fabrika ekran payı:** ≥%60 (şu an ~%7)
- **Karar mesafesi:** Açılıştan ilk anlamlı karara ≤2 dokunuş (bugün 4–5)
- **Panelde geçen süre:** Aktif seans süresinin ≤%25'i
- **Çekmece yüksekliği:** Hiçbir çekmece ekranın %33'ünü aşmıyor
- **Ana navigasyon:** 3 sekme, açılış her zaman Fabrika
- **Mini oyun bağlamı:** Katalogdan açılabilen mini oyun sayısı sıfır

> **Tek cümlelik kabul testi.** Oyunu hiç görmemiş birine telefonu uzatın ve
> hiçbir şey söylemeyin. **30 saniye içinde "şurada bir sorun var" diyerek
> doğru istasyonu işaret edebiliyorsa** Factory Home V2 çalışıyor demektir.
