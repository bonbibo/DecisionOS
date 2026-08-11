# Luupie — İşleyiş Planı

Aynı iş, **oyunun kendi akışına göre** kesilmiş hâli. `URETIM-PLANI.md` işi
fazlara ve efora göre böler; bu doküman **davranışa** göre böler: hangi şey
ne zaman gerçekten çalışmaya başlar, çalıştığı nasıl anlaşılır, ve neden o
sırada.

> **Tek kural:** Her blok, bir öncekinin yarattığı durumu kullanır. Sıra
> keyfi değil — bir bloğu erkene almak, onu boşluğa tasarlamak demektir.

---

## Blokların sırası

```
A AKIŞ ──▶ B TIKANMA ──▶ C OKUMA ──▶ D MÜDAHALE ──▶ E KARŞILIK
                                                        │
   ┌────────────────────────────────────────────────────┘
   ▼
F YIPRANMA ──▶ G DÖNÜŞ ──▶ H BESLEME ──▶ I BÜYÜME ──▶ J BASKIN
```

| Blok | Oyunun o andaki tek cümlelik hâli | Faz |
|---|---|---|
| **A** Akış | Bozuk oyuncak giriyor, onarılmış çıkıyor | 1 |
| **B** Tıkanma | Hat kendi kendine tıkanıyor | 1 |
| **C** Okuma | Tıkanmanın nerede olduğu **bakınca** anlaşılıyor | 1 |
| **D** Müdahale | Oyuncu tıkanmayı açabiliyor ve açtığını görüyor | 1 |
| **E** Karşılık | Açmanın karşılığı para, paranın karşılığı hız | 1 |
| **F** Yıpranma | Çözüm kalıcı değil — işçiler yoruluyor | 1 |
| **G** Dönüş | Çıkmanın ve geri gelmenin anlamı var | 1 |
| **H** Besleme | Yorgunluğu **oynayarak** çözebiliyorsun | 2 |
| **I** Büyüme | Fabrika ve şehir gerçekten büyüyor | 3 |
| **J** Baskın | Savaş, hattı hızlandıran bir kısayol | 4 |

---

## A · AKIŞ — "Bir oyuncak baştan sona geçiyor"

### Ne olur

Kapıdan bozuk bir oyuncak gelir. Banda düşer, TEŞHİS'e girer, çıkar, SÖKME'ye
girer, ONARIM, CİLA, ve sağ uçtan onarılmış olarak çıkar. Kimse müdahale
etmez, hiçbir şey tıkanmaz. Sadece **akar**.

### Sırayla

1. Bozuk oyuncak üretimi: kapıdan düzenli aralıkla girer
2. Bant: soldan sağa taşır
3. Dört istasyon: her biri gireni bir süre tutar, sonra bırakır
4. İstasyon süresi: her istasyonun kendi işlem süresi var, farklı
5. Onarılmış oyuncak: sağ uçta biriken bir yığın
6. İşçiler sahnede: istasyonlarında duruyor, çalışma animasyonu dönüyor

### Bitti sayılır ki

> Ekrana 60 saniye bakıyorsun, hiçbir şeye dokunmuyorsun, ve **soldan giren
> bozuk oyuncağın sağdan onarılmış çıktığını gözle takip edebiliyorsun.**

Bu blokta hiçbir sayı, hiçbir panel, hiçbir düğme yok. Sadece hareket.

### Erken yapılırsa ne olmaz

Bu ilk blok — öncesi yok. Ama şu **sonraya bırakılmamalı**: istasyon
süreleri baştan **farklı** olmalı. Hepsi eşitse hat asla tıkanmaz ve B bloğu
test edilemez.

---

## B · TIKANMA — "Hat kendi kendine bozuluyor"

### Ne olur

İstasyonlar farklı hızda çalıştığı için hattın bir yerinde iş birikir. Yavaş
istasyonun **solunda** yığın büyür; **sağındaki** bant boşalır. Yığın tavana
vurunca soldaki istasyon **durur** — çıktısını koyacak yer yoktur. Tıkanma
zincirleme geriye yürür.

Aynı kural sağ uçta da geçerli: onarılmış oyuncaklar sevk edilmezse CİLA
tıkanır, CİLA tıkanınca ONARIM tıkanır, hat kilitlenir.

### Sırayla

1. Tampon: her istasyon arasında bir bekleme yığını, üst sınırı var
2. **Tamponu dolan istasyon durur** — yavaşlamaz, durur
3. Tamponu boş kalan istasyon **aç kalır** — işi yok, bekler
4. Çıktı yığını dolunca hat baştan sona kilitlenir
5. **İki hasar tipi:** sökük dikiş (ONARIM'ı yorar) · solmuş boya (CİLA'yı yorar)
6. Gelen iş karışımı değiştikçe **darboğaz kayar**

### Bitti sayılır ki

> Hiç dokunmadan 3 dakika izlersen hat **tıkanır ve kilitlenir**. Ve gelen
> hasar tipi karışımını değiştirdiğinde, tıkanmanın yeri **başka bir
> istasyona geçer**.

İkinci cümle bu bloğun asıl testi. Darboğaz hep aynı yerde kalıyorsa hasar
tipi sistemi çalışmıyor demektir — ve bu, oyunun çekirdek fikri.

### Bundan önce Okuma yapılırsa

Gösterecek bir şey yoktur. Darboğaz görsel dilini tıkanma olmadan tasarlarsan,
neyi göstermesi gerektiğini tahmin etmiş olursun. Önce **gerçek** tıkanma,
sonra onu anlatan dil.

---

## C · OKUMA — "Sorunun nerede olduğu bakınca anlaşılıyor"

### Ne olur

Oyuncu ekrana bakar ve **hangi istasyonun suçlu olduğunu** panele girmeden
söyler. Öğretilen tek kalıp:

> **Dolu yığın ile boş bandın arasındaki istasyon suçludur.**

### Sırayla

1. Tampon yığını **fiziksel** görünür: 3 kutu ile 30 kutu farklı görünür
2. Bant yoğunluğu görünür: tıkanan tarafta sık, aç tarafta seyrek
3. İşçi davranışı durumu anlatır: yetişemeyen hızlı ve panik, aç kalan
   esniyor, işsiz elleri cebinde dolaşıyor
4. Tıkanan istasyon `⛔` baloncuğu açar
5. İşçisiz istasyon `👤?` baloncuğu açar
6. Aynı anda en fazla iki baloncuk; üçüncüsü köşedeki sayaca yazılır
7. Hiçbir durum **yalnızca renkle** anlatılmaz — her birinin ikinci kanalı var

### Bitti sayılır ki

> **Ekran görüntüsü testi:** Oyunun görüntüsünü al, arayüzü kırp. Kalan
> görüntü tek başına şunu anlatmalı: hangi istasyon yavaş, nerede yığılma
> nerede boşluk, kim çalışıyor kim boşta.
>
> **30 saniye testi:** Oyunu hiç görmemiş birine telefonu uzat, hiçbir şey
> söyleme. 30 saniyede "şurada bir sorun var" deyip **doğru istasyonu**
> göstermeli.

### Bundan önce Müdahale yapılırsa

Oyuncu rastgele düğmeye basar. Doğru istasyona müdahale ettiğinde bile
"ben çözdüm" hissi doğmaz, çünkü neyi çözdüğünü bilmiyordur. Müdahalenin
tatmini **teşhisin doğru olmasından** gelir.

---

## D · MÜDAHALE — "Açabiliyorum ve açtığımı görüyorum"

### Ne olur

Oyuncu darboğaza dokunur, panel açılır, bir şey yapar, panel kapanır — ve
**hat gözünün önünde hızlanır.** Bilgi sahnede, karar panelde.

### Sırayla

1. İstasyona dokunma → panel açılır (%66 × %90, arkada sahne görünür)
2. **İşçi atama:** boştaki Luupie'yi istasyona koy
3. Çarpan **ayrı ayrı** gösterilir: işçi ×, yatkınlık ×, moral ×, hızlanma ×
4. **Yükseltme:** düğme satın almadan önce sonucu yazar — `3.9 → 3.3 sn · +%18`
5. Yatkınlık: türü istasyonla eşleşen işçi ×1.35
6. **Dönüş deltası** — panel kapanınca zorunlu koreografi:
   makineye doğru küçülerek kapan → parlama → üstünde `19.3 → 3.2 sn` çipi →
   bant rampayla hızlanır → **tampon yığını gözle görülür şekilde erir**
7. Öneri motoru: hat hızına en çok katkı yapan eylemi başa koyar —
   darboğazda işçi yoksa öneri "yükselt" değil **"ata"**

### Bitti sayılır ki

> Panel kapandıktan sonraki **1 saniye içinde**, panele bakmadan, bir şeyin
> değiştiğini görüyorsun. Ve tampon yığını erimeye başlıyor.

Hiçbir şey değişmediyse koreografi çalışmaz, panel sessizce kapanır. Yalan
söyleyen bir kutlama, kutlama olmamasından kötüdür.

### Bundan önce Karşılık yapılırsa

Para vardır ama harcamanın anlamı yoktur. Yükseltme maliyetlerini neye göre
ayarlayacağını bilemezsin, çünkü yükseltmenin **ne kadar işe yaradığını**
henüz ölçmedin.

---

## E · KARŞILIK — "Açmanın karşılığı para, paranın karşılığı hız"

### Ne olur

Onarılmış oyuncaklar birikir. Sipariş kartı "8/8 hazır" der. Oyuncu sevk
eder — kamyon yanaşır, kutular yüklenir, paralar HUD'a uçar. Para darboğaza
yatırılır. Hat hızlanır. Halka kapanır.

### Sırayla

1. Sipariş: aynı anda **bir aktif + bir sıradaki**, üçüncüsü yok
2. **Sevkiyat, hattı açan zorunlu eylemdir** — sevk etmezsen çıktı yığını
   dolar ve hat kilitlenir (B bloğundaki kural)
3. Sevkiyat kutlaması: kamyon → yükleme → para uçuşu → sayaç sayarak artar →
   işçiler el sallar → yeni sipariş düşer
4. **Sipariş düğmesi hiçbir şeyin altında kalmaz** — mevcut prototipte oyunu
   45 saniyede kilitleyen hata tam olarak buydu
5. **Birleştirme:** 3 aynı → bir üst seviye · 5 karışık → rastgele üst seviye
6. Sipariş sınıfları: standart · kaliteli (+%33 prim) · butik (+%53) ·
   acele (+%81, kaçarsa kaybolur)
7. Hat **yalnızca Seviye 1** üretir — değer birleştirmeden gelir
8. Kaynak maliyeti: her istasyon pamuk/iplik/parça yer, biten istasyon aç kalır
9. Enerji overdrive (×2, 10 enerji) ve geri dönüşüm tezgahı

### Bitti sayılır ki

> Bir oturumda şunu yapabiliyorsun: darboğazı bul → işçi ata → hat hızlanır →
> sipariş dolar → sevk et → para gelir → **o parayı bir sonraki darboğaza
> yatır.** Ve döngü baştan başlar, biraz daha hızlı.

### Bundan önce Yıpranma yapılırsa

Oyuncuya sorun çıkarmış ama çözecek kaynağı vermemiş olursun. Moral düşüşü
"ceza" gibi hissedilir. Önce kazanma yolu, sonra yıpranma.

---

## F · YIPRANMA — "Çözüm kalıcı değil"

### Ne olur

Kurduğun düzen bozulmaya başlar. İşçiler çalıştıkça yorulur, moralleri düşer,
hat yavaşlar. Kimse hata yapmadı — **üretimin kendisi bir gider üretiyor.**

Bu blok oyuna zamanı sokar. Ondan önce oyun bir bulmacaydı; buradan sonra bir
**işletme**.

### Sırayla

1. Moral düşüşü: hatta çalışan −6/saat · boşta bekleyen −2/saat
2. Moral doğrudan çarpana girer: `0.55 + sevgi/100 × 0.75`
3. **Kantin rafı:** 60'ın altına düşen işçi arka planda kuru yemek yer —
   1 malzeme → +4 moral, **tavanı 60**
4. Nötr nokta 60 = ×1.00. Yani oyun kendi kendini ×1.00'de dengeler:
   ceza yok, ama üstü de yok
5. **Psycho:** moral 25'in altında dönüşür — ×2 hız ama ürünün %18'i hatalı,
   hatalılar paketlemeyi tıkar
6. Psycho'dan üç çıkış: besle · zapt et · bırak çalışsın
7. Malzeme akışı (bu blokta sabit oranlı; gerçek binası I bloğunda gelir)

### Bitti sayılır ki

> Hattı mükemmel kurup 4 saat bırakıyorsun. Geri döndüğünde hat hâlâ
> çalışıyor ama **daha yavaş** — ve nedenini işçilerin yüzünden anlıyorsun.
> Bir işçi psycho'ya dönmüşse hattın çıktısında hatalı ürünler görüyorsun.

### Bundan önce Besleme yapılırsa

Beslenecek bir açlık yoktur. Yemekhane, karşılığı olmayan bedava bir buff'a
döner — mimarinin tam olarak kaçındığı şey. **Önce gider, sonra çözüm.**

---

## G · DÖNÜŞ — "Çıkmanın ve geri gelmenin anlamı var"

### Ne olur

Oyuncu çıkar. Fabrika çalışmaya devam eder. Geri döndüğünde ekranda bir
popup değil, **sahnede biriken şeyler** bulur: kasalar, dolmuş sipariş,
düşmüş moraller. Ve ilk 10 dakikasını hiç görmemiş biri de aynı akışa
sorunsuz girer.

### Sırayla

1. Çevrimdışı ilerleme, **tavan 4 saat**
2. Dönüş sahnesi: kamyon sağdan girer, kasalar rampada yığılır, dokununca
   patlar, para HUD'a uçar — modal yok
3. Vardiya raporu **kart** olur, ekranı kaplamaz
4. Geri dönme sebepleri netleşir: dolan yığın · biten sipariş · **düşen
   moral** · dolan enerji
5. **İlk 10 dakika akışı:**
   - 0:00 bant akar, ilk oyuncak toplanır *(nav, görev, sipariş gizli)*
   - 0:30 bir istasyon yavaşlar, solunda tampon dolar
   - 1:30 ilk işçi ataması — ilk "ben yaptım"
   - 3:00 ilk sipariş, tek seçenek
   - 5:00 kontrollü arıza, kısa tamir, bant 1 sn'de başlar
   - 7:00 ilk sevkiyat, para ilk kez HUD'a akar
   - 9:00 restorasyon başlar
6. İlk beş dakikada görünmeyecekler: kozmetik · lig · albüm · koleksiyon ·
   geri dönüşüm · tüm istatistik tablosu

### Bitti sayılır ki

> Oyunu kapatıp 3 saat sonra açtığında, **ne olduğunu sana kimse yazmadan**
> sahneye bakarak anlıyorsun: şu kadar kasa birikmiş, sipariş dolmuş,
> şu işçinin morali düşmüş.
>
> Ve ikinci oturumunu **hatırlatma olmadan** başlatıyorsun.

Bu blokla birlikte **Faz 1 biter ve oyun tek başına yayınlanabilir.**

---

## H · BESLEME — "Yorgunluğu oynayarak çözüyorum"

### Ne olur

Aç işçinin başında baloncuk çıkar. Yemekhaneye geçersin. 60–90 saniye
doğrayıp pişirip tabaklarsın. İşçiler yer, moralleri fırlar, hat hızlanır.

**Aktif oynanışın pasif kazanca dönüştüğü tek yer burası.**

### Sırayla

1. Malzeme kaynağı ve deposu — **tek kapı bu**, zamanlayıcı cooldown yok
2. Mutfak zinciri: doğra → pişir → tabakla, dokunuşla
3. Yanma: fazla pişen yemek çöp olur → **3 malzeme yanar** (gerçek bedel)
4. Masadaki işçinin sabrı: beklerken morali **düşmeye devam eder**
5. Servis → **+25 moral, tavan 100** — 3 malzeme karşılığı
6. Girişler yalnızca sahneden: aç işçi baloncuğu · vardiya sonu kartı
7. Psycho'dan çıkışın en ucuz yolu buraya bağlanır

### Neden bu bir döngü, hediye değil

| Yol | Malzeme | Kazanç | Verim | Tavan |
|---|---|---|---|---|
| Kantin rafı (pasif) | 1 | +4 | 4 moral/malzeme | 60 → ×1.00 |
| **Yemekhane (aktif)** | 3 | +25 | **8.3 moral/malzeme** | 100 → ×1.30 |

Aktif oynamak **aynı kaynağı 2 kat verimli harcamak** demek. Bedava güç değil.

### Bitti sayılır ki

> Yemekhane oynamayan bir oyuncu hattı ×1.00'de tutuyor ve oyunu bitirebiliyor.
> Düzenli oynayan ×1.20–1.25'e çıkıyor. **×1.30'da sürekli kalınabiliyorsa
> malzeme çok bol demektir** — denge bozuk.

---

## I · BÜYÜME — "Fabrika ve şehir gerçekten büyüyor"

### Ne olur

Siparişlerden gelen **plan** ile şehre çıkarsın. Kaynak binaları kurarsın,
yükseltirsin. Bölgeleri restore edersin. Her yeni bölge tamirhaneye bir
**yeni kural** ekler — hat uzar, katlanmaz.

Bu bloğa kadar sabit oranla akan her kaynak, burada **gerçek bir binaya**
devredilir.

### Sırayla

1. Şehir sahnesi + plan para birimi
2. Kaynak binaları: Pamuk Tarlası · İplikhane · Parça Atölyesi
3. **Depo kuralı:** bina depo dolana kadar üretir, **sonra durur** —
   oyuncu toplayana kadar kaynak fabrikaya gitmez
4. **Mutfak Serası** — H bloğundaki sabit malzeme akışını devralır
5. **Hurdalık** — nadir parça, 6 saatte 1
6. İstasyon Seviye 10 üstü **nadir parça** ister
7. Bölge restorasyonu: çok aşamalı proje, **inşaat hâli binanın kendisinde
   görünür** — ilerleme çubuğu değil
8. **3. ve 4. hasar tipi** bölge açılışıyla gelir — darboğaz okuması bir kez
   daha tazelenir
9. Yeni istasyon slotu
10. Koleksiyon atölyesi — ekonominin nihai sink'i

### Bitti sayılır ki

> 14 gün boyunca oynadığında **hiçbir kaynak sürekli tavanda ve sürekli
> sıfırda değil**, ilerleme durmuyor, ve her yeni bölge hattı okumanı
> değiştiriyor.

Bu bir hesap tablosu işi. 14 günü oynamadan **önce tabloda** simüle et,
sonra oynayarak doğrula.

---

## J · BASKIN — "Savaş, hattı hızlandıran bir kısayol"

### Ne olur

Vahşi psycho oyuncaklar tamirhaneyi basar. Kadronu seçersin, her savaşçıya
ekipman olarak **onarılmış bir oyuncak** verirsin, 90–120 saniye dalga
savunursun. Kazanırsan nadir parça ve hasarlı düşman oyuncak alırsın —
ikincisi hattın en değerli girdisi.

### Sırayla

1. Battle sahnesi + dalga iskeleti
2. Kadro seçimi — **savaşan Luupie o sırada hatta çalışamaz**
3. **Ekipman kilidi:** verdiğin onarılmış oyuncak siparişe koyulamaz →
   battle, hattın çıktısı için siparişle **yarışır**
4. Yatkınlık sistemi savaşa uyarlanır — aynı karakter, aynı mantık
5. Ödül: nadir parça · hasarlı düşman oyuncak (daha değerli girdi)
6. Kayıp: ekipman **kırılır** → hatta bozuk oyuncak olarak döner
   *(kayıp değil, gecikme — hiçbir yerde ölü uç yok)*
7. Her savaş: kadro **−15 moral** → doğrudan yemekhaneye talep

### Bitti sayılır ki

> Battle oynayan ile oynamayan iki hesabı 14 gün paralel koştur.
> Oynayan **1.8×–2.2×** daha hızlı ilerlemeli.
>
> 2.5×'in üstü "battle fiilen zorunlu oldu" demektir → Hurdalık hızlandırılır.
> Bu bir yan oyun; duvar değil, kısayol.

---

## Sıranın özeti — neden bu düzen

Her ok, "bu olmadan sonraki anlamsız" demek:

| Sıra | Olmadan sonraki ne olur |
|---|---|
| A → B | Akış yoksa tıkanacak bir şey yok |
| B → C | Tıkanma yoksa görsel dili boşluğa tasarlarsın |
| C → D | Okuma yoksa oyuncu rastgele basar, "çözdüm" hissi doğmaz |
| D → E | Müdahale ölçülmeden yükseltme fiyatı ayarlanamaz |
| E → F | Kazanma yolu yokken yıpranma **ceza** gibi hissedilir |
| F → G | Yıpranma yoksa geri dönmek için sebep yok |
| F → H | Açlık yoksa yemekhane **bedava buff**'a döner |
| E → I | Plan'ın nereden geldiği belirsizse şehir havada kalır |
| I → J | Nadir parçanın yavaş alternatifi yoksa battle **zorunlu** olur |

---

## Her blok sonunda oyun oynanır durumda

Bu planın en önemli özelliği: **hiçbir blok, sonraki bloğu bekleyen bir
boşluk bırakmaz.** Henüz gelmemiş sistemin yerine sabit değerli bir vekil
durur, o blok gelince vekil gerçek sistemle değişir.

| Blokta | Henüz yok | Yerinde ne var |
|---|---|---|
| A–E | Moral | İşçi çarpanı sabit ×1.00 |
| F–G | Yemekhane | Kantin rafı tek başına — hat ×1.00'de dengeli |
| A–H | Şehir | Kaynaklar sabit oranla akar |
| A–I | Battle | Nadir parça yalnız Hurdalık'tan; ondan önce istasyon tavanı 10 |

---

## Ölçüler tek bakışta

| Ne | Değer |
|---|---|
| Moral çarpanı | `0.55 + sevgi/100 × 0.75` → ×0.55 … ×1.30 |
| Nötr nokta | Sevgi 60 = ×1.00 |
| Psycho eşiği | Sevgi 25 |
| Moral düşüşü | Çalışan −6/sa · boşta −2/sa · battle −15 · çevrimdışı 4 sa tavan |
| Kantin rafı | 1 malzeme → +4 moral, tavan 60 |
| Yemekhane | 3 malzeme → +25 moral, tavan 100 |
| Yemekhane süresi | 60–90 sn |
| Sipariş | Aynı anda 1 aktif + 1 sıradaki |
| Oturum | Kısa 1–2 dk · orta 4–6 dk · uzun 8–12 dk · günde 2–3 |
| Çevrimdışı tavan | 4 saat |
| Faz 1 kapsamı | 1 bölge · 4 istasyon · 5 karakter · 2 hasar tipi |

---

## İlgili dokümanlar

| Ne için | Nereye |
|---|---|
| Üst düzey yapı, katman bağları, kapalı döngü denetimi | `OYUN-MIMARISI.md` |
| Bütün tasarım kuralları ve sayılar | `LUUPIE-SPEC.md` |
| Faz/efor/takvim, karar kapıları, Unity zemini | `URETIM-PLANI.md` |
| **Bu doküman** | Aynı işin **akışa göre** kesilmiş hâli |
