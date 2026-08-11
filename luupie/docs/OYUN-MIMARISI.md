# Luupie — Oyun Mimarisi

**Üst düzey yapı kararı.** Üç katman, tek ekonomi, **açık uç yok**.

```
        ANA OYUN                ARA OYUN              YAN OYUNLAR
   ┌──────────────────┐   ┌────────────────┐   ┌──────────────────────┐
   │   TAMİRHANE      │   │   YEMEKHANE    │   │  BATTLE · GENİŞLEME  │
   │   idle · sürekli │   │  aktif · 60-90 │   │  seansa özel         │
   └──────────────────┘   └────────────────┘   └──────────────────────┘
```

---

## 1. Neden bu yapı

Pazarlama panosunun tür tablosu iki şeyi aynı anda söylüyordu:

| Tür | Güçlü olduğu yer |
|---|---|
| **Idle** | Retansiyon ★★★★★ · Monetizasyon ★★★★★ |
| **Time-Management / Service** | Pazarlama ★★★★★ · Karakter uyumu ★★★★★ |
| **Survivor / Arena** | Pazarlama ★★★★★ · Prototip hızı ★★★★☆ |

Tek tür seçmek, o türün zayıf sütununu kabul etmek demekti. Üç katmanlı yapı
**her türü güçlü olduğu yerde kullanıyor:**

- **Idle** uzun vadeli tutmayı ve geliri taşır → ana oyun
- **TM** karakter ve pazarlamayı taşır → ara oyun, reklamda gösterilecek an
- **Survivor** çeşitliliği ve etkinlik hacmini taşır → yan oyun

---

## 2. Tek büyük halka

Kural: **her katman bir sonrakini besler ve halka başa döner. Hiçbir katman
kendi başına duran bir ödül dağıtıcısı değildir.**

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
   GENİŞLEME ──🥕 malzeme──▶ YEMEKHANE ──💛 moral──▶ TAMİRHANE ─┘
       ▲                          ▲                     │
       │                          │                     ▼
       │                     −15 moral              SİPARİŞ
       │                          │                  │     │
       │                       BATTLE ◀──🧸 ekipman───┘     │
       │                          │                        │
       │                     ⚙️ nadir parça                │
       │                          │                        │
       └────────── 📋 plan ◀──────┴────────────────────────┘
```

Okunuşu tek cümlede: **sipariş parayı ve planı verir → plan şehri büyütür →
şehir malzeme üretir → malzeme yemekhaneyi çalıştırır → yemekhane morali
yükseltir → moral hattı hızlandırır → hat daha çok sipariş çıkarır.**
Battle bu halkanın hızlandırıcı kolu: hattın ürününü rehin alır, karşılığında
hattın en kıt girdisini verir ve kadronun moralini düşürerek halkayı yeniden
başlatır.

| Katman | Ne tüketir | Ne üretir | Kapısı |
|---|---|---|---|
| **Tamirhane** | Bozuk oyuncak · pamuk/iplik/parça · moral | Onarılmış oyuncak → 🪙 coin + 📋 plan | Yok — sürekli |
| **Yemekhane** | 🥕 Malzeme + oyuncunun dikkati | 💛 Moral (60 üstü tek yol) | Malzeme deposu |
| **Battle** | 🧸 Onarılmış oyuncak (kilitlenir) + kadro morali | ⚙️ Nadir parça + hasarlı düşman oyuncak | Günlük giriş + kadro |
| **Genişleme** | 📋 Plan | İstasyon slotu · kaynak binası · 🥕 malzeme · yeni hasar tipi | Plan |

---

## 3. Ana oyun — Tamirhane (idle)

> Bozuk oyuncaklar gelir, hattan geçer, onarılmış çıkar, sevk edilir.

Fabrika hattının **doğrudan devamı** — istasyonlar yeniden isimlendirildi,
mekanik aynı. `LUUPIE-SPEC.md`'deki üretim zinciri, çarpan formülü, tampon
kuralı, darboğaz görsel dili ve ekonomi **aynen geçerli**.

### Zincir

```
 BOZUK OYUNCAK ─▶ TEŞHİS ─▪─ SÖKME ─▓▓─ ONARIM ─── CİLA ─▶ ONARILMIŞ ─▶ SEVK
                                        ▲
                                    DARBOĞAZ
```

### Fabrikadan tek gerçek fark — ve bu bir kazanç

Fabrikada her ürün aynıydı; darboğaz sabitti. Tamirhanede **her bozuk oyuncak
farklı hasarlı gelir:**

| Hasar tipi | Ağır yük binen istasyon | Ne zaman açılır |
|---|---|---|
| Sökük dikiş | Onarım | Başlangıç |
| Solmuş boya | Cila | Başlangıç |
| Kırık mekanizma | Sökme + Onarım | Bölge 2 |
| Dağılmış dolgu | Teşhis + Onarım | Bölge 3 |

Yani **darboğaz gelen iş karışımına göre kayar.** Oyuncu sabit bir cevabı
ezberleyemez; her seansta hattı yeniden okur. Bu, düz üretim hattından daha
iyi bir idle döngüsü — optimizasyon hedefi hareketli.

> **Karar (eski açık soru 1):** Başlangıçta **2 hasar tipi**. FTUE'de hareketli
> darboğaz kavramı tek seferde öğretilmez; 3. ve 4. tip bölge açılışlarıyla
> gelir ve her biri hattın okunuşunu bir kez daha tazeler.

### Kaynaklar

Ponchics'in üç kaynağı yedek parçaya eşlendi, dördüncüsü yemekhane için eklendi:

| Kaynak | Nerede üretilir | Kime gider |
|---|---|---|
| 🧵 **Pamuk** (dolgu) | Genişleme — Pamuk Tarlası | Hat istasyonları |
| 🪡 **İplik** | Genişleme — İplikhane | Hat istasyonları |
| ⚙️ **Parça** (mekanik) | Genişleme — Parça Atölyesi | Hat istasyonları |
| 🥕 **Malzeme** (yiyecek) | Genişleme — **Mutfak Serası** | **Yemekhane + kantin rafı** |
| ⚙️✨ **Nadir parça** | **Battle** · Hurdalık (çok yavaş) | İstasyon seviye 10+ |

Depo dolunca durma, upgrade matrix, enerji/psycho ikili hızlanma, geri
dönüşüm, koleksiyon — hepsi `LUUPIE-SPEC.md`'deki gibi.

### Bozuk oyuncak akışı

Girdi üç yerden gelir ve bu, yan katmanları ana oyuna bağlayan ikinci damar:

| Kaynak | Ne getirir |
|---|---|
| Şehir teslimatı | Standart bozuk oyuncak akışı (sürekli) |
| **Battle sonrası** | Hasarlı düşman oyuncaklar — daha değerli, daha zor |
| **Battle kaybı** | Kırılan ekipman oyuncağın kendisi — kayıp değil, gecikme |
| Müşteri getirisi | Hikâye siparişleri, özel onarımlar |

---

## 4. Ara oyun — Yemekhane (aktif, 60–90 sn)

TM/Service katmanı. Burası mimarinin en kolay **açık uç** verecek yeriydi —
"oyna, buff al" bir döngü değil, bir hediye dağıtıcısıdır. Aşağıdaki dört
kural onu kapatıyor.

### Kural 1 — Yemekhane'nin **tek** çıktısı moraldir

Ayrı bir "+%15 hat hızı" bonusu **yoktur ve olmayacak**. Moral zaten çarpan
formülünün içinde:

```
İşçi × Yatkınlık × Moral × Hızlanma
Moral çarpanı = 0.55 + sevgi/100 × 0.75      → ×0.55 ... ×1.30
```

İkinci bir hız kanalı açmak, aynı şeyi iki yerden ölçmek olurdu. Tek kanal:
**moral.** Yemekhane onu yükseltir, başka hiçbir şey yapmaz.

### Kural 2 — Nötr nokta 60, üstüne çıkmanın tek yolu aktif oynamak

Formülün kendi matematiği kapıyı zaten çizmiş:

| Sevgi | Çarpan | Anlamı |
|---|---|---|
| 0 | ×0.55 | Hat sürünüyor |
| 25 | ×0.74 | **Psycho eşiği** |
| **60** | **×1.00** | **Nötr — bedava tavan** |
| 100 | ×1.30 | Tam performans |

**Kantin rafı (pasif):** İşçi 60'ın altına düşerse arka planda kuru yemek
yer. Malzeme harcar, **tavanı 60'tır**. Yani oyuncu hiç yemekhane oynamazsa
hattı ×1.00'de tutar — ceza yok, ama üstü de yok.

**Yemekhane (aktif):** 60 ile 100 arasındaki **%30'luk hız bandı yalnızca
buradan alınır.**

### Kural 3 — Aktif oynamak resmen 2 kat verimlidir

Aynı kaynağı iki farklı verimle harcıyorsun; karar buradan doğuyor:

| Yol | Malzeme | Kazanç | Verim | Tavan |
|---|---|---|---|---|
| 🥫 Kantin rafı (pasif) | 1 | +4 moral | **4 moral/malzeme** | 60 |
| 🍲 Yemekhane (aktif) | 3 | +25 moral | **8.3 moral/malzeme** | 100 |

Hybrid-casual'ın tam tanımı bu: **aktif oynanış, kıt bir kaynağın üzerinde bir
verim çarpanıdır** — bedava güç değil.

### Kural 4 — Kapı zamanlayıcı değil, kaynaktır

Keyfi "20 dakika cooldown" **kaldırıldı**. Cooldown açık uçtur: neden 20?
Yemekhane'yi ne sınırlarsa o gerçek kapıdır ve o **malzeme deposudur**.

| | Değer |
|---|---|
| Mutfak Serası (Sv. 1) | 30 🥕 / saat · depo 60 |
| Bir tam servis (8 işçi) | 24 🥕 |
| Kantin rafı yükü | Sevgi < 60 olan **her işçi** için 12 🥕/saat |

Sonuçlar kendiliğinden doğuyor:

- Kadro büyüdükçe pasif tüketim artar → **Sera yükseltmesi zorunlu hale gelir**
  (Genişleme'ye gerçek bir talep)
- Gece boyu kadroyu hatta bırakırsan sabah depo boş → **yemek pişiremezsin**
- Yemekhane oynayıp herkesi 100'e çıkarırsan kantin rafı **hiç tüketmez**
  (kimse 60 altında değil) → aktif oyun pasif tüketimi de düşürür

> **Karar (eski açık soru 2):** Oyun yemekhaneyi **dayatmaz**. Moral ortalaması
> %50 altına inince sahnede baloncuk çıkar, o kadar. Dayatma idle'ın ruhunu
> bozar; zaten kaynak kapısı ve %30'luk hız bandı yeterli sebep.

### Ne oynanır

Mutfak zinciri: **Doğra → Pişir → Tabakla**, dokunuşla ilerler.
Otonom garson yok — burada servis eden **oyuncunun kendisi**; işçiler masada
oturur ve bekler.

| | Kural |
|---|---|
| Süre | 60–90 sn |
| Müşteri | Kendi işçilerin — 4–8 Luupie |
| Sabır | Bekleyen işçinin morali **düşmeye devam eder** |
| Yanma | Fazla pişen yemek çöp olur — **malzeme yanar** (tek ceza, ve gerçek) |
| Açılış | Sahneden: aç işçinin baloncuğu · vardiya sonu kartı |

Yanma cezasının bir bedeli olması da bu yapı sayesinde: eskiden "yemek çöp
olur" soyut bir cezaydı, şimdi **3 malzeme yanar** — yani Sera'da 6 dakikalık
üretim.

> Konsept 02'nin "otonom garsonlar çıldırır" fikri **ana oyuna taşındı**:
> tamirhanede işçiler zaten otonom ve psycho'ya dönüyor. Yemekhane, o sistemin
> **çözüm** tarafı oldu. İki doküman böylece çelişmiyor, birbirini tamamlıyor.

### Moral nereden düşer

Döngünün kapanması için morali *tüketen* tarafın da tanımlı olması gerekiyor:

| Sebep | Hız |
|---|---|
| Hatta çalışmak | −6 sevgi / saat |
| Boşta beklemek | −2 sevgi / saat |
| Battle'a girmek | −15 sevgi (anlık) |
| Yemekhane'de aç bekletilmek | −1 sevgi / 10 sn |
| Çevrimdışı | Aynı hız, **4 saat tavanla** |

**Moral, üretimin işletme gideridir.** Hattı ne kadar çok çalıştırırsan o
kadar hızlı tükenir. Bedava değil, ve bu yüzden döngü kapalı.

---

## 5. Yan oyun — Battle

Survivor/Arena katmanı. Konsept 03'ün (Fabrika Kuşatması) yan mod hâli.

| | Kural |
|---|---|
| Ne zaman | Ayrı sekme; günlük 3 giriş + etkinlik |
| Kim savaşır | Kadrondaki Luupie'ler — **aynı yatkınlık sistemi** |
| **Giriş bedeli** | Her savaşçıya ekipman olarak **1 onarılmış oyuncak** |
| Kurgu | Vahşi psycho oyuncaklar tamirhaneyi basıyor |
| Süre | 90–120 sn dalga savunması |
| Ödül | ⚙️✨ **Nadir parça** · hasarlı düşman oyuncak (hatta girdi) |
| Kayıp bedeli | Ekipman oyuncağı **kırılır** → hatta bozuk oyuncak olarak döner |
| Her durumda | Kadro **−15 moral** |

### Battle nasıl bağlandı

Üç ayrı damarla, hiçbiri süs değil:

1. **Ürün rehini.** Savaşa soktuğun onarılmış oyuncak, o sırada **siparişe
   koyulamaz**. Battle, hattın çıktısı için siparişle *yarışır*. Gerçek bir
   fırsat maliyeti.
2. **Moral gideri.** Savaşan kadro −15 moral ile döner → doğrudan Yemekhane'ye
   talep yaratır. Battle oynayan oyuncu yemekhane oynamak zorunda kalır.
3. **Tek hızlı nadir parça yolu.** İstasyonların **10. seviye üstü**
   yükseltmesi nadir parça ister. Battle bunu hızlı verir.

### Oynamayan oyuncu ne kaybeder

**Hiçbir şey — sadece zaman.** Nadir parça, Genişleme'deki **Hurdalık**
binasından da gelir: *1 adet / 6 saat*. Yani battle bir duvar değil,
bir kısayol. Tavan aynı, hız farklı.

> **Karar (eski açık soru 3):** Savaşan Luupie o sırada **hatta çalışamaz.**
> Kadro kararı gerçek olsun diye: en iyi işçini savaşa sokmak hattı yavaşlatır.
> Savaş 90–120 sn sürer, dönüş sonrası 0 bekleme — ceza süre değil, moral.

**Kapsam uyarısı:** Üç katmanın en pahalısı bu — yeni combat kodu, düşman
davranışı, dalga tasarımı, denge. §8'de en sona konmasının sebebi bu.

---

## 6. Yan oyun — Genişleme

Zaten tasarlanmış olan Şehir sistemi. Halkanın **kaynak ucu**: diğer üç
katmanın tükettiği her şey burada üretilir.

| | Kural |
|---|---|
| Ne yapılır | Bölge restorasyonu, kaynak binası kurma/yükseltme |
| Para birimi | **📋 Plan** (siparişten gelir) |
| Bölgeler | Repair Alley · Candy District · Psycho Lab · Shipping Bay · Clocktower |

| Bina | Üretir | Kimi besler |
|---|---|---|
| Pamuk Tarlası | 🧵 Pamuk | Hat |
| İplikhane | 🪡 İplik | Hat |
| Parça Atölyesi | ⚙️ Parça | Hat |
| **Mutfak Serası** | 🥕 Malzeme | **Yemekhane + kantin rafı** |
| **Hurdalık** | ⚙️✨ Nadir parça (1 / 6 sa) | İstasyon Sv. 10+ |

Bölgeler seviye kapısıyla değil çok aşamalı projelerle açılır; her bölge
tamirhaneye **yeni bir kural** ekler (`LUUPIE-SPEC.md` §14) — 3. ve 4. hasar
tipi de buradan gelir.

---

## 7. Kapalı döngü denetimi

Her katman için dört soru. Hiçbirinde boşluk kalmamalı.

| Katman | Girdisi nereden | Çıktısı nereye | Neyle sınırlı | Hiç oynanmazsa |
|---|---|---|---|---|
| **Tamirhane** | Şehir + Battle (bozuk oyuncak) · Genişleme (kaynak) · Yemekhane (moral) | Sipariş → 🪙 + 📋 | Darboğaz · tampon · kaynak | Oyun yok — bu ana oyun |
| **Yemekhane** | Genişleme (🥕) | Moral 60→100 | **Malzeme deposu** | Hat ×1.00'de kalır, %30 bant kapalı |
| **Battle** | Tamirhane (🧸 ekipman) · kadro | ⚙️✨ + hasarlı oyuncak | Günlük 3 · kadro · ürün | Nadir parça 6 saatte 1 gelir, tavan aynı |
| **Genişleme** | Tamirhane (📋 plan) | Tüm kaynaklar + slot + hasar tipi | Plan · aşama sayısı | Kaynak tavana takılır, hat büyüyemez |

**Denetim sonucu:** Hiçbir katman bedava çıktı vermiyor, hiçbir kaynağın tek
bir tüketicisi yok, hiçbir katman zorunlu değil ama hepsi kârlı. Bir katmanı
kapatırsan oyun çalışır — **daha yavaş** çalışır. Aranan tam olarak buydu.

### Yanlış olabilecek üç yer — ve panzehirleri

| Risk | Belirti | Panzehir |
|---|---|---|
| Malzeme bollaşır | Yemekhane bedava buff'a döner | Sera üretimi kadro büyümesinden **yavaş** ölçeklenir |
| Nadir parça darboğazı | Battle fiilen zorunlu olur | Hurdalık hızı telemetriyle ayarlanır; hedef: battle **2× hızlandırsın**, kilitlemesin |
| Moral hep 100 | Çarpan sabite döner, karar ölür | Çalışma gideri (−6/sa) kadro büyüdükçe toplamda artar; tek seansta herkesi 100 yapmak malzeme yetmez |

---

## 8. Oturum modeli

Üç katman doğal olarak üç oturum uzunluğu üretiyor:

| Oturum | Süre | Ne yapılır |
|---|---|---|
| **Kısa** | 1–2 dk | Kasaları topla · darboğaza bak · yükselt · çık |
| **Orta** | 4–6 dk | + Yemekhane turu oyna (moral tazele) |
| **Uzun** | 8–12 dk | + Battle veya Genişleme |

Günde 2–3 oturum hedefi korunuyor. Kritik nokta: **kısa oturum tek başına
yeterli.** Ara ve yan oyunlar zorunlu değil, kârlı.

Geri dönme sebepleri: dolan kaynak deposu · biten sipariş · **düşen moral** ·
dolan Sera · battle enerjisi.

---

## 9. Kapsam ve aşamalı açılış

Üç katmanı aynı anda yapmak küçük ekip için gerçekçi değil. Sıra:

| Aşama | Ne yapılır | Neden bu sırada |
|---|---|---|
| **1** | **Tamirhane (idle)** tek başına oynanabilir | Ekonominin ve retansiyonun temeli; mevcut kodun çoğu burada |
| **2** | **Yemekhane** ara oyun | Moral bandını açar; TM anı reklam malzemesi olur |
| **3** | **Genişleme** | Kaynak üretimini ve hasar tiplerini açar |
| **4** | **Battle** | En pahalı, en az bağlı; ilk üçü tuttuktan sonra |

**Aşama 1 tek başına yayınlanabilir bir oyundur.** Diğer üçü onu
zenginleştirir, ayakta tutmaz.

> **Sıra ile döngü çelişmiyor mu?** Hayır. Aşama 1'de Sera ve kantin rafı
> **sabit değerlerle** çalışır (Sera yok, malzeme sabit oranla akar). Aşama 3
> gelince o sabit, gerçek binaya devredilir. Her aşamada halka kapalı kalır,
> sadece halkanın bir parçası geçici olarak "otomatik" olur.

> **Karar (eski açık soru 4):** Aşama 1 yayın kapsamı — **1 bölge · 4 istasyon
> · 5 karakter · 2 hasar tipi.** Sanat yükünün en dar boğaz olduğu tespiti
> (`URETIM-PLANI.md` §7) bu sayıyı belirledi.

---

## 10. Doküman haritası

| Katman | Hangi doküman |
|---|---|
| Ana oyun · Tamirhane | `LUUPIE-SPEC.md` — zincir, çarpan, ekonomi, ekran modeli aynen geçerli; istasyon isimleri bu dokümandaki gibi |
| Ara oyun · Yemekhane | Bağlanma kuralları **burada §4**; mutfak zinciri ve TM mekanikleri `KONSEPT-02-RESTORAN.md` |
| Yan oyun · Genişleme | `LUUPIE-SPEC.md` §14 + bu doküman §6 |
| Yan oyun · Battle | Bağlanma kuralları **burada §5**; combat spec'i Faz 4'te |
| Üretim planı (faz/efor) | `URETIM-PLANI.md` — faz haritası bu mimariye göre yazılmıştır |
| **İşleyiş planı (davranış)** | `ISLEYIS-PLANI.md` — A–J blokları, her birinin kabul testi |
| Test kayıtları | `TEST-RAPORU-01/02/03.md` |

---

## 11. Mevcut build'e etkisi

Yayındaki fabrika build'i **atılmıyor** — Tamirhane'nin iskeleti o.

| Mevcut | Yeni hâli | İş |
|---|---|---|
| PRESS · STITCH · PAINT · PACK | TEŞHİS · SÖKME · ONARIM · CİLA | Yeniden isimlendirme + ikon |
| Hammadde (sonsuz) | Bozuk oyuncak akışı | Girdi modeli değişir |
| Ürün → sipariş | Onarılmış → sipariş | Aynı |
| İşçi/yatkınlık | Aynen | — |
| **Moral** | **Tek hız kanalı + işletme gideri** | Düşüş hızları, kantin rafı, 60 tavanı eklenir |
| **Yemekhane mini oyunu** | **Ara oyuna terfi** | Malzeme ekonomisi + 60→100 bandı |
| Darboğaz okuma | Aynen + **hareketli darboğaz** | Hasar tipi sistemi eklenir |
| Şehir | Genişleme | + Mutfak Serası, + Hurdalık |

Test raporlarındaki açık iş listesi (`LUUPIE-SPEC.md` §18) **geçerliliğini
koruyor** — 1 numaralı bloke madde hâlâ ilk iş.

---

## 12. Karar kaydı

Dört açık soru bu revizyonda kapatıldı:

| # | Soru | Karar | Gerekçe |
|---|---|---|---|
| 1 | Hasar tipi sayısı | **2** ile başla, 3–4 bölge açılışıyla | FTUE'de hareketli darboğaz tek seferde öğretilmez |
| 2 | Yemekhane zorunlu mu | **Hayır** — sadece baloncuk | Dayatma idle'ın ruhunu bozar; kaynak kapısı yeterli |
| 3 | Battle kadrosu ayrı mı | **Evet** — savaşan hatta çalışmaz | Gerçek kadro kararı doğurur |
| 4 | Aşama 1 kapsamı | 1 bölge · 4 istasyon · 5 karakter | Sanat yükü dar boğaz |

| 5 | Motor | **Full Unity** — baştan sona, ara geçiş yok | Faz 4 combat ve mağaza dağıtımı; motor geçişi riski sıfırlanır |

Teknik zemin `URETIM-PLANI.md` §9'da: 10 Hz simülasyon tick'i, ScriptableObject
veri katmanı, sahte izometri, kayıt/çevrimdışı sözleşmesi. Web prototipi ürün
değil — şartname referansı, yaratıcı test malzemesi ve oynanabilir demo olarak
kalıyor.
