# Luupie — Oyun Mimarisi

**Üst düzey yapı kararı.** Üç katman, tek ekonomi.

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

## 2. Bağlantı ekonomisi

Kural: **her katman ana oyuna geri besler. Hiçbiri süs değildir.**

```
   YEMEKHANE ──── moral ────▶ ┌─────────────┐
   (aktif)                    │             │
                              │  TAMİRHANE  │──▶ SİPARİŞ ──▶ 🪙
   BATTLE ─── nadir parça ───▶│    (idle)   │                │
   (yan)                      │             │                │
                              └─────────────┘                ▼
   GENİŞLEME ◀──── plan ──────────────────────────────  yükseltme
   (yan)      yeni istasyon · yeni bölge
```

| Katman | Ana oyuna ne verir | Ana oyundan ne alır |
|---|---|---|
| Yemekhane | **Moral** → hat hızı çarpanı | Yemek malzemesi, işçi kadrosu |
| Battle | **Nadir parça** → üst seviye onarım | Savaşacak Luupie'ler, ekipman |
| Genişleme | **Yeni istasyon / bölge** | Plan (siparişten gelir) |

Bir katman kapatılsa oyun çalışır ama **daha yavaş** çalışır. Bağ budur.

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

| Hasar tipi | Ağır yük binen istasyon |
|---|---|
| Sökük dikiş | Onarım |
| Kırık mekanizma | Sökme + Onarım |
| Solmuş boya | Cila |
| Dağılmış dolgu | Teşhis + Onarım |

Yani **darboğaz gelen iş karışımına göre kayar.** Oyuncu sabit bir cevabı
ezberleyemez; her seansta hattı yeniden okur. Bu, düz üretim hattından daha
iyi bir idle döngüsü — optimizasyon hedefi hareketli.

### Kaynaklar

Ponchics'in üç kaynağı yedek parçaya eşlendi:

| Eski | Yeni | Nerede üretilir |
|---|---|---|
| Wool | 🧵 **Pamuk** (dolgu) | Genişleme — bölge binası |
| Oil | 🪡 **İplik** | Genişleme — bölge binası |
| Mine | ⚙️ **Parça** (mekanik) | Genişleme — bölge binası + **Battle** |

Depo dolunca durma, upgrade matrix, enerji/psycho ikili hızlanma, geri
dönüşüm, koleksiyon — hepsi `LUUPIE-SPEC.md`'deki gibi.

### Bozuk oyuncak akışı

Girdi üç yerden gelir ve bu, yan katmanları ana oyuna bağlayan ikinci damar:

| Kaynak | Ne getirir |
|---|---|
| Şehir teslimatı | Standart bozuk oyuncak akışı (sürekli) |
| **Battle sonrası** | Hasarlı düşman oyuncaklar — daha değerli, daha zor |
| Müşteri getirisi | Hikâye siparişleri, özel onarımlar |

---

## 4. Ara oyun — Yemekhane (aktif, 60–90 sn)

TM/Service katmanı. `KONSEPT-02-RESTORAN.md`'deki tasarım **kapsamı küçültülmüş
hâliyle** buraya oturur.

### Ne zaman açılır

- İşçilerin ortalama morali **%50 altına** düştüğünde (sahnede baloncuk)
- Vardiya sonunda oyuncu isterse
- Cooldown: 20 dakika

### Ne yapılır

Mutfak zinciri: **Doğra → Pişir → Tabakla**, dokunuşla ilerler.
Otonom garson yok — burada servis eden **oyuncunun kendisi**; işçiler masada
oturur ve bekler.

| | Kural |
|---|---|
| Süre | 60–90 sn |
| Müşteri | Kendi işçilerin — 4–8 Luupie |
| Sabır | Bekleyen işçinin morali **düşmeye devam eder** |
| Yanma | Fazla pişen yemek çöp olur (tek ceza) |
| Sonuç | Doğru beslenen her işçi **+25 moral**, tam servis **+%15 hat hızı · 30 dk** |

### Neden bu doğru bağ

Yemekhane oynamak = **hattı hızlandırmak**. Aktif oynanış doğrudan pasif
kazanca dönüşüyor; hybrid-casual'ın tam tanımı bu. Ve psycho'ya dönmüş bir
işçiyi geri kazanmanın en ucuz yolu da burası.

> Konsept 02'nin "otonom garsonlar çıldırır" fikri **ana oyuna taşındı**:
> tamirhanede işçiler zaten otonom ve psycho'ya dönüyor. Yemekhane, o sistemin
> **çözüm** tarafı oldu. İki doküman böylece çelişmiyor, birbirini tamamlıyor.

---

## 5. Yan oyun — Battle

Survivor/Arena katmanı. Konsept 03'ün (Fabrika Kuşatması) yan mod hâli.

| | Kural |
|---|---|
| Ne zaman | Ayrı sekme; günlük 3 giriş + etkinlik |
| Kim savaşır | Kadrondaki Luupie'ler — **aynı yatkınlık sistemi** |
| Kurgu | Vahşi psycho oyuncaklar tamirhaneyi basıyor |
| Süre | 90–120 sn dalga savunması |
| Ödül | ⚙️ **Parça** · nadir onarım bileşeni · hasarlı düşman oyuncak (girdi) |
| Risk | Kaybedersen ödül yok; kadro yaralanır (kısa süre çalışamaz) |

**Bağ:** Battle, ana oyunun en kıt kaynağını (mekanik parça) ve en değerli
girdisini (nadir bozuk oyuncak) üretir. Oynamayan oyuncu ilerler, oynayan
daha hızlı ilerler.

**Kapsam uyarısı:** Üç katmanın en pahalısı bu — yeni combat kodu, düşman
davranışı, dalga tasarımı, denge. §8'de en sona konmasının sebebi bu.

---

## 6. Yan oyun — Genişleme

Zaten tasarlanmış olan Şehir sistemi.

| | Kural |
|---|---|
| Ne yapılır | Bölge restorasyonu, kaynak binası kurma/yükseltme |
| Para birimi | **Plan** (siparişten gelir) |
| Çıktı | Yeni istasyon slotu · kaynak üretimi · yeni bozuk oyuncak akışı |
| Bölgeler | Repair Alley · Candy District · Psycho Lab · Shipping Bay · Clocktower |

Bölgeler seviye kapısıyla değil çok aşamalı projelerle açılır; her bölge
tamirhaneye **yeni bir kural** ekler (`LUUPIE-SPEC.md` §14).

---

## 7. Oturum modeli

Üç katman doğal olarak üç oturum uzunluğu üretiyor:

| Oturum | Süre | Ne yapılır |
|---|---|---|
| **Kısa** | 1–2 dk | Kasaları topla · darboğaza bak · yükselt · çık |
| **Orta** | 4–6 dk | + Yemekhane turu oyna (moral tazele) |
| **Uzun** | 8–12 dk | + Battle veya Genişleme |

Günde 2–3 oturum hedefi korunuyor. Kritik nokta: **kısa oturum tek başına
yeterli.** Ara ve yan oyunlar zorunlu değil, kârlı.

Geri dönme sebepleri: dolan kaynak deposu · biten sipariş · düşen moral ·
battle enerjisi dolması.

---

## 8. Kapsam ve aşamalı açılış

Üç katmanı aynı anda yapmak küçük ekip için gerçekçi değil. Sıra:

| Aşama | Ne yapılır | Neden bu sırada |
|---|---|---|
| **1** | **Tamirhane (idle)** tek başına oynanabilir | Ekonominin ve retansiyonun temeli; mevcut kodun çoğu burada |
| **2** | **Yemekhane** ara oyun | Moral sistemine bağlanır; TM anı reklam malzemesi olur |
| **3** | **Genişleme** | Şehir zaten tasarlı; kaynak üretimini açar |
| **4** | **Battle** | En pahalı, en az bağlı; ilk üçü tuttuktan sonra |

**Aşama 1 tek başına yayınlanabilir bir oyundur.** Diğer üçü onu
zenginleştirir, ayakta tutmaz.

---

## 9. Doküman haritası

| Katman | Hangi doküman |
|---|---|
| Ana oyun · Tamirhane | `LUUPIE-SPEC.md` — zincir, çarpan, ekonomi, ekran modeli aynen geçerli; istasyon isimleri bu dokümandaki gibi |
| Ara oyun · Yemekhane | `KONSEPT-02-RESTORAN.md` — mutfak zinciri ve TM mekanikleri; **kapsam §4'e göre küçültülür**, otonom garson bölümü ana oyuna taşındı |
| Yan oyun · Genişleme | `LUUPIE-SPEC.md` §14 |
| Yan oyun · Battle | Henüz spec yok — Aşama 4'te yazılacak |
| Üretim planı | `URETIM-PLANI.md` — faz tablosu bu mimariye göre güncellenecek |
| Test kayıtları | `TEST-RAPORU-01/02/03.md` |

---

## 10. Mevcut build'e etkisi

Yayındaki fabrika build'i **atılmıyor** — Tamirhane'nin iskeleti o.

| Mevcut | Yeni hâli | İş |
|---|---|---|
| PRESS · STITCH · PAINT · PACK | TEŞHİS · SÖKME · ONARIM · CİLA | Yeniden isimlendirme + ikon |
| Hammadde (sonsuz) | Bozuk oyuncak akışı | Girdi modeli değişir |
| Ürün → sipariş | Onarılmış → sipariş | Aynı |
| İşçi/moral/yatkınlık | Aynen | — |
| Darboğaz okuma | Aynen + **hareketli darboğaz** | Hasar tipi sistemi eklenir |
| Şehir | Genişleme | Aynen |
| Yemekhane mini oyunu | **Ara oyuna terfi** | Kapsam büyür |

Test raporlarındaki açık iş listesi (`LUUPIE-SPEC.md` §18) **geçerliliğini
koruyor** — 1 numaralı bloke madde hâlâ ilk iş.

---

## 11. Açık sorular

1. **Hasar tipi sayısı:** başlangıçta 4 mü, 2 mi? (Öneri: 2 — FTUE'de hareketli
   darboğaz kavramı tek seferde öğretilmez)
2. **Yemekhane zorunlu mu:** moral %50 altına inince oyun onu dayatsın mı,
   yoksa sadece önersin mi? (Öneri: önersin — dayatma idle'ın ruhunu bozar)
3. **Battle kadrosu ayrı mı:** savaşan Luupie o sırada hatta çalışamıyor mu?
   (Öneri: evet — gerçek bir kadro kararı doğurur)
4. **Aşama 1 yayın kapsamı:** kaç bölge, kaç istasyon, kaç karakter?
   (Öneri: 1 bölge, 4 istasyon, 5 karakter)
