# Luupie — 4 Fazlık Plan

Tek sayfalık çalışma planı. Ayrıntı için: mimari `OYUN-MIMARISI.md` ·
tasarım `LUUPIE-SPEC.md` · akış `ISLEYIS-PLANI.md` · efor `URETIM-PLANI.md`.

**Motor: full Unity.** **Yön: yatay.** **Ana oyun: Tamirhane (idle).**

---

## Halka

```
GENİŞLEME ─🥕─▶ YEMEKHANE ─💛─▶ TAMİRHANE ─▶ SİPARİŞ ─📋─▶ GENİŞLEME
                     ▲                          │
                     └──── −15 moral ── BATTLE ◀┘ 🧸 ekipman rehin
```

Sipariş parayı ve planı verir → plan şehri büyütür → şehir malzeme üretir →
malzeme yemekhaneyi çalıştırır → yemekhane morali yükseltir → moral hattı
hızlandırır → hat daha çok sipariş çıkarır.

---

## Değişmez kurallar

1. **Bilgi sahnede, karar panelde.** Hiçbir fabrika durumu, sahnede
   görünmeden panelde sayı olarak gösterilmez.
2. **Tek hız kanalı: moral.** İkinci bir "hız bonusu" hiçbir yerden eklenmez.
3. **Yaşam alanına arayüz giremez.** Butonlar okunabilecek kadar büyük,
   karakter alanına değmez.
4. **Her faz sonunda oyun oynanır durumda.** Gelmemiş sistemin yerine sabit
   değerli vekil durur.
5. **Reklam moral satmaz.** %30'luk hız bandı yalnızca oynanarak kazanılır.
6. **Denge sayıları koda yazılmaz** — hepsi veri dosyasında yaşar.

---

# FAZ 1 · TAMİRHANE

**8–9 hafta · ~17.5 adam-hafta kod · ~7.5 sanat**
**Akış blokları: A Akış → B Tıkanma → C Okuma → D Müdahale → E Karşılık →
F Yıpranma → G Dönüş**

> **Tek soru:** Oyuncu hattaki darboğazı gözle bulup düzeltebiliyor ve buna
> geri dönüyor mu?

Yemekhane yok, şehir yok, battle yok. Kaynaklar sabit oranla akar, kantin rafı
morali 60'ta tutar — hat ×1.00'de dengeli çalışır.

### 1.0 Zemin *(2 hafta)*

- Unity projesi, sürüm kilidi, repo + LFS
- **Tek `Simulate()` fonksiyonu, 10 Hz** — canlı oyun ve çevrimdışı dönüş
  aynı kod yolundan geçer, başka hiçbir yerde üretim hesabı yapılmaz
- Bütün denge sayıları veri dosyasında (kodda sabit sayı yok)
- İzometrik sahne: kamera, sıralama, güvenli alan
- Sprite atlası + mevcut karakterlerin içe aktarımı
- Kayıt/yükleme + çevrimdışı ileri sarma (tavan 4 saat)
- **Kabul:** uygulamayı kapat, saati 3 saat ileri al, aç — sonuç canlı
  koşturmayla birebir aynı

### 1.1 Hat akar *(A)*

- Kapıdan bozuk oyuncak girer, banda düşer
- Dört istasyon: TEŞHİS · SÖKME · ONARIM · CİLA
- **İstasyon süreleri baştan farklı** — eşitse hat hiç tıkanmaz ve B test
  edilemez
- Sağ uçtan onarılmış oyuncak çıkar
- **Kabul:** 60 sn izle, dokunma, soldan gireni sağdan çıkarken takip et

### 1.2 Hat tıkanır *(B)*

- İstasyonlar arası tampon, üst sınırlı
- **Tamponu dolan istasyon durur** (yavaşlamaz, durur) · boş kalan aç kalır
- Sevk edilmezse çıktı dolar, zincir geriye kilitlenir
- **2 hasar tipi:** sökük dikiş → ONARIM'ı yorar · solmuş boya → CİLA'yı yorar
- **Kabul:** 3 dk izle, hat kilitlensin. Hasar karışımını değiştir —
  **darboğaz başka istasyona geçmeli**

### 1.3 Tıkanma okunur *(C)*

- Tampon yığını fiziksel görünür (3 kutu ≠ 30 kutu)
- Bant yoğunluğu: tıkanan tarafta sık, aç tarafta seyrek
- İşçi davranışı: yetişemeyen panik · aç kalan esniyor · işsiz cebinde eller
- `⛔` tıkalı · `👤?` işçisiz baloncuğu, aynı anda en fazla 2
- Hiçbir durum yalnızca renkle anlatılmaz
- **Kabul:** görüntüyü al, arayüzü kırp — kalan görüntü darboğazı anlatmalı.
  Oyunu görmemiş biri 30 sn'de doğru istasyonu göstermeli

### 1.4 Oyuncu müdahale eder *(D)*

- İstasyona dokun → panel (%66 × %90, arkada sahne görünür)
- İşçi atama · yükseltme (`3.9 → 3.3 sn · +%18` satın almadan önce yazar)
- Çarpan **ayrı ayrı**: işçi × yatkınlık × moral × hızlanma
- **Dönüş deltası zorunlu:** panel makineye doğru kapanır → parlama →
  delta çipi → bant rampayla hızlanır → **tampon gözle erir**
- Öneri motoru hat hızına en çok katkıyı başa koyar (işçi yoksa "ata",
  "yükselt" değil)
- **Kabul:** panel kapandıktan sonraki 1 sn içinde, panele bakmadan
  değişimi gör

### 1.5 Karşılığı gelir *(E)*

- Sipariş: 1 aktif + 1 sıradaki, üçüncüsü yok
- **Sevkiyat hattı açan zorunlu eylem** — sevk etmezsen hat kilitlenir
- Kutlama: kamyon → yükleme → para uçuşu → sayaç → işçiler el sallar
- **Sipariş düğmesi hiçbir şeyin altında kalmaz** *(prototipteki oyunu
  45 sn'de kilitleyen hata)*
- Birleştirme: 3 aynı / 5 karışık → üst seviye, maks L3
- Sipariş sınıfları: standart · kaliteli +%33 · butik +%53 · acele +%81
- Kaynak maliyeti, enerji overdrive, geri dönüşüm tezgahı
- **Kabul:** darboğazı bul → ata → hızlan → sipariş dolsun → sevk et →
  parayı bir sonraki darboğaza yatır

### 1.6 İşçiler yıpranır *(F)*

- Moral düşüşü: çalışan −6/sa · boşta −2/sa · çevrimdışı 4 sa tavanla
- Çarpan: `0.55 + sevgi/100 × 0.75`
- **Kantin rafı:** 1 malzeme → +4 moral, **tavan 60** (= ×1.00 nötr)
- **Psycho:** moral 25 altında → ×2 hız ama %18 hatalı, paketlemeyi tıkar
- Üç çıkış: besle · zapt et · bırak çalışsın
- **Kabul:** hattı mükemmel kur, 4 saat bırak. Dön — hat daha yavaş, ve
  nedenini işçilerin yüzünden anla

### 1.7 Dönüş anlamlı olur *(G)*

- Dönüş sahnesi: kamyon girer, kasalar yığılır, dokununca patlar — modal yok
- Vardiya raporu kart, ekranı kaplamaz
- **İlk 10 dakika:** 0:30 bir istasyon yavaşlar → 1:30 ilk atama, ilk
  "ben yaptım" → 3:00 ilk sipariş → 5:00 kontrollü arıza → 7:00 ilk sevkiyat
- İlk 5 dk'da görünmez: kozmetik · lig · albüm · koleksiyon · geri dönüşüm
- **Kabul:** 3 saat sonra aç — ne olduğunu kimse yazmadan sahneden anla

### 🚦 KAPI 1

| Ölçüt | Eşik |
|---|---|
| 30 saniye testi | Doğru istasyonu gösteren ≥ %70 |
| İç test | ≥ 8 kişi × 3 oturum |
| Hatırlatmasız 2. oturum | ≥ %50 |
| Hareketli darboğaz | Oyuncu hasar tipine göre atamayı değiştiriyor |
| Performans | Hedef cihazda 60 fps |
| Çevrimdışı tutarlılığı | 4 saatlik dönüş = canlı koşturma |
| Çalışma hatası | 0 |

**Geçemezse:** görsel dil mi zayıf, mekanik mi sığ — ayırt et. İkincisiyse
Yemekhane'yi çekirdeğe terfi ettirmek yedek plan.

**Bu fazın sonunda oyun tek başına yayınlanabilir.**
Kapsam: 1 bölge · 4 istasyon · 5 karakter · 2 hasar tipi.

---

# FAZ 2 · YEMEKHANE

**2–3 hafta · ~6 adam-hafta kod · ~3 sanat**
**Akış bloğu: H Besleme**

> **Tek soru:** Aktif oynanış pasif kazanca dönüşünce oyuncu daha çok kalıyor mu?

Faz 1'de kantin rafı morali 60'ta tutuyordu. Bu faz **60–100 bandını** açar —
oyunun tek gerçek aktif oynanış sebebi.

### Ne yapılır

- Malzeme kaynağı + deposu — **tek kapı bu, zamanlayıcı cooldown yok**
- Mutfak zinciri: doğra → pişir → tabakla, dokunuşla, 60–90 sn
- Yanma: fazla pişen çöp olur → **3 malzeme yanar** (gerçek bedel)
- Masadaki işçinin sabrı: beklerken morali düşmeye devam eder
- Servis → **+25 moral, tavan 100**
- Giriş yalnızca sahneden: aç işçi baloncuğu · vardiya sonu kartı
- Psycho'dan çıkışın en ucuz yolu buraya bağlanır

### Neden döngü, hediye değil

| Yol | Malzeme | Kazanç | Verim | Tavan |
|---|---|---|---|---|
| Kantin rafı (pasif) | 1 | +4 | 4 moral/🥕 | 60 → ×1.00 |
| **Yemekhane (aktif)** | 3 | +25 | **8.3 moral/🥕** | 100 → ×1.30 |

Aktif oynamak = aynı kaynağı **2 kat verimli** harcamak. Bedava güç değil.

### 🚦 KAPI 2

| Ölçüt | Eşik |
|---|---|
| D1 / D7 retansiyon | ≥ %35 / ≥ %12 |
| Oturum/gün | ≥ 2 |
| **Yemekhane oynayan ÷ oynamayan D7** | **≥ 1.4×** |
| Ortalama moral | 65–85 (100'e yapışmıyor) |

Kalın satır bu fazın varlık sebebi. 1.4× çıkmazsa yemekhane bir zaman
hırsızıdır — mekanik değil, bağ yanlıştır.

---

# FAZ 3 · GENİŞLEME

**3–4 hafta · ~8 adam-hafta kod · ~4 sanat**
**Akış bloğu: I Büyüme**

> **Tek soru:** Ekonomi 14 gün boyunca tavana vurmadan ve tıkanmadan ilerliyor mu?

Faz 1–2'nin sabit oranlı kaynak vekilleri burada **gerçek binalara** devredilir.

### Ne yapılır

- Şehir sahnesi + **📋 plan** para birimi (siparişten gelir)
- Kaynak binaları: Pamuk Tarlası · İplikhane · Parça Atölyesi
- **Depo kuralı:** bina depo dolana kadar üretir, **sonra durur** —
  oyuncu toplayana kadar kaynak fabrikaya gitmez
- **Mutfak Serası** — Faz 2'nin sabit malzeme akışını devralır
- **Hurdalık** — nadir parça, 6 saatte 1
- İstasyon Seviye 10 üstü nadir parça ister
- Bölge restorasyonu: çok aşamalı proje, **inşaat hâli binanın kendisinde
  görünür** (ilerleme çubuğu değil)
- **3. ve 4. hasar tipi** bölge açılışıyla — darboğaz okuması tazelenir
- Yeni istasyon slotu (hat **uzar**, katlanmaz)
- Koleksiyon atölyesi — ekonominin nihai sink'i

### 🚦 KAPI 3

| Ölçüt | Eşik |
|---|---|
| 14 günlük ilerleme | Tavana vurma yok, tıkanma yok |
| Kaynak dengesi | Hiçbiri sürekli tavanda / sürekli sıfırda değil |
| Bölge temposu | Hedeflerin ±%30'u |
| D14 retansiyon | ≥ %6 |
| Enflasyon | Koleksiyon sink'i fazlayı soğuruyor |

14 günü **oynamadan önce hesap tablosunda** simüle et, sonra oynayarak doğrula.

---

# FAZ 4 · BATTLE + LANSMAN

**8–11 hafta · ~18 adam-hafta kod · ~4.5 sanat**
**Akış bloğu: J Baskın**

> **Tek soru:** Battle bir kısayol olarak mı kalıyor, yoksa fiilen zorunlu mu oldu?

### 4a — Battle *(4–5 hafta)*

- Battle sahnesi + dalga iskeleti, 90–120 sn
- Kadro seçimi — **savaşan Luupie o sırada hatta çalışamaz**
- **Ekipman kilidi:** verdiğin onarılmış oyuncak siparişe koyulamaz →
  battle hattın çıktısı için siparişle **yarışır**
- Yatkınlık sistemi savaşa uyarlanır — aynı karakter, aynı mantık
- Ödül: nadir parça · hasarlı düşman oyuncak (hattın en değerli girdisi)
- Kayıp: ekipman **kırılır** → hatta bozuk oyuncak olarak döner
  *(kayıp değil, gecikme — hiçbir yerde ölü uç yok)*
- Her savaş: kadro **−15 moral** → doğrudan yemekhaneye talep
- Günlük 3 giriş + etkinlik iskeleti

### 4b — Yumuşak lansman *(4–6 hafta)*

- Mağaza build'i (iOS + Android), imzalama, cihaz matrisi
- Analitik + kohort raporlama
- Reklam SDK + ödüllü yerleşimler — **moral satmaz**
- Mağaza ekonomisi (paket, kaynak, hızlandırma)
- Ses tasarımı · yerelleştirme iskeleti
- UA kampanyası + iterasyon

### 🚦 KAPI 4

| Ölçüt | Eşik |
|---|---|
| **Battle'lı ÷ battle'sız ilerleme** | **1.8× – 2.2×** |
| Battle oynamayanın D14 | Oynayanın %80'inden az değil |
| Ekipman kilidi | Sipariş süresini ≤ %25 uzatıyor |
| D30 ROAS | iOS ~%47 · Android ~%15 civarı |

2.5×'in üstü "battle zorunlu oldu" demek → Hurdalık hızlandırılır.
**%150 ROAS planlama varsayımı olarak kullanılmasın.**

---

## Sayılar tek bakışta

| Ne | Değer |
|---|---|
| Moral çarpanı | `0.55 + sevgi/100 × 0.75` → ×0.55 … ×1.30 |
| Nötr nokta | Sevgi **60** = ×1.00 |
| Psycho eşiği | Sevgi **25** |
| Moral düşüşü | Çalışan −6/sa · boşta −2/sa · battle −15 · çevrimdışı 4 sa tavan |
| Kantin rafı | 1 🥕 → +4 moral, tavan 60 |
| Yemekhane | 3 🥕 → +25 moral, tavan 100, süre 60–90 sn |
| İstasyon çarpanı | İşçi × Yatkınlık × Moral × Hızlanma |
| Yatkınlık | ×1.35 (tür istasyonla eşleşirse) |
| Psycho / overdrive | ×2 hız · psycho'da %18 hatalı |
| Birleştirme | 3 aynı / 5 karışık → üst seviye, maks L3 |
| Sipariş | 1 aktif + 1 sıradaki |
| Panel | %66 genişlik × %90 yükseklik |
| Referans yön | **Yatay**, 932 × 430 tasarım / 1920 × 886 hedef |
| Oturum | Kısa 1–2 dk · orta 4–6 dk · uzun 8–12 dk · günde 2–3 |
| Çevrimdışı tavan | 4 saat |
| Faz 1 kapsamı | 1 bölge · 4 istasyon · 5 karakter · 2 hasar tipi |

---

## Toplam

| Faz | Süre | Kod | Sanat | Çıktı |
|---|---|---|---|---|
| **1 · Tamirhane** | 8–9 hf | ~17.5 | ~7.5 | **Yayınlanabilir idle oyun** |
| **2 · Yemekhane** | 2–3 hf | ~6 | ~3 | %30'luk moral bandı, aktif katman |
| **3 · Genişleme** | 3–4 hf | ~8 | ~4 | Gerçek kaynak ekonomisi, 4 hasar tipi |
| **4 · Battle + lansman** | 8–11 hf | ~18 | ~4.5 | Yan mod + mağaza + UA |

**≈ 50 adam-hafta kod + 19 sanat.** Üç kişilik ekiple **Faz 1 yayınına
~8–9 hafta**, tam yumuşak lansmana **~6–7 ay**.

Sanat en dar boğaz — 9 karakter × 6 durum = 54 animasyon seti kapsamı
patlatır. **5 karakterle başla**, diğer 4'ü Faz 3'te bölge açılışlarıyla gel.
