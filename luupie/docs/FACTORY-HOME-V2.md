# Luupie — Factory Home V2 · Yatay UX/UI Planı

Yönelim yataya döndü. Bant istifi ölür, yerine tam ekran sahne ve köşelere
demirlenmiş yüzen arayüz gelir. Üretim zinciri artık soldan sağa okunur —
darboğaz tarifi mekânsal hale gelir.

---

## 0. Değişimin bilançosu

Yatay bu oyun için bedava değil. Karar verilmiş; plan ona göre kuruldu, ama iki
sonucu baştan yazıyorum çünkü ikisi de tasarımı değiştiriyor.

**Kazanç**
- **Zincir doğal yönünü bulur.** Dikeyde hattı katlamak zorundaydık; yatayda
  4 istasyon soldan sağa dizilir.
- **Darboğaz okuması mekânsal olur:** solunda yığılma, sağında açlık —
  kelimenin tam anlamıyla.
- **Fabrika %62 değil %100** alan kaplar; arayüz üstünde yüzer.
- **Çekmece geniş ve alçak olur** — her şey tek satırda, kaydırmasız.
- İleride 6 istasyona çıkmak düzeni bozmaz.

**Bedel**
- **Tek elle oynanış biter.** Konsept dokümanının açık tercihiydi.
- **Dikey alan kıtlaşır:** 430 px'e beş bant sığmaz — istif yerine kaplama
  zorunlu.
- **40 saniyelik seans zayıflar.** Kimse 40 saniye için telefonu çevirmez.
- Üst-orta bölge başparmakla erişilemez hale gelir; durum ile eylem ayrışmak
  zorunda.

> **Tasarıma yansıması:** Oyun "günde 6 kısa bakış"tan "günde 2–3 gerçek
> oturum"a kayar. Bu bir kayıp değil, farklı bir retansiyon modeli — ama
> **sipariş sınıf karışımı buna göre yeniden dengelenmeli** (bkz. bölüm 11).

---

## 1. Yeni yapı ilkesi

| Dikeyde | Yatayda |
|---|---|
| Beş yatay bant üst üste istiflenir; her bant kendi yüksekliğini fabrikadan çalar. Fabrika %62. | Sahne tüm ekranı kaplar; arayüz köşelere demirlenmiş **yüzen adalar** olur. Fabrika %100, kaplama ≤%22. |

Temel ilke aynen geçerli:

> **Fabrikanın durumu hakkındaki hiçbir bilgi, önce sahnede görünmeden bir
> panelde sayı olarak gösterilemez.**

Üstüne yatayın iki kuralı biner:

1. **Zincir bandı dokunulmazdır.** Ekranın dikey ortasındaki `~180 px`'lik
   şerit — istasyonların, bandın ve tamponların yaşadığı yer — hiçbir arayüz
   öğesiyle örtülmez. Çekmece bile oraya girmez.
2. **Durum üstte, eylem alt köşelerde.** Yatayda üst-orta başparmakla
   erişilemez. Okunacak şey üst kenara, dokunulacak şey alt köşelere gider —
   ikisi aynı öğe olamaz.

---

## 2. Ekran anatomisi

Referans cihaz `932 × 430` yatay. iOS yatayda simetrik yan güvenli alan
uygular: her iki yandan `59 px`, altta home indicator `21 px`. Kullanılabilir
alan `814 × 409`.

```
┌────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐      ┌────────────────────┐          ┌─────────────┐  │
│ │🪙1,240 🧸86│      │(◕) Peluş Tavşan ×20 │          │[KASA 3]  ⚙ │  │
│ └──────────┘      │  ▓▓▓▓▓▓░░ 14/20 12dk│          └─────────────┘  │
│  üst sol           └────────────────────┘             üst sağ       │
│  salt okunur        üst orta · salt okunur                          │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│                          ▼ DARBOĞAZ                                │
│  ┌────┐    ┌────┐   ┌════┐    ┌────┐         ZİNCİR BANDI          │
│ ─┤PRES├─▫▫─┤DİKİŞ├▓▓▓┤BOYA├────┤PAKET├──     180 px · DOKUNULMAZ     │
│  └────┘    └────┘   └════┘    └────┘                    [kasa]     │
│             tampon dolu ▲   ▲ tampon boş                           │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ ┌───────────────┐                    ┌──────┐┌──────┐┌──────┐      │
│ │[FABRİKA] ŞEHİR│                    │TIKANDI││      ││      │      │
│ │       LUUPIES │                    └──────┘└──────┘└──────┘      │
│ └───────────────┘                                                  │
│  alt sol · sol başparmak              alt sağ · sağ başparmak      │
└────────────────────────────────────────────────────────────────────┘
```

| Ada | Konum | Boyut | Rol |
|---|---|---|---|
| Kaynak HUD | Üst sol | 210 × 44 | Salt okunur — para, ürün |
| Sipariş şeridi | Üst orta | 300 × 62 | Salt okunur — ilerleme, süre, ödül |
| Kasa + menü | Üst sağ | 140 × 44 | Sayaç; dokununca kamera kasaya gider |
| Navigasyon | Alt sol | 204 × 52 | 3 sekme, sol başparmak |
| Vardiya kartları | Alt sağ | 3 × 116 × 68 | Eylem; sağ başparmak |
| İstasyon çekmecesi | Alttan | tam en × ≤164 | Açılınca vardiya kartlarını gizler |

Toplam arayüz kaplaması ≈ **%21** — geri kalan her piksel fabrika. Tablet (4:3)
ve geniş telefonlarda adalar kenara yapışık kalır; fabrika ortadan büyür,
hiçbir şey yeniden konumlanmaz.

---

## 3. Başparmak bölgeleri

Yatayda telefon iki uçtan tutulur; başparmaklar alt köşelerden pivot yapar.
Bu, dikeydeki tek başparmak yayından tamamen farklı bir haritadır.

```
┌────────────────────────────────────────────────────┐
│                                                    │
│         ERİŞİLEMEZ — buraya eylem koyma            │
│         yalnızca salt okunur durum                 │
│╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│
│   zincir bandı — istasyon hotspot'ları (uzanma)    │
│╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌│
│ ╱▔▔▔▔▔╲              uzanma            ╱▔▔▔▔▔╲     │
││ KOLAY │                              │ KOLAY │    │
└┴───────┴──────────────────────────────┴───────┴────┘
   sol başparmak                       sağ başparmak
```

> **KURAL: durum ile eylem aynı öğe olamaz.** Sipariş tamamlandığında üstteki
> şerit yalnızca parlar; SEVK ET düğmesi alt sağda vardiya kartı olarak doğar.

**İstasyon hotspot'ları.** Zincir bandı ekranın dikey ortasında olduğu için
istasyonlar "uzanma" bölgesindedir — kabul edilebilir, çünkü istasyona dokunmak
*keşif* hareketidir, refleks değil. Ama zincir bandı asla ekranın üst üçte
birine yerleştirilmemeli; orada dokunulamaz hale gelir.

Dokunma hedefi minimum `44 × 44 px`, istasyonun görsel sınırından bağımsız.
Kamera sabit — serbest pan/zoom yok, tüm hat tek bakışta görünür.

---

## 4. Darboğaz görsel dili

Mantık yönelimle değişmez; okunuşu kolaylaşır. Öğretilen kalıp tektir:

> **Dolu yığın ile boş bandın arasındaki istasyon suçludur.** Yatayda bu,
> ekranda soldan sağa okunan tek bir cümledir.

| Durum | Bant | Tampon | İşçi | Ek sinyal |
|---|---|---|---|---|
| Akışta | Düzenli aralıklı ürünler | %0–40, alçak yığın | Ritmik çalışma | — |
| Yığılma | Sol taraf tıka basa dolu | %80+, ürünler yere taşar | Hızlı ama yetişemiyor | Çerçeve kalınlaşır |
| Aç kalma | Sağ taraf boş | 0 | Esneme, saate bakma | — |
| Arıza | Bant durur | Dondurulur | İki adım geri çekilir | Duman + kırmızı flaş + titreme |
| Psycho overdrive | 2× hızlı akış | Hatalı ürünler farklı siluet | Mor aura, titrek duruş | Hatalılar bantta ayırt edilir |
| İşçisiz | Çok seyrek ürün | Yavaş dolar | Boş tezgah + soluk hayalet | — |

Hiçbir durum yalnızca renkle anlatılmaz; her birinin ikinci kanalı vardır.
**Arıza için tam ekran modal yoktur** — modal oyuncuyu sahneden koparır ve
sorunun nerede olduğunu öğretmez.

**Yatayın getirdiği ek imkân.** Genişlik arttığı için tamponlar artık gerçek
fiziksel yığın olarak çizilebilir — dikeyde 7 px'lik kutucuklara sıkışıyorlardı.
Yığın yüksekliği doluluk oranını doğrudan gösterir; taşma anında ürünler zemine
düşer ve orada kalır. Oyuncu tampon yüzdesini hiç okumadan bilir.

---

## 5. İstasyon çekmecesi

> ⚠️ **Bu bölüm `EKRAN-MODELI-V3.md` tarafından geçersiz kılındı.** Yönelim
> kararı değişti: alt çekmece yerine Hay Day tarzı ortalanmış büyük panel
> (%66 × %90) kullanılıyor. Aşağıdaki çekmece ölçüleri artık geçerli değil;
> içerik kuralları (işçi şeridi, delta önizlemesi, neyin olmayacağı) V3'te
> korunuyor.



Yataydaki en büyük yapısal kazanç. Dikeyde çekmece `430 × 307` dikdörtgendi ve
içerik dikey istiflenmek zorundaydı. Yatayda `932 × 164` olur — **geniş ve
alçak**. Her şey tek satıra dizilir.

```
┌────────────────────────────────────────────────────────────────┐
│        fabrika karartılır, seçili istasyon spot ışıkta         │
│  ┌────┐   ┌────┐   ╔════╗   ┌────┐                             │
│ ─┤    ├───┤    ├───║ ▓▓ ║───┤    ├──   zincir bandı açık kalır │
│  └────┘   └────┘   ╚════╝   └────┘                             │
├════════════════════════ ▬▬▬ ══════════════════════════════════┤
│ ① KİMLİK       │ ② İŞÇİ — liste yok, şerit  │ ③ TEK YÜKSELTME  │
│ Boya & Süsleme │ ┌──────┐┌──────┐┌──────┐   │ ┌──────────────┐ │
│                │ │(●)Uni││ Pofu ││ Vako │ → │ │YÜKSELT·340 🪙│ │
│ 9.0 sn         │ │×1.35 ││ 8.1sn││ 9.4sn│   │ │ 9.0 → 7.6 sn │ │
│ Sv 3·tampon 30 │ │6.8 sn││      ││      │   │ └──────────────┘ │
│                │ └──────┘└──────┘└──────┘   │                  │
└────────────────────────────────────────────────────────────────┘
                          164 px · %38
```

**Çekmecede olacaklar**
- İstasyon adı + güncel süre (büyük, sol blok)
- İşçi şeridi — dokun, anında ata, şerit kapanmaz
- Tek yükseltme düğmesi + fiyat (sağ blok)
- Delta önizlemesi: `9.0 → 7.6 sn`
- Seviye ve tampon kapasitesi (küçük)

**Çekmecede olmayacaklar**
- Diğer istasyonların istatistikleri
- Hammadde / bileşen listeleri
- Sekme, alt sekme, dikey kaydırma
- Sipariş bilgisi
- İkinci bir yükseltme yolu

**Geri bildirim zinciri.** İşçi değişti → çekmecedeki sayı `9.0`'dan `6.8`'e
sayarak iner **+** aynı anda sahnede bant hızlanır **+** tampon gözle görülür
şekilde erimeye başlar. Çekmece 164 px ile sınırlı olduğu için zincir bandı hep
açık kalır — etkiyi *aynı anda* görürsünüz.

**Kamera davranışı:** çekmece açılırken sahne ölçeklenmez, yalnızca `~40 px`
yukarı kayar. Ölçekleme izometrik sahnede titreme yaratır; kaydırma yaratmaz.

**Delta kuralı.** Her yükseltme düğmesi sonucu satın almadan önce gösterir.
Oyuncu parayı harcamadan getiriyi bilir — "şimdi neyi geliştirmeliyim?" kararı
tahminden hesaba döner.

---

## 6. Sipariş şeridi ve sevkiyat

| Dikeyde | Yatayda |
|---|---|
| Sipariş tamamlanınca şeridin kendisi *SEVK ET* düğmesine dönüşürdü; şerit başparmak menzilindeydi. | Şerit yalnızca **parlar ve nabız atar**. *SEVK ET* alt sağda 1. öncelikli vardiya kartı olarak doğar — başparmağın altında. |

Bu ayrım keyfi değil: yatayda üst-orta erişilemez bölgedir. Oyunun en önemli
dokunuşunu oraya koymak, her sevkiyatta kullanıcıyı tutuşunu değiştirmeye
zorlar.

| Sınıf | Süre | Rolü |
|---|---|---|
| Hızlı sipariş | 10–20 dk | Oturum içinde kapanır (yatay için yeniden dengelendi) |
| Standart sipariş | 60–120 dk | Aynı gün ikinci oturum sebebi |
| Hikâye siparişi | 8–24 sa | Ertesi gün dönüş + bölge ilerlemesi |

Oyuncu aynı anda **bir aktif + bir sıradaki** sipariş yönetir; üçüncüsü yoktur.

---

## 7. Vardiya kartları ve navigasyon

Alt sağda en fazla üç kart, her biri `116 × 68`. Yatayda bunlar bant olmaktan
çıkıp **yüzen çip** olur — kart yoksa hiçbir alan boşa gitmez.

| Öncelik | Tetikleyici | Kart metni | Eylem |
|---|---|---|---|
| 1 | Sipariş hazır | "20 Peluş Tavşan hazır" | Sevk et |
| 2 | Arıza / tıkanma | "Boya tıkandı — 2 dk" | Tamir olayını aç |
| 3 | Toplanmamış kasa | "3 kasa bekliyor" | Kamerayı kasaya götür |
| 4 | İşçisiz istasyon | "Paketleme'de kimse yok" | İşçi şeridini aç |
| 5 | Yükseltme karşılanabilir | "Darboğazı 340 ile hızlandır" | İstasyon çekmecesini aç |
| 6 | Sevgi düşük | "Uni'nin morali düştü" | Yemekhane olayını aç |

Sıralama dikey plandan bir kademe değişti: **sevkiyat 1. sıraya çıktı**, çünkü
artık şerit üzerinden yapılamıyor ve tek satış noktası o.

### Navigasyon

Alt solda üç sekme, yatay dizilim, `204 × 52`. Yatayda alt kenar boyunca uzanan
tam genişlikte tab bar **kullanılmaz** — 430 px'lik dikey alanda 84 px'i
sekmelere vermek savurganlıktır ve sağ başparmağın eylem bölgesini işgal eder.

1. **Fabrika** — üretim, siparişler, müdahaleler, çevrimdışı kazanç. Açılış
   sekmesi her zaman budur; aktif zamanın %60–70'i burada geçer.
2. **Şehir** — bölge haritası ve restorasyon projeleri. Fabrikanın sonucu.
3. **Luupies** — sahiplenme, koleksiyon, kozmetik, karakter ilişkileri.

| Eski yer | Yeni yer | Gerekçe |
|---|---|---|
| Orders sekmesi | Üst şerit + sipariş çekmecesi | Sipariş üretimin hedefi; ayrı liste değil |
| Games / Arcade | Sahnedeki bağlamsal olaylar | Katalogdan açılan mini oyun ayrı üründür |
| Daily / Weekly | Üst sağ menü → yan panel | Yön gösterici yan hedef |
| Workshop | Fabrika içinde destek tezgahı | İkinci üretim oyunu olmaktan çıkar |
| Map | Şehir sekmesi | Harita artık üretimin sonucu |

> **Hammadde sadeleştirmesi.** Kumaş, dişli, iplik, düğme, stuffing ve charm
> ayrı ayrı takip edilmemeli. **Tek ara kaynak yeterli:** Workshop yalnızca
> *bileşen* üretir, o da yalnızca üst model oyuncaklar için gerekir. Altı
> kaynak → bir kaynak. Yatay ekranda HUD'a altı sayaç sığdırmak zaten mümkün
> değil — bu sadeleştirme artık teknik bir zorunluluk.

---

## 8. Dönüş deneyimi

Offline kazanç popup değil, sahnedeki fiziksel nesne. Yatayda kamyon **sağdan
girer** ve sağ alttaki yükleme rampasına yanaşır — doğrudan sağ başparmağın
menziline.

1. **Kamyon gelir** (1,5 sn). Oyuncu hiçbir şeye dokunmadan fabrikayı görür.
2. **Kasalar rampada yığılır.** Sayı ≈ offline süresi; üçten fazlaysa yığın
   büyür ama sayı üçte kalır.
3. **Dokununca patlar** — para ve ürün ikonları üst soldaki HUD'a uçar. Uçuş
   yolu ekranın boş köşegeninden geçer, zincir bandını kesmez.
4. **Vardiya raporu kart olur.** "Boya 2 sa 10 dk tıkalı kaldı" modal değil,
   alt sağdaki bir karttır — kartın eylemi doğrudan o istasyonu açar.

> **Neden popup değil:** Popup, oyuncunun gördüğü ilk şeyi bir *rapor* yapar.
> Kasa ise ilk şeyi *fabrika* yapar.

---

## 9. Mini oyun yüzeyleri

Üç kural yönelimden bağımsız:

1. **Giriş her zaman sahneden.** Tıkanan makine, psycho işçi, düşen ürün,
   sipariş kasası. Listeden asla.
2. **Geçiş konumu öğretir.** Kamera önce o noktaya yaklaşır, sonra mini oyun
   yüzeyi yükselir.
3. **Çıkışta değişim görünür.** Aynı kameraya dönülür ve düzelttiğin şey
   **1 saniye içinde** gözle görülür.

| Olay | Yatay uyarlaması | Fabrika sonucu | Süre |
|---|---|---|---|
| Perfect Seam | Dikiş hattı yatay uzar — daha uzun, hassas çizgi | Hatalı ürünleri temizler | 20–30 sn |
| Dance-Off | İşçiler yan yana dizilir; ritim şeridi altta | Tüm işçilere moral ve hız | 30–40 sn |
| Conveyor Run | Şeritler yatay akar — asıl kazanan yönelim bu | Düşen ürünleri kurtarır | 15–25 sn |
| Cargo Sort | Kasalar solda, hedefler sağda; sürükleme yatay | Acil siparişi bonusla yollar | 25–35 sn |
| Pressure Chamber | Basınç göstergesi yatay bar; tut–bırak | Psycho işçiyi overdrive'a sokar | 20–30 sn |
| Memory Loom | Desen ızgarası 4×3 olur (dikeyde 3×4 idi) | Blueprint / hikâye parçası açar | 30–40 sn |

> **Dört yönlü swipe uyarısı.** Yukarı/aşağı swipe için `430 px`'de yalnızca
> ~180 px hareket payı kalır; sol/sağ için ~800 px. Bu asimetri dört yönlü
> mekanikleri bozar — **dikey swipe eşiği yatayınkinin yarısı olmalı**
> (örn. 40 px'e karşı 80 px), yoksa oyuncu yukarı kaydırmayı sürekli ıskalar.

**Ödül kuralı.** Hiçbir mini oyun *yalnızca* coin ve XP vermez. Önce ekranda
gördüğümüz somut bir problemi çözer, ödül ondan sonra gelir. Başarısızlık kaynak
yakmaz — fırsatı kaçırır ve istasyonu kısa süre kilitler.

---

## 10. Ekonominin rolleri

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

UI'daki karşılığı: hattan çıkan ürün HUD'da para değil, **ürün sayacını**
artırır. Para yalnızca sevkiyat anında, sağ alttan sol üste uçan gözle görülür
bir akışla HUD'a girer. Oyuncu iki şeyi aynı anda öğrenir: üretim yetmez,
satmak gerekir.

---

## 11. Seans modeli

Yönelim değişikliğinin en az konuşulan ama en ağır sonucu. Kimse 40 saniyelik
bir bakış için telefonu yatay çevirmez.

| Varsayım | Dikey model | Yatay model |
|---|---|---|
| Günlük oturum | 5–6 kısa bakış | 2–3 gerçek oturum |
| Oturum süresi | 40 sn – 5 dk | 4–12 dk |
| Oturum başına karar | 1–2 | 4–6 |
| Hızlı sipariş süresi | 5–10 dk | 10–20 dk |
| Offline tavan | 4 saat | 6–8 saat |
| Dönüş kancası | Dolan kova merakı | Biten hikâye siparişi |

Uzayan offline tavan zorunlu: oturumlar seyrekleştiği için 4 saatlik tavan
oyuncunun kazancını sürekli kırpar ve "geç kaldım" hissi yaratır. **6–8 saat**,
günde iki oturuma denk düşer.

Buna karşılık oturum başına *daha çok karar* sunulmalı — oyuncu oturduğunda
yapacak işi olmalı. Vardiya kartlarının üç yerine **oturum başında beşe kadar
çıkabilmesi**, ilk üçü çözüldükçe kalanların akması bunu sağlar.

> **Tavsiye:** Yalnız yatay yapın. İki yönelimi birden desteklemek arayüzü iki
> kez tasarlamak, iki kez test etmek ve her ikisini de vasat yapmak demektir.
> Yatayın doğal uzantısı tablettir — `4:3`'te adalar kenarda kalır, fabrika
> ortadan büyür, hiçbir şey yeniden konumlanmaz.

---

## 12. İlk 10 dakika

| Süre | Adım | Ne olur | Gizli |
|---|---|---|---|
| 0:00–0:30 | Bant soldan sağa akar | Kamera hattı bir uçtan diğerine tarar, sonra tamamını gösterecek yerde durur. Oyuncu ilk oyuncağı **alt-orta** bölgeden toplar. Hiç metin yok. | nav, vardiya kartları, sipariş şeridi |
| 0:30–1:30 | Boya yavaşlar | Solunda tampon dolar, sağındaki bant boşalır. Darboğazın iki imzası aynı anda ve **yan yana** görünür — yatayın en büyük öğretme avantajı. | nav, sipariş şeridi |
| 1:30–3:00 | İlk işçi ataması | Çekmece alttan yükselir, işçi şeridi görünür. Süre `9.0 → 6.8` iner, bant hızlanır. İlk "ben yaptım" anı. | yükseltme düğmesi (henüz para yok) |
| 3:00–5:00 | İlk sipariş | Şerit üst ortadan iner. Tek seçenek, seçim yok. | sipariş sınıfları, sıradaki slot |
| 5:00–7:00 | Kontrollü arıza | Makine titrer, duman çıkar. **Alt sağda** vardiya kartı belirir — kartların nerede yaşadığı burada öğretilir. Kısa tamir oyunu çözer, bant 1 sn içinde başlar. | diğer mini oyunlar |
| 7:00–9:00 | İlk sevkiyat | Üst şerit parlar, alt sağda *SEVK ET* kartı doğar. Para ilk kez HUD'a akar. Ekonominin kuralı ve "durum üstte, eylem altta" ilkesi aynı anda öğretilir. | — bu an tam görünür olmalı |
| 9:00–10:00 | Repair Alley | Şehir sekmesi ilk kez açılır, ilk aşama başlar, anlamlı bekleme bırakılır. | Luupies sekmesi, kozmetikler |

**İlk beş dakikada asla görünmeyecekler:** Wardrobe · League · Weekly · Alumni ·
tüm ürün modelleri · dört istasyonun tam istatistik tablosu · prestij ·
koleksiyon setleri.

---

## 13. Bölge restorasyonu

| Bölge | Hedef açılış | Eklediği kural | Yatayda görünümü |
|---|---|---|---|
| Repair Alley | 1–2. gün | Arıza ve kalite | Hattın sağ ucuna tamir tezgahı eklenir |
| Candy District | 3–5. gün | Moral ve enerji | Yemekhane ön plana, hattın altına yerleşir |
| Psycho Lab | 7–10. gün | Risk ve overdrive | Çekmeceye overdrive anahtarı gelir |
| Shipping Bay | 14–21. gün | Sipariş yönlendirme | Sağ rampa büyür, şerit ikinci slot kazanır |
| Clocktower | 30. gün+ | Prestij / yeni vardiya | Fabrika Devri arayüzü açılır |

Yatay burada da işe yarar: her yeni bölge hattı **uzatır**, katlamaz. 4
istasyonluk hat 6'ya çıktığında düzen değişmez, sadece genişler — dikeyde bu
ancak ikinci bir kat açarak mümkündü ve okunabilirliği öldürürdü.

Restorasyon aşamaları Şehir sekmesinde **inşaat halinde bina** olarak
gösterilir — ilerleme çubuğu değil, binanın kendisi kademeli tamamlanır. Bu
tarihler telemetriyle ayarlanacak başlangıç hedefleridir.

---

## 14. Uygulama sırası ve kabul ölçütleri

| Sıra | Paket | Kabul ölçütü |
|---|---|---|
| 1 | **Yatay Factory Home dikey dilimi** | Sahne tam ekran · arayüz kaplaması ≤%22 · zincir bandı hiçbir şeyle örtülmüyor · 4 istasyon soldan sağa · çekmece ≤164 px · tampon fiziksel yığın · kasa toplanıyor · bir bağlamsal mini oyun bağlı |
| 2 | **Ergonomi geçişi** | Tüm eylemler alt köşelerde · üst kenarda tek bir dokunulabilir eylem yok · SEVK ET vardiya kartı olarak doğuyor · dikey swipe eşiği yatayın yarısı |
| 3 | **Ekonomi birleştirme** | Hattan doğrudan para gelmiyor · sipariş tek satış noktası · hammadde altıdan bire indi · offline tavan 6–8 saat · sipariş süreleri yeniden dengelendi |
| 4 | **FTUE ve dönüş** | İlk 10 dk beat'leri sırayla tetikleniyor · ilk 5 dk'da yasak ekranlar görünmüyor · dönüşte popup yok, kamyon sağdan giriyor · vardiya kartları oturum başında 5'e kadar çıkıyor |
| 5 | **Bölge restorasyonu ve meta** | Bölgeler aşamalı projeyle açılıyor · hat uzuyor, katlanmıyor · kozmetikler karakterde görünüyor · Fabrika Devri |

### Ölçülebilir başarı sinyalleri

- **Arayüz kaplaması:** ≤%22 — geri kalan her piksel fabrika
- **Zincir bandı bütünlüğü:** orta 180 px'i örten arayüz öğesi sayısı sıfır
- **Karar mesafesi:** Açılıştan ilk anlamlı karara ≤2 dokunuş
- **Erişilebilirlik:** Üst kenarda dokunulabilir eylem sayısı sıfır
- **Çekmece yüksekliği:** ≤164 px (%38)
- **Ana navigasyon:** 3 sekme, alt sol, açılış her zaman Fabrika
- **Mini oyun bağlamı:** Katalogdan açılabilen mini oyun sayısı sıfır
- **Oturum:** Medyan 4–12 dk, günde 2–3 oturum

> **Tek cümlelik kabul testi.** Oyunu hiç görmemiş birine telefonu **yatay**
> uzatın ve hiçbir şey söylemeyin. **30 saniye içinde "şurada bir sorun var"
> diyerek doğru istasyonu işaret edebiliyorsa** Factory Home V2 çalışıyor
> demektir.
