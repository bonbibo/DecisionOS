# Luupie — Konsept Kararı

Girdi: `Luupie Konsept Sunumu` (Ağustos 2026) + FigJam kanıt panosu
(Audience Research · Genre Table · Evidence Standard · Marketing Expectations).

---

## 1. Sunum ne diyor

**Hedef kitle:** 16–30, karma cinsiyet, global T2–T3, casual / hybrid-casual;
sevimli maskot + absürt kaos + dönüşüm + hafif kara mizah.
**Görsel hook:** Cute → Psycho.

**Dört konsept, iki tür:**

| # | Konsept | Tür | Özü |
|---|---|---|---|
| 01 | **Tamirhane** | Time-Management / Service | Bozuk oyuncakları tamir et, kaosu engelle |
| 02 | **Restoran Vardiyası** | Time-Management / Service | Sen pişir, oyuncak garsonlar servis etsin |
| 03 | **Fabrika Kuşatması** | Survivor / Arena | Oyuncak istilasına karşı ayakta kal |
| 04 | **Bölge Savunması** | Survivor / Arena | Savaş, kurtar, bölgeni büyüt, kalıcı güçlen |

---

## 2. Asıl gerilim

Panodaki tür tablosu yedi yönü sıralıyor. İki satır bizi doğrudan ilgilendiriyor:

| Sıra | Tür | Karakter uyumu | Pazarlama | Monetizasyon | Retansiyon | Prototip hızı | Üretim riski | Genel |
|---|---|---|---|---|---|---|---|---|
| **1** | Casual Time Management / Service | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ | Low-Med | ★★★★★ |
| **5** | **Idle / Auto-Battler** | ★★★★☆ | ★★★★☆ | **★★★★★** | **★★★★★** | ★★★☆☆ | Medium | ★★★★☆ |

**Şu ana kadar inşa ettiğimiz şey 5. sıradaki tür.** Panonun kendi
değerlendirmesi idle'ı prototip hızı ve üretim riski yüzünden aşağı çekiyor.

Ama aynı tablo şunu da söylüyor: **idle, yedi yön içinde monetizasyon ve
retansiyonda tek başına en yüksek puanı alıyor** (ikisinde de ★★★★★). Yani
idle reddedilmiyor — "yavaş ve riskli ama uzun vadede en kazançlı" deniyor.

Bu, ikisini karşı karşıya koymak yerine **birleştirmeyi** işaret ediyor.

---

## 3. Elimizde ne var, hangi konsepte ne kadar taşınır

Mevcut varlıklar: 27 karakter sprite (9 tür × kafa/sweet/psycho) + yürüme
sprite'ları · izometrik fabrika sanatı · 4 istasyonlu hat simülasyonu ·
işçi atama + yatkınlık + moral çarpanı · 3 kodlanmış mini oyun (Tamir,
Yemekhane, Zapt) + 3 tasarlanmış · sipariş ekonomisi, upgrade matrix, merge,
geri dönüşüm · şehir/bölge restorasyonu · yatay ekran modeli · çalışan build.

| Konsept | Karakterler | Sahne/sanat | Mini oyunlar | Ekonomi | Hat simülasyonu | Yeniden kullanım |
|---|---|---|---|---|---|---|
| **01 Tamirhane** | ✅ | ✅ fabrika→tamirhane | ✅ **Tamir çekirdek olur** | ✅ meta | ⚠️ kontrol değişir | **En yüksek** |
| **02 Restoran** | ✅ garson olur | ❌ yeni ortam | ✅ **Yemekhane çekirdek olur** | ✅ meta | ⚠️ kontrol değişir | Orta |
| **03 Kuşatma** | ⚠️ düşman olur | ✅ fabrika durur | ❌ | ❌ | ❌ | Düşük |
| **04 Bölge Savunması** | ✅ | ❌ | ❌ | ⚠️ kısmen | ❌ | Düşük–orta |

Konsept 04'ün meta döngüsü (`SAVUN → KURTAR → ÜSSE DÖN → GELİŞTİR → GÜÇLEN`)
şehir restorasyon sistemimizle **birebir aynı yapıda** — orası transfer eder,
ama çekirdek combat sıfırdan.

---

## 4. Kritik gözlem: Tamirhane bir yeniden yazım değil, kontrol değişimi

Elimizdeki hat oyunu ile Konsept 01 arasındaki fark tür farkı gibi görünüyor
ama değil. İkisi de aynı şeyi yapıyor: **istasyonlar, kuyruk baskısı, stresli
karakterler, zaman.**

Tek gerçek fark:

| | Şimdi (idle) | Konsept 01 (TM) |
|---|---|---|
| İstasyon işini kim yapar | İşçi otomatik | **Oyuncu, süre baskısı altında** |
| Darboğaz nerede | Hattın en yavaş halkası | **Oyuncunun elleri** |
| Oturum | Bakış, kontrol | Bölüm oyna, yıldız al |
| Başarısızlık | Yok | Bölüm kaybı / düşük yıldız |

Yani hattı, tamponları, yatkınlığı ve psycho'yu atmıyoruz — **kontrolü
oyuncuya veriyoruz ve etrafını bölümle sarıyoruz.**

---

## 5. Öneri: TM çekirdek + idle meta (hybrid-casual)

Sunumun kendi tanımı zaten bu: **hybrid-casual**. Panonun tablosu da tam olarak
bu birleşimi destekliyor — her türün güçlü olduğu sütunu alıyoruz:

```
   TM / Service'ten          Idle'dan
   ─────────────────         ─────────────────
   ★★★★★ pazarlama           ★★★★★ retansiyon
   ★★★★★ karakter uyumu      ★★★★★ monetizasyon
   ★★★★☆ prototip hızı       (mevcut kodumuz)
```

**Yapı:**

- **Çekirdek (aktif):** Konsept 01 Tamirhane. Oyuncu bölüm oynar — bozuk
  oyuncak akışı gelir, tamir eder, psycho'ları sakinleştirir, süre biter,
  yıldız alır. Mevcut Tamir mini oyunu bunun çekirdeği olur.
- **Meta (idle):** Mevcut fabrika hattı. Bölümler arasında arka planda üretim
  yapar, kaynak biriktirir, sipariş doldurur. Oyuncu bölümden çıkınca
  fabrikasına döner, yükseltir, işçi atar.
- **Bağ:** Bölümde kazanılan yıldızlar fabrikayı büyütür; fabrikadan çıkan
  kaynak bölümde kullanılan araçları/güçlendirmeleri açar.

Bu, hem panonun 1. sıradaki türünü çekirdeğe koyar hem de 5. sıradaki türün
retansiyon/monetizasyon avantajını korur — ve **yazdığımız kodun tamamı
kullanılır.**

---

## 6. Panodan çıkan iki uyarı

Kanıt standardı bölümü kendi kendine dürüst davranıyor; iki maddeyi öne
çıkarmakta fayda var:

**ROAS varsayımı.** Pano diyor ki: casual D30 ROAS ortalaması iOS'ta ~%47,
Android'de ~%15 (Liftoff/Singular). %150 net ROAS "iddialı ve kanıtlanmamış";
panonun kendi ifadesiyle *planlama varsayımı olarak gerçekçi değil*. Bütçe
modeli buna göre kurulmalı.

**Hook henüz doğrulanmadı.** *"Cute → Psycho güçlü bir hipotez, henüz
doğrulanmadı."* Pano, oyun inşa edilmeden önce 3–5 statik konseptle
$500–1.500'lük bir yaratıcı test öneriyor ve kararın **CPI/IPM** ile
verilmesini, tek başına CTR ile verilmemesini söylüyor.

> **Bu ikisi tür kararından bağımsız.** Hangi konsepti seçersek seçelim,
> yaratıcı testin genre kilidinden **önce** yapılması panonun kendi
> standardına uyar. Test paralel yürüyebilir; mevcut build zaten
> ekran görüntüsü ve video üretebilecek durumda.

---

## 7. Karar gereken sorular

1. **Çekirdek tür:** TM/Service mi, Survivor mı? (Öneri: TM — hem 1. sırada
   hem elimizdekiyle en uyumlu)
2. **Hangi TM konsepti:** Tamirhane mi Restoran mı? (Öneri: Tamirhane —
   fabrika sanatı ve tamir mini oyunu doğrudan taşınır; restoran yeni ortam
   ister)
3. **Mevcut idle hat:** meta katman olarak kalsın mı, tamamen bırakılsın mı?
   (Öneri: meta olarak kalsın — panonun kendi tablosunda retansiyon ve
   monetizasyonda en yüksek puan orada)
4. **Yaratıcı test:** genre kilidinden önce mi sonra mı?
   (Öneri: önce, panonun kendi standardı bunu söylüyor)

---

## 8. Kararın mevcut işlere etkisi

| Karar | `LUUPIE-SPEC.md` | Açık iş listesi | Kod |
|---|---|---|---|
| TM çekirdek + idle meta | Çekirdek döngü bölümü yeniden yazılır; ekonomi, ekran modeli, karakter sistemi aynen kalır | 23 maddenin ~18'i geçerli kalır | Tamamı kullanılır |
| Yalnız TM (idle bırakılır) | Ekonomi ve hat bölümleri düşer | ~10 madde düşer | Hat simülasyonu rafa kalkar |
| Survivor'a geçiş | Spec'in büyük kısmı geçersiz | Liste sıfırlanır | Karakterler + sanat kalır, gerisi yeniden |

Karar verilene kadar **1 numaralı bloke madde geçerliliğini koruyor** —
sipariş düğmesi nav'ın altında ve oyun 45 saniyede kilitleniyor. Hangi yöne
gidilirse gidilsin, çalışan bir build elde tutmak yaratıcı test için de
gerekli.
