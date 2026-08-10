# Luupie — Çekirdek Üretim Döngüsü

> ⚠️ **Bu doküman `LUUPIE-SPEC.md` içinde birleştirildi.**
> Tek yetkili tasarım dokümanı odur; bu dosya tarihsel kayıt olarak duruyor.

Fabrikayı bir sayaçtan gerçek bir idle simülasyona çeviren sistem: **darboğazlı
üretim zinciri**. Mevcut mini oyunları da yük taşır hale getirir.

---

## 1. Teşhis: elimizde neden idle oyun yok

Şu anki ekonomi tek satır. Her Ponchiq 20 saniyede bir `product` üretiyor, ürün
başına 2 altın geliyor, psycho bunu 2'ye katlıyor. Bu bir **sayaç**, simülasyon
değil.

Eksik olan grafik ya da içerik değil — **karar**. İyi bir idle oyunda oyuncu her
seansta "şu an elimdeki kaynağı nereye koyarsam çıktım artar?" sorusuna cevap
verir. Bizde bu sorunun cevabı hep aynı: daha fazla Ponchiq al. Tek kaldıraç,
tek yön, sıfır optimizasyon.

İkinci bedeli: üç mini oyun ekonomiye **bağlı değil**. Tamir istasyonu rastgele
bir zamanlayıcıyla açılıyor, yemekhane sevgi barını dolduruyor ama sevginin
üretimle tek teması %25 eşiği. Mini oyunlar iyi çalışıyor; sorun onların
bağlandığı bir sistemin olmaması.

---

## 2. Öneri: darboğazlı üretim zinciri

Oyuncak tek parçada değil **dört aşamada** üretilir. Her aşama bir istasyondur;
istasyonlar arasında tampon (ara stok) vardır. Bir istasyon ne kadar hızlıysa
değil, **zincirin en yavaş halkası ne kadar hızlıysa** fabrika o kadar üretir.

```
  Pamuk Presi      Dikiş Tezgahı      Boya & Süsleme      Paketleme
  6.0 sn/parça     7.5 sn/parça       9.0 sn/parça        5.0 sn/parça
  ● Şefo (88)      ● Pofu (61)        ○ işçi yok ×0.30    ● Vako (74)
      │                  │                   │                 │
      └──[ 2/8 ]────────►└──[ 8/8 ]─────────►└──[ 0/8 ]───────►│
          normal            YIĞILMA              AÇ KALIYOR      🧸 + altın
                              ▲                     ▲
                              └── DARBOĞAZ ─────────┘

  Fabrika hızı = en yavaş istasyon = 9.0 sn/parça → saatte ~400 oyuncak
  Boya'ya işçi ata → ×0.30 yerine ×1.15 → darboğaz Dikiş'e kayar
```

Darboğazın iki imzası vardır ve ikisi de ekranda görünür: **öncesinde tampon
dolup taşar, sonrasında istasyon aç kalır.** Oyuncunun okuması gereken tek şey
bu. Bu tek kural bütün oyunu doğurur: oyuncu ekrana bakıp darboğazı gözle görür,
altınını oraya harcar — ve darboğaz bir sonraki istasyona kayar.

---

## 3. Ponchiq'ler artık işçi

Bugün karakterler rastgele dolaşıyor ve havadan ürün üretiyor. Bunun yerine her
Ponchiq bir istasyona **atanır**, oraya yürür ve orada çalışır. Amaçsız gezinme
biter; izometrik sahne okunabilir hale gelir.

Bir istasyonun hız çarpanı şu üçünün çarpımıdır:

| Etken | Çarpan | Not |
|---|---|---|
| İşçi yok | ×0.30 | İstasyon otomatik ama cılız çalışır — durmaz, sürünür |
| Sevgi düzeyi | ×0.55 – ×1.30 | `0.55 + sevgi/100 × 0.75` — sürekli, eşiksiz |
| Tür yatkınlığı | ×1.35 | Şefo preste, Cıvata boyada, Vako pakette |
| Psycho | ×2.00 | Ama üretiminin %18'i **hatalı** çıkar |

Sevginin sürekli çarpana dönüşmesi tek başına büyük kazanım: okşamak ve beslemek
artık "eşiğe düşmesin" bakımı değil, doğrudan üretim hızı. **Yemekhane mini
oyunu böylece ekonominin içine girer.**

### Tür yatkınlığı koleksiyonu anlamlandırır

| İstasyon | Yatkın türler |
|---|---|
| Pamuk Presi | Şefo (domuz), Ponpon (ayı) |
| Dikiş Tezgahı | Pofu (tavşan), Mırmır (kedi) |
| Boya & Süsleme | Uni (tek boynuz), Çako (punk) |
| Paketleme | Vako (ördek), Cıvata (robot) |
| Serbest | Rako (kurt) — her istasyonda ×1.15, gece ×1.4 |

"Yeni Luupie sahiplen" kararı estetik olmaktan çıkıp hat kurma kararına dönüşür:
boyada zayıfsam Cıvata veya Uni almalıyım.

---

## 4. Psycho: kumar artık ölçülebilir

Konsept dokümanındaki "Verimlilik Takası" şu an sadece bir çarpan. Zincir bunu
gerçek bir kumara çevirir:

- **Kazanç:** Psycho işçi istasyonu **2 kat** hızlı çalıştırır. Darboğazdaki bir
  psycho, tüm fabrikanın çıktısını neredeyse ikiye katlar.
- **Bedel:** Ürettiğinin %18'i **hatalı** çıkar. Hatalılar zincirde ilerler ve
  **Paketleme'yi tıkar** — paketleme hızı yarıya iner, tıkanıklık temizlenene
  kadar.

Tıkanıklığı temizlemenin yolu **Tamir İstasyonu mini oyunu**. Böylece tamir,
rastgele açılan bir yan aktivite olmaktan çıkar; oyuncunun kendi açgözlülüğünün
sonucu olur. Dokümanın "villain dışarıdan gelmez" fikrinin mekanik karşılığı.

Oyuncunun üç meşru seçeneği olur:
1. **Zapt et** (Oyuncak Krizi) — 2x biter, hata durur
2. **Besle** (Yemekhane) — sevgi yükselir, kendiliğinden Sweet'e döner
3. **Bırak çalışsın** — tamir yükünü kabullen; ileri oyuncunun stratejisi

---

## 5. Uzun yol: oyuncak modelleri

Tek tip ürün seviye 10'dan sonra sıkıcı olur. Fabrika aynı anda tek bir **model**
üretir; model değiştirmek 45 saniyelik hat kurulumu ister. Bu, "şimdi mi geçeyim
yoksa eldeki siparişi bitireyim mi?" kararını doğurur.

| Model | Aşama süresi | Değer | Açılış |
|---|---|---|---|
| Pamuk Ayıcık | ×1.0 | 3 🪙 | Başlangıç |
| Peluş Tavşan | ×1.4 | 6 🪙 | Sv 4 |
| Robot Figür | ×2.0 | 14 🪙 | Sv 8 |
| Tek Boynuz | ×3.0 | 40 🪙 | Sv 14 |

Değer artışı süre artışından hızlı büyür, yani üst modeller her zaman daha
kârlıdır — **ama ancak hattınız onları besleyebiliyorsa**. Tek Boynuz'a geçip
zinciri çökertmek gerçek bir hata olabilmeli; oyuncu geri dönebilmeli.

### Siparişler seansa hedef verir

Yaklaşık 18 dakikada bir sipariş düşer: *"20 × Peluş Tavşan → 850 🪙 + 3 yıldız
tozu"*, 2 saat geçerli. Sayı büyütmekten ibaret döngüye bitiş çizgisi koyar ve
haftalık lige doğrudan hacim yazar.

---

## 6. Offline simülasyon

Şu an offline birikim düz çarpım: `süre / 20sn × 0.6`. Zincirle birlikte bu,
gerçek bir **ileri sarım** olur — 30 saniyelik adımlarla, tampon ve darboğaz
kurallarına uyarak, 4 saat tavanla.

Getirisi sadece doğruluk değil; **dönüş ekranı artık bir şey anlatır**:

```
  TEKRAR HOŞ GELDİN — 3 sa 40 dk

  612 oyuncak · 3.670 🪙

  ⚠ Boya & Süsleme 2 sa 10 dk tıkalı kaldı — Uni psycho'ya döndü,
    hatalılar paketlemeyi kilitledi.
    Tampon dolduğu için Dikiş Tezgahı da 1 sa 20 dk boşta bekledi.
```

Bu ekran oyuncuya **ne yapacağını söyler**. "Kaybettin" demez — potansiyelin ne
kadarını topladığını gösterir ve bir sonraki seansa somut iş verir. Dokümanın
"ceza değil, kaçan fırsat" felsefesiyle birebir uyumlu.

---

## 7. Bir seans neye benzer

Doküman 40 saniye – 5 dakika arası seanslar istiyor. Zincir bunu doğal üretir:

| Süre | Adım | Ne olur |
|---|---|---|
| 0:00 | Offline raporu | Ne üretildi, hangi istasyon tıkandı. Topla. |
| 0:08 | Hattı oku | Kırmızı istasyon ve dolu tampon nerede? Tek bakış. |
| 0:15 | Sorunu çöz | Tıkanıklık → Tamir, düşük sevgi → Yemekhane, psycho → Oyuncak Krizi. **Mini oyunlar buraya oturur.** |
| 1:30 | Darboğazı yükselt | Biriken altını en yavaş istasyona harca. Darboğaz kayar. |
| 1:50 | Ayarla | İşçi yerlerini değiştir, sipariş kabul et, modeli yükselt. |
| 2:20 | Çık | Fabrika arkada çalışmaya devam eder. |

Kritik nokta: **3. adım zorunlu değil ama kârlı.** Casual oyuncu sadece yükseltme
yapıp çıkar; hırslı oyuncu üç mini oyunu da oynayıp aynı süreden iki katı verim
alır. Dokümandaki "beceri tavanı" tam olarak burada oluşur.

---

## 8. Prestij: Fabrika Devri

Mezuniyet sistemi zaten var — Ponchiq'ler 48 saatte sahipleniliyor ve albüme
giriyor. Üstüne uzun vadeli sıfırlama gelir: seviye 20'de **Fabrika Devri**
açılır. İstasyon seviyeleri ve altın sıfırlanır; karşılığında her mezun Ponchiq
bir **Mezun Yıldızı**'na dönüşür ve her yıldız kalıcı **+%4 global hız** verir.

Albüm dekoratif koleksiyon olmaktan çıkıp prestij para birimi olur — "iyi bak,
mezun et, tekrarla" döngüsü uzun vadede de ödüllendirilir.

---

## 9. İlk sayısal ayar

Hepsi `js/data.js` içindeki `CONFIG`'e girer, hiçbiri koda gömülmez:

| Parametre | Değer | Gerekçe |
|---|---|---|
| İstasyon temel süreleri | 6.0 / 7.5 / 9.0 / 5.0 sn | Boya kasten başlangıç darboğazı — ilk ders orada verilir |
| Yükseltme etkisi | hız ×1.18 / seviye | 4 seviyede ~2 kat; ilerleme hissedilir |
| Yükseltme maliyeti | 120 × 1.60^(S−1) | Maliyet hızdan hızlı büyür → sonsuz tek istasyon yatırımı engellenir |
| Tampon kapasitesi | 15 + 5 × seviye | Kısa devamsızlığı yutar, uzun ihmali cezalandırır |
| Hata oranı (psycho) | %18 | Sürekli tamir gerektirmeyecek, görmezden gelinemeyecek kadar |
| Tıkanma cezası | paketleme ×0.5 | Öldürücü değil; "şu an ilgilen" sinyali |
| Offline verim / tavan | %60 · 4 saat | Mevcut değerler korunur, zincire uyarlanır |
| Model geçiş süresi | 45 sn | Kararı gerçek yapacak kadar, sinir bozacak kadar değil |

Bu sayılar başlangıç noktası; asıl ayar oynayarak yapılır. Önemli olan hepsinin
tek yerde ve veri olarak durması.

---

## 10. Uygulama planı

Üç fazda, her fazın sonunda oyun oynanabilir kalır.

### Faz 1 — zorunlu: zincir çalışsın
Dört istasyon, tamponlar, darboğaz kuralı, işçi atama, yükseltme paneli ve
zincire dayalı offline simülasyon. **Bu faz tek başına oyunu idle oyuna
çevirir.** Yeni dosya `js/production.js` — hem canlı tick hem offline ileri
sarım aynı fonksiyonu kullanır, böylece iki ekonomi arasında sapma olamaz.

### Faz 2 — derinlik: mini oyunları bağla
Sevgi → sürekli verim çarpanı. Psycho → hatalı ürün → paketleme tıkanması →
Tamir mini oyunu. Tür yatkınlıkları. Bu fazdan sonra üç mini oyunun da ekonomik
bir sebebi olur.

### Faz 3 — meta: uzun yol
Oyuncak modelleri ve hat kurulumu, siparişler, Fabrika Devri prestiji, ligin
sipariş hacmiyle beslenmesi.

### Dokunulacak dosyalar

| Dosya | İş |
|---|---|
| `js/production.js` | **yeni** — zincir simülasyonu (canlı + offline ortak) |
| `js/data.js` | İstasyon, model, yatkınlık tanımları ve tüm sayısal ayar |
| `js/ponchiq.js` | `produceTimer` yerine istasyon ataması, hedefe yürüme, çalışma animasyonu |
| `js/factory.js` | İstasyonları, tamponları ve tıkanma parıltısını izometrik sahneye çiz |
| `js/ui.js` | İstasyon paneli: yükselt, işçi ata, model seç |
| `js/game.js` | Durum şeması, kayıt göçü, offline raporu |
| `js/minigames.js` | Tamir tıkanmayı temizler, yemekhane sevgiyi hedefe yönlendirir |
| `tests/` | Zincir matematiği birim testleri |

Test edilecekler: darboğaz doğru hesaplanıyor mu, tampon taşınca üst istasyon
duruyor mu, offline ileri sarım canlı simülasyonla aynı sonucu veriyor mu.

### Kayıt uyumluluğu
Mevcut `luupie_save_v1` kayıtlarında istasyon yok. Yükleme sırasında varsayılan
istasyon seti oluşturulur ve eldeki Ponchiq'ler sırayla atanır — kimse
ilerlemesini kaybetmez. Kayıt anahtarı `v2`'ye çıkar.

---

## 11. Kasten dışarıda bıraktıklarım

Bir idle oyuna eklenebilecek her şeyi eklemek, oyunu ilk günden yönetilemez
yapar. Şunları bilerek almıyorum:

- **Birden fazla oda / kat.** Tek oda, tek zincir. Dikey ekranda ikinci kat
  okunabilirliği öldürür. Genişleme gerekirse istasyon sayısı 4'ten 6'ya çıkar,
  oda sayısı değil.
- **Hammadde satın alma ekonomisi.** Pamuk sonsuz. İkinci kaynak para birimi,
  karar sayısını artırmadan tabloyu karmaşıklaştırır.
- **İşçi seviye/beceri ağacı.** Sevgi + tür yatkınlığı zaten iki boyut.
  Üçüncüsü Ponchiq'leri tablo satırına çevirir, karakter olmaktan çıkarır.
- **Psycho Kargo (sosyal katman).** Dokümanda var ve iyi bir fikir, ama sunucu
  ister. Tek oyunculu çekirdek oturmadan sosyal katman inşa etmek erken.

Hepsi Faz 3 sonrası tekrar masaya gelebilir — çekirdek döngü kanıtlandıktan
sonra.
