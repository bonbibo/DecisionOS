# Luupie — Üretim Planı

Konsept 02 (Restoran Vardiyası) için faz haritası, iş paketleri, sanat listesi

> 🏗 **Mimari güncellendi:** `OYUN-MIMARISI.md` üç katmanlı yapıyı tanımlıyor
> (Tamirhane idle ana oyun · Yemekhane ara oyun · Battle + Genişleme yan oyun).
> Aşağıdaki faz yapısı ve kapılar geçerli, ama **Faz 1 prototipinin konusu
> Tamirhane idle çekirdeğidir**, restoran vardiyası değil. Yemekhane
> Aşama 2'ye, Battle Aşama 4'e kayar (mimari §8).

ve karar kapıları.

Efor **adam-hafta** cinsinden verilir; takvim ekip büyüklüğüne göre değişir.
Referans takvim **1 geliştirici + 1 sanatçı + yarım zamanlı tasarım** varsayar.

---

## 1. Plan varsayımları

`KONSEPT-02-RESTORAN.md` §11'deki açık sorular plan için şöyle bağlandı.
Değiştirmek isterseniz plan buna göre kayar.

| Soru | Varsayım | Gerekçe |
|---|---|---|
| Yemek sayısı | Prototipte **2**, Bölge 1'de **8** | FTUE'de tek mekanik öğretilir |
| Mutfak kontrolü | **Dokun-ilerlet** | Yatayda iki başparmak; sürükleme yavaş ve hataya açık |
| Vardiya uzunluğu | **90 sn** ile başla | Telemetriyle uzat, kısaltmak zor |
| Merge | **Tarif geliştirmeye** dönüşür | Yemek birleştirmek anlamlı bir fiil değil |
| Mevcut fabrika build'i | **Canlı kalır** | Yaratıcı test malzemesi; yeni build'i beklemez |

---

## 2. Faz haritası

```
FAZ 0          FAZ 1                FAZ 2                  FAZ 3
Kararlar   →   Prototip        →    Dikey dilim       →    Yumuşak lansman
1 hafta        3–4 hafta            5–6 hafta              4–6 hafta
               ▲                    ▲                      ▲
            KAPI 1               KAPI 2                 KAPI 3
        "eğlenceli mi?"     "tutuyor mu?"          "ekonomi çalışıyor mu?"
```

Her kapı **geçilemezse durulur veya yön değişir**. Kapı kriterleri §8'de.

---

## 3. Faz 0 — Kararlar ve hazırlık · 1 hafta

Kod yazılmadan önce kapatılması gereken üç şey.

| # | İş | Efor | Not |
|---|---|---|---|
| 0.1 | **Motor kararı** | 2 gün | §5 — planın en kritik maddesi |
| 0.2 | **Sanat stili kilidi** | 3 gün | Restoran sahnesi için 1 anahtar kare; mevcut karakterlerle uyum testi |
| 0.3 | **Yaratıcı test kurulumu** | 2 gün | §6 — Faz 1 ile paralel koşar |
| 0.4 | Mevcut build'in bloke hatasını düzelt | 0.5 gün | Sipariş düğmesi nav'ın altında; test malzemesi çalışır olmalı |

---

## 4. Faz 1 — Prototip · 3–4 hafta

**Tek soru:** *Mutfak hızını garson kapasitesine göre ayarlamak eğlenceli mi?*

Sanat placeholder olabilir. Mevcut karakter sprite'ları kullanılır. Hiçbir
meta sistem yok — ne para, ne yükseltme, ne bölüm haritası.

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 1.1 | Vardiya iskeleti: süre, hedef ciro, başla/bitir | 0.1 | 0.5 |
| 1.2 | Mutfak zinciri: doğra → pişir → tabakla, dokunuşla ilerler | 1.1 | 1.0 |
| 1.3 | Yanma mekaniği (süre ×1.5 aşılırsa çöp) | 1.2 | 0.3 |
| 1.4 | Pas tezgahı + limit + tabak yığılması (diegetic) | 1.2 | 0.5 |
| 1.5 | Müşteri: gelme, oturma, sipariş, sabır, ayrılma | 1.1 | 1.0 |
| 1.6 | Garson otonom döngüsü + yol bulma | 1.4, 1.5 | 1.5 |
| 1.7 | Moral sistemi + hız/kapasite çarpanı | 1.6 | 0.5 |
| 1.8 | **Psycho dönüşümü** + tabak düşürme + koridor tıkama | 1.7 | 0.8 |
| 1.9 | Sakinleştirme mini oyunu (mevcut tasarım) | 1.8 | 0.5 |
| 1.10 | Yıldız değerlendirmesi + vardiya sonu ekranı | 1.1 | 0.5 |
| 1.11 | Tek yükseltme (pişirme hızı) + dönüş deltası | 1.10 | 0.5 |
| 1.12 | İç test turu + denge iterasyonu | hepsi | 1.5 |

**Toplam ≈ 9 adam-hafta** · 2 kişiyle 4–5 hafta, 3 kişiyle 3 hafta.

**Kritik yol:** 1.2 → 1.4 → 1.6 → 1.7 → 1.8. Garson otonomisi (1.6) en riskli
kalem; yol bulma ve tabak devri orada.

---

## 5. Motor kararı

Planın en büyük çatalı. Mevcut build **web SPA** (Vite/rolldown paketleri,
DOM + canvas). Prototip için hızlı, üretim için sınırları var.

| | Web (mevcut) | Unity |
|---|---|---|
| Prototip hızı | **Çok hızlı** — kod tabanı hazır | Yavaş — sıfırdan kurulum |
| 60 fps, çok sprite | Riskli (DOM ağır, canvas yönetimi elle) | **Güçlü** |
| Mağaza dağıtımı | Sarmalayıcı gerekir | **Yerel** |
| Yaratıcı test | Anında link | Build gerekir |
| Ekip aşinalığı | Bilinmiyor | Bilinmiyor |
| Reklam SDK / analitik | Zahmetli | **Standart** |

**Öneri: iki aşamalı.** Faz 1 prototipi **web'de** yapılsın — kod tabanı,
karakterler ve ekran modeli hazır, KAPI 1'e en hızlı oradan varılır. KAPI 1
geçilirse Faz 2 **Unity'de** kurulur; prototip o noktada zaten atılacak bir
şeydir (throwaway), tasarım kararları taşınır, kod taşınmaz.

Bunun bedeli: Faz 2 başında ~1 hafta kurulum. Kazancı: yanlış türe 3 ay
harcamama riski.

> Ekip Unity'de daha hızlıysa Faz 1 de Unity'de yapılabilir; o zaman prototip
> takvimi ~1 hafta uzar ama Faz 2 kurulumu düşer. Karar ekip aşinalığına bağlı.

---

## 6. Paralel iş — yaratıcı test

Pano bunu genre kilidinden **önce** istiyordu; kilit verildi, ama test yine de
Faz 1 ile **paralel** koşmalı — sonucu Faz 2 kapsamını belirler.

| # | İş | Efor |
|---|---|---|
| 6.1 | 3–5 statik konsept: Cute→Psycho dönüşümü, garson çöküşü, restoran kaosu | 0.5 |
| 6.2 | $500–1.500 bütçeyle test kurulumu (Meta / TikTok) | 0.3 |
| 6.3 | Sonuç okuma: **CPI ve IPM** birincil, CTR ikincil | 0.2 |

Mevcut fabrika build'i görsel malzeme üretebiliyor; restoran mockup'ı için
0.2 hafta sanat yeter.

**Kıyas ölçütü:** Pano casual ortalamasını Android **$0.14**, iOS **$1.41**
olarak veriyor. Bunun belirgin altına inemiyorsak hook zayıf demektir.

---

## 7. Sanat üretim listesi

En büyük maliyet kalemi ve en uzun teslim süresi olan taraf.

### Faz 1 (placeholder kabul edilir)

| Varlık | Adet | Efor |
|---|---|---|
| Mutfak istasyonları (kaba) | 3 | 0.3 |
| Masa + sandalye (kaba) | 1 set | 0.2 |
| Yemek: ham / pişmiş / tabaklı | 2 × 3 | 0.3 |
| Mevcut karakter sprite'ları | — | 0 (hazır) |

### Faz 2 (üretim kalitesi)

| Varlık | Adet | Efor |
|---|---|---|
| **Restoran sahnesi** (mutfak + salon, izometrik) | 1 | **2.5** |
| Yemekler | 8 × 3 aşama | 1.5 |
| Mobilya, dekor, bölge varyasyonu | 1 set | 1.0 |
| **Karakter animasyonları** | bkz. aşağı | **3.0** |
| Vardiya UI, yıldız ekranı, panel çerçevesi | — | 1.0 |
| Efektler (buhar, yanık, psycho aurası, tabak kırılması) | — | 0.8 |

### Karakter animasyon kapsamı — dikkat

Restoran altı yeni durum istiyor: **boşta · yürüme · tepsi taşıma · sipariş
alma · psycho koşu · tepsi düşürme.**

Elimizde 4 karakterin yürüme sayfası var. 9 karakter × 6 durum = **54 animasyon
seti** — bu kapsam patlar.

**Öneri: 3 karakterle tam kadro başla.** Pofu, Şefo, Vako (üç farklı yatkınlık
rolü). Diğerleri Faz 3'te bölge açılışlarıyla gelir. Böylece Faz 2 animasyon
yükü 18 sete iner.

---

## 8. Karar kapıları

### KAPI 1 — Faz 1 sonu · "Eğlenceli mi?"

| Ölçüt | Eşik |
|---|---|
| İç test oturumu | En az 8 kişi, her biri 5+ vardiya |
| "Tekrar oynamak istedim" | ≥ %60 |
| Ortalama vardiya süresi | Oyuncu ikinci vardiyayı **kendiliğinden** başlatıyor mu |
| Psycho olayı | Oyuncu bunu *kendi hatası* olarak algılıyor mu (sistem kusuru değil) |
| Yaratıcı test CPI | Hedef aralığın içinde (§6) |

Geçemezse: mutfak/garson dengesi mi bozuk, yoksa konsept mi zayıf — ayırt et.
İkincisiyse Konsept 01 (Tamirhane) yedekte; sahne dışında her şey ortak.

### KAPI 2 — Faz 2 sonu · "Tutuyor mu?"

| Ölçüt | Eşik |
|---|---|
| D1 retansiyon | ≥ %35 |
| D7 retansiyon | ≥ %12 |
| Oturum/gün | ≥ 2 |
| Bölüm tamamlama | İlk 10 vardiyada bırakma ≤ %40 |

### KAPI 3 — Faz 3 sonu · "Ekonomi çalışıyor mu?"

| Ölçüt | Eşik |
|---|---|
| D30 ROAS | **Panonun kendi verisiyle gerçekçi hedef: iOS ~%47, Android ~%15 civarı** |
| ARPDAU | Bütçe modeline göre |
| Reklam gösterimi/oturum | Türe uygun aralıkta |

> %150 net ROAS **planlama varsayımı olarak kullanılmasın** — panonun kendi
> uyarısı. Bütçe gerçek aralığa göre kurulmalı.

---

## 9. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| **Sanat kapsamı patlar** (54 animasyon) | Takvim ×2 | 3 karakterle başla; diğerleri bölge açılışıyla |
| **Garson yol bulma karmaşıklaşır** | Kritik yolda gecikme | Izgara tabanlı basit yol; serbest navigasyon yok |
| **TM türü kalabalık** | Farklılaşma kaybolur | Psycho garson KAPI 1'de kanıtlanmalı, sonraya bırakılmaz |
| **Motor kararı gecikirse** | Yeniden yazım | Faz 0'da kapatılır, ertelenmez |
| **ROAS beklentisi gerçekçi değil** | Bütçe modeli çöker | Pano verisiyle yeniden hesap, Faz 0'da |
| **Prototip kodu üretime taşınmak istenir** | Teknik borç | Faz 1 kodu baştan **atılacak** ilan edilsin |

---

## 10. İlk iki hafta — somut

Bugünden başlayarak yapılacaklar:

**1. hafta**
1. Motor kararı toplantısı → karar yazılı olarak kaydedilsin *(0.1)*
2. Sanat: restoran anahtar karesi — mevcut karakterlerle uyum testi *(0.2)*
3. Mevcut build'in sipariş düğmesi düzeltilsin, yaratıcı test malzemesi hazırlansın *(0.4)*
4. Yaratıcı test konseptleri brief'i *(6.1)*

**2. hafta**
5. Vardiya iskeleti + mutfak zinciri kodlanır *(1.1, 1.2)*
6. Placeholder mutfak sanatı *(Faz 1 sanat)*
7. Yaratıcı test yayına alınır *(6.2)*

İki hafta sonunda elde: **dokunarak yemek pişirilebilen, süreli bir vardiya**
ve **yayında bir yaratıcı test**.

---

## 11. Özet tablo

| Faz | Süre | Efor (adam-hafta) | Çıktı |
|---|---|---|---|
| 0 · Kararlar | 1 hafta | 1.5 | Motor + stil kilidi + test yayında |
| 1 · Prototip | 3–4 hafta | 9 + 0.8 sanat | Oynanabilir tek vardiya |
| 2 · Dikey dilim | 5–6 hafta | ~16 + 10 sanat | Bölge 1, meta katman, FTUE |
| 3 · Yumuşak lansman | 4–6 hafta | ~14 | Mağaza build'i, analitik, UA |

**Yumuşak lansmana kadar ≈ 4 ay**, üç kişilik ekiple. Sanat tarafı en dar
boğaz — karakter animasyon kapsamı kontrol altında tutulursa takvim tutar.
