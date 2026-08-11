# Luupie — Konsept 02: Restoran Vardiyası

**Seçilen çekirdek:** Time-Management / Service · *"Yemeği sen yap, oyuncaklar servis etsin."*

> 🔻 **Kapsam değişti:** Bu konsept artık **ana oyun değil, ara oyun**.
> `OYUN-MIMARISI.md` §4 geçerlidir: 60–90 sn'lik yemekhane turu, müşteriler
> kendi işçilerin, ödül moral. Otonom garson / psycho bölümü ana oyuna
> (Tamirhane) taşındı. Aşağıdaki mutfak zinciri, kontrol şeması ve TM
> mekanikleri aynen kullanılır; bölüm/yıldız ilerlemesi ve restoran meta
> katmanı kullanılmaz.


Bu doküman `LUUPIE-SPEC.md`'nin çekirdek döngü bölümünü değiştirir. Ekran
modeli, karakter sistemi ve ekonominin meta katmanı aynen geçerli kalır —
hangi bölümlerin ayakta kaldığı §9'da.

---

## 1. Farklılaşma: garsonlar darboğazdır

Cooking Fever ve Diner DASH'te servis eden **sizsiniz**. Burada değil:

> **Siz mutfaktasınız. Servisi otonom oyuncak garsonlar yapıyor — ve onlar
> yorulunca çıldırıyor.**

Çekirdek gerilim buradan doğuyor:

```
Hızlı pişir  →  tabaklar pastan taşar  →  garson yetişemez
             →  morali düşer  →  PSYCHO  →  tepsiyi düşürür, koridoru kapatır
```

Yani **sadece hızlı olmak yetmiyor.** Mutfak hızını garson kapasitesine göre
ayarlamak gerekiyor. Bu, tür içinde gerçek bir yenilik ve "Cute → Psycho"
hook'unun mekanik karşılığı — hook artık afiş değil, oynanış.

Ve kritik olan: **darboğaz okuma becerisi aynen korunuyor**, sadece öznesi
makinelerden garsonlara geçiyor.

| Eski (fabrika) | Yeni (restoran) |
|---|---|
| İstasyon tamponu dolar | **Pas tezgahında tabak yığılır** |
| Sonraki istasyon aç kalır | **Garson boşta bekler** |
| Makine tıkanır | **Garson çıldırır** |

Tasarladığımız diegetic dil birebir taşınıyor.

---

## 2. Çekirdek döngü — vardiya

Bir vardiya 90–150 saniye.

```
 MÜŞTERİ GELİR ──▶ GARSON SİPARİŞ ALIR ──▶ PAS TEZGAHI
                                                │
                     ┌──────────────────────────┘
                     ▼
              ★ MUTFAK — OYUNCU ★
        ┌────────┐  ┌────────┐  ┌─────────┐
        │ DOĞRA  ├─▶│ PİŞİR  ├─▶│ TABAKLA │──▶ PAS TEZGAHI
        └────────┘  └────────┘  └─────────┘         │
                                                     ▼
                                          GARSON MASAYA GÖTÜRÜR
                                                     │
                                                     ▼
                                          MÜŞTERİ YER · ÖDER · ÇIKAR
```

**Oyuncunun elleri mutfakta.** Doğrama, pişirme ve tabaklama oyuncunun
dokunuşuyla ilerler. Garsonlar otonomdur — sipariş alır, hazır tabağı götürür.

**Oyuncunun ikinci işi:** garsonların moralini gözetmek. Yığılma büyüdükçe
moral düşer; eşiği geçerse psycho olur ve vardiyayı bozar.

---

## 3. Mutfak — oyuncunun alanı

Üç istasyon, zincir hâlinde. Fabrikanın dört istasyonlu hattının doğrudan
karşılığı; kontrol oyuncuya geçmiş hâli.

| İstasyon | Eylem | Süre (Lv1) |
|---|---|---|
| **Doğra** | Malzemeye dokun → doğranır | 1.5 sn |
| **Pişir** | Tavaya koy → pişer; **fazla beklerse yanar** | 4.0 sn |
| **Tabakla** | Pişmişi tabağa al → pasa koy | 1.0 sn |

Kurallar:

- Her istasyonun **kapasitesi** vardır (Lv1: 2 eşzamanlı iş)
- **Yanma:** pişen yemek süresinin %150'sini geçerse çöp olur — tek gerçek
  ceza mekaniği, dikkat gerektirir
- Pas tezgahının **limiti** vardır (Lv1: 4 tabak). Dolarsa tabaklama durur —
  fabrikadaki "çıktı tamponu dolunca istasyon durur" kuralının aynısı

Yükseltmeler: istasyon süresi ↓, kapasite ↑, pas limiti ↑ — hepsi mevcut
upgrade matrix'iyle.

---

## 4. Garsonlar — otonom ve kırılgan

Her garson bir Luupie. Sahnede yürür, sipariş alır, tabak taşır.

### Davranış döngüsü

```
boşta → masaya git → sipariş al → pasa götür
      → hazır tabak bekle → al → masaya götür → boşta
```

### Moral

| Etken | Etki |
|---|---|
| Pas tezgahında tabak beklemesi | Her 5 sn'de moral −2 |
| Müşteri sabrı tükenip çıkması | Moral −10 |
| Zamanında teslim | Moral +3 |
| Vardiya sonu başarı | Moral +15 |

Moral doğrudan **yürüme hızına** ve **taşıma kapasitesine** girer:

```
hız çarpanı = 0.55 + moral/100 × 0.75      (mevcut formül, aynen)
taşıma      = moral ≥ 60 ise 2 tabak, altında 1
```

### Psycho

Moral **%25** altına düşerse garson çıldırır:

| | Sonuç |
|---|---|
| Kazanç | **2× hızlı** koşar |
| Bedel | Taşıdığının **%18'i** yere düşer, koridoru kapatır |
| Görsel | Mor aura, titrek duruş, tepsi savurma |
| Çözüm | **Sakinleştir** mini oyunu · veya tatlı ikram et · veya bırak koşsun |

Fabrika versiyonundaki üç seçenek aynen korunuyor. Ve enerji ile ikili yol da
duruyor:

| Yol | Hız | Bedel | Risk |
|---|---|---|---|
| ⚡ "Acele Et!" | Tüm garsonlar ×1.5 · 20 sn | 10 enerji | Yok |
| 💢 Psycho | Tek garson ×2 | Bedava | %18 tabak düşer |

### Tür yatkınlığı

| Luupie | Yatkınlık |
|---|---|
| Vako (ördek) | Sipariş alma — müşteri sabrını yavaşlatır |
| Cıvata (robot) | Taşıma — 3 tabak taşır |
| Pofu (tavşan) | Hız — ×1.35 yürüme |
| Şefo (domuz) | **Mutfak yardımcısı** — bir istasyonu otomatik ilerletir |
| Mırmır (kedi) | Moral — yakınındaki garsonların moral düşüşünü yavaşlatır |
| Ponpon (ayı) | Sabır — psycho eşiği %25 yerine %15 |
| Uni · Çako · Rako | Sonraki bölgelerde açılır |

Böylece "yeni Luupie sahiplen" kararı yine hat kurma kararı olur.

---

## 5. Müşteriler

**Müşteriler de Luupie.** Farklı türler farklı yemek ister; bu hem 27
sprite'ın tamamını kullanır hem de koleksiyon/yatkınlık diline bağlanır.

| Özellik | Değer |
|---|---|
| Sabır | 25–40 sn (yemeğe ve bölgeye göre) |
| Sabır göstergesi | Baş üstünde diegetic baloncuk, dolu → boş |
| Sabır biterse | Çıkar, bahşiş yok, garson morali −10 |
| Bahşiş | Hızlı teslimde ödeme +%20'ye kadar |

---

## 6. Vardiya sonucu

| Yıldız | Koşul |
|---|---|
| ★★★ | Hedef ciroya ulaş **ve** hiç müşteri kaçmasın **ve** psycho olayı olmasın |
| ★★ | Hedef ciroya ulaş, en fazla 1 kayıp veya 1 psycho olayı |
| ★ | Hedef ciroyu tuttur |
| Başarısız | Ciro hedefin altında |

Başarısızlıkta kaynak yanmaz — vardiya tekrar oynanır. (Konsept dokümanının
"ceza değil, kaçan fırsat" ilkesi.)

---

## 7. Meta katman — vardiyalar arası

Aktif vardiya bittiğinde restorana dönülür. Burası **idle katman** ve
`EKONOMI-V4`'ten gelen sistemlerin çoğu aynen çalışır.

| Sistem | Restoran karşılığı | Durum |
|---|---|---|
| Üç kaynak (Wool/Oil/Mine) | **Üç malzeme** (Tahıl / Süt / Sebze) | ✅ aynen |
| Şehir kaynak binaları | Çiftlikler — malzeme üretir, deposu dolunca durur | ✅ aynen |
| Depo dolunca durma | Aynen | ✅ |
| Upgrade matrix (6 parametre) | İstasyon, pas, masa, garson slotu | ✅ aynen |
| Siparişler | **Catering kontratları** — vardiya dışı, uzun süreli | ✅ uyarlanır |
| Enerji | "Acele Et!" yakıtı | ✅ aynen |
| Geri dönüşüm | Bozulan malzeme → alt kalite / enerji | ✅ uyarlanır |
| Bölge restorasyonu | Yeni restoran bölgeleri | ✅ aynen |
| Koleksiyon | Tarif koleksiyonu + mezun garsonlar | ✅ uyarlanır |
| **Merge (3 aynı / 5 karışık)** | — | ⚠️ **bkz. aşağı** |

**Merge hakkında dürüst not:** Fabrikada doğal oturuyordu (L1 oyuncak → L3).
Restoranda karşılığı zorlama olur; yemek birleştirmek mantıklı bir fiil değil.
İki seçenek:

1. **Bırakılsın.** TM'in kendi ilerleme ekseni (yıldız → bölüm → bölge) zaten
   var; merge fazlalık olur.
2. **Tarif geliştirmeye dönüşsün.** Aynı yemeği 3 kez ★★★ ile servis et →
   tarif seviyesi artar → daha pahalı menü öğesi açılır.

**Öneri: 2.** Merge'in matematiği korunur, fiili anlamlı hale gelir.

---

## 8. Ekran modeli

`LUUPIE-SPEC.md` §11'deki üç bölge kuralı **aynen geçerli**:

```
┌──────────────────────────────────────────────────────────────┐
│ ⏱ 1:24   🪙340                              ★ hedef 500  ⚙  │ ← köşe kromu
│                                                              │
│   ╭─────╮        MASALAR                                     │
│   │ 😋  │      ▣  ▣  ▣  ▣                    YAŞAM ALANI     │
│   ╰──┬──╯       ●     ●                     krom giremez     │
│  ┌───┴──┐  ┌──────┐  ┌────────┐  ┌─────┐                    │
│  │DOĞRA │─▶│PİŞİR │─▶│TABAKLA │─▶│ PAS │  ← oyuncunun eli   │
│  └──────┘  └──────┘  └────────┘  └─────┘                    │
│ 📋                                        [🍳][🏙][💜]       │ ← köşe kromu
└──────────────────────────────────────────────────────────────┘
```

- **Mutfak alt şeritte** — başparmak menzilinde, çünkü sürekli dokunuluyor
- **Salon üstte** — izlenir, dokunulmaz (garsonlar otonom)
- Diegetic baloncuklar aynen: müşteri sabrı, garson morali, pişme sayacı,
  psycho uyarısı
- Panel sistemi (%66 × %90) meta katmanda aynen
- **Dönüş deltası** vardiya sonunda çalışır: yükseltme aldıysan sonraki
  vardiyada farkı ilk 3 saniyede gör

Değişen tek kural: vardiya sırasında **panel açılmaz**. Aktif bölüm kesintisiz
akar; tüm yönetim vardiya dışında.

---

## 9. Ne taşınıyor, ne gerekiyor

### Doğrudan taşınanlar ✅

| Varlık | Not |
|---|---|
| 27 karakter sprite + yürüme | Garson **ve** müşteri olarak — hepsi kullanılır |
| Psycho sistemi | Çekirdek hook, tasarımı hazır |
| Sevgi/moral çarpan formülü | Aynı formül, `0.55 + moral/100 × 0.75` |
| Tür yatkınlığı | Yeni rollere eşlendi (§4) |
| Sakinleştirme mini oyunu | Psycho garson için birebir |
| Yemekhane mini oyunu | Tatlı ikramı olarak birebir |
| Ekonomi V4'ün meta katmanı | §7 tablosu |
| Ekran modeli V3 | Üç bölge, panel, diegetic dil |
| Şehir / bölge restorasyonu | Restoran bölgeleri |
| İzometrik render hattı | Kamera ve derinlik sıralaması aynı |

### Yeniden gerekenler ⚠️

| İş | Büyüklük |
|---|---|
| Restoran izometrik sahnesi (mutfak + salon) | **Büyük** — ana sanat maliyeti |
| Yemek ve tabak sprite'ları (~12 yemek × 3 aşama) | Orta |
| Masa, sandalye, pas tezgahı | Orta |
| Mutfak dokunuş kontrolleri | Orta |
| Vardiya/bölüm çerçevesi (süre, hedef, yıldız) | Orta |
| Müşteri gelme/oturma/ayrılma davranışı | Orta |
| Garson yol bulma (masa ↔ pas) | Orta |

### Rafa kalkanlar

Fabrika hattı simülasyonu, üretim hattı sanatı, oyuncak merge — bunlar
`LUUPIE-SPEC.md`'de kayıtlı kalır; ileride idle bir yan mod istenirse hazır.

---

## 10. İlk dikey dilim

Prototip için en kısa yol — panonun "prototip hızı" kriterine oynar:

| # | İş |
|---|---|
| 1 | Tek vardiya: 3 masa, 1 garson, 2 yemek, 90 sn |
| 2 | Mutfak zinciri: doğra → pişir → tabakla, dokunuşla ilerler |
| 3 | Pas tezgahı limiti + tabak yığılması (diegetic) |
| 4 | Garson otonom döngüsü + moral düşüşü |
| 5 | Psycho dönüşümü + sakinleştirme mini oyunu |
| 6 | Yıldız değerlendirmesi + vardiya sonu ekranı |
| 7 | Tek yükseltme (pişirme hızı) + dönüş deltası |

Bu yedi madde **çekirdek hipotezi test eder**: "mutfak hızını garson
kapasitesine göre ayarlamak eğlenceli mi?" Cevap evetse gerisi ölçek.

Mevcut karakter sprite'ları ve psycho tasarımı hazır olduğu için 4–5. maddeler
neredeyse bedava geliyor.

---

## 11. Açık sorular

1. **Yemek sayısı ve karmaşıklığı:** ilk bölgede 2 yemek mi 4 mü? (Öneri: 2 —
   FTUE'de tek mekanik öğretilir)
2. **Mutfak kontrolü:** dokun-ilerlet mi, sürükle-bırak mı? (Öneri: dokun —
   yatayda iki başparmak, sürükleme yavaş)
3. **Vardiya uzunluğu:** 90 sn mi 150 sn mi? (Öneri: 90 ile başla, telemetriyle
   uzat)
4. **Merge:** bırakılsın mı, tarif geliştirmeye mi dönüşsün? (Öneri: tarif)
5. **Mevcut fabrika build'i:** yaratıcı test için canlı tutulsun mu, arşive mi
   kalksın? (Öneri: canlı tutulsun — pano yaratıcı testi genre kilidinden önce
   istiyor ve elde çalışan bir görsel var)
