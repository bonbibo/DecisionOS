# Luupie — Üretim Planı

Üç katmanlı mimarinin (`OYUN-MIMARISI.md`) faz haritası, iş paketleri, sanat
listesi ve karar kapıları.

Efor **adam-hafta** cinsinden verilir; takvim ekip büyüklüğüne göre değişir.
Referans takvim **1 geliştirici + 1 sanatçı + yarım zamanlı tasarım** varsayar.

---

## 1. Planın tek kuralı

> **Her faz sonunda halka kapalı olmalı.**

Yani her fazın çıktısı, o an eldeki mekaniklerle **kendi başına anlamlı bir
oyun** olmalı — sonraki fazı bekleyen boşluk bırakmamalı. Bu, mimarinin
"açık uç yok" ilkesinin üretim tarafındaki karşılığı.

Pratikte şu anlama gelir: bir sonraki fazda gelecek sistemin yerine **sabit
değerli bir vekil** konur, o faz gelince vekil gerçek sistemle değiştirilir.

| Faz | Henüz yok | Vekili |
|---|---|---|
| 1 | Yemekhane | Kantin rafı tek başına çalışır — hat ×1.00'de dengelenir |
| 1–2 | Genişleme | Kaynaklar sabit oranla akar, bina yok |
| 1–3 | Battle | Nadir parça yalnız Hurdalık'tan (Faz 3), Faz 1–2'de istasyon tavanı 10 |

---

## 2. Faz haritası

```
FAZ 0        FAZ 1            FAZ 2         FAZ 3          FAZ 4        FAZ 5
Kilit    →   Tamirhane    →   Yemekhane →   Genişleme  →   Battle   →   Yumuşak
1 hf         4–5 hf           2–3 hf        3–4 hf         4–5 hf       lansman
             ▲                ▲             ▲              ▲            4–6 hf
          KAPI 1           KAPI 2        KAPI 3         KAPI 4
        "darboğaz        "aktif oyun   "ekonomi       "battle
         okunuyor mu"     tutuyor mu"   14 gün         kilitlemiyor
                                        ayakta mı"      mu"
```

Her kapı **geçilemezse durulur veya yön değişir**. Kriterler §8'de.
Mimari aşamalarıyla eşleşme: Aşama 1 → Faz 1 · Aşama 2 → Faz 2 ·
Aşama 3 → Faz 3 · Aşama 4 → Faz 4.

---

## 3. Faz 0 — Kilit ve temizlik · 1 hafta · 1.5 adam-hafta

Kod yazılmadan önce kapatılması gereken beş şey.

| # | İş | Efor | Not |
|---|---|---|---|
| 0.1 | **Motor kararı** | 2 gün | §6 — planın en kritik maddesi |
| 0.2 | **Bloke hatayı düzelt** | 0.5 gün | Sipariş düğmesi nav'ın altında; oyun 45 sn'de kilitleniyor (`LUUPIE-SPEC.md` §18 #1) |
| 0.3 | **Sanat stili kilidi** | 2 gün | Tamirhane anahtar karesi; mevcut karakterlerle uyum testi |
| 0.4 | **Telemetri şeması** | 1 gün | Kapıların ölçüleceği olay listesi baştan tanımlanır |
| 0.5 | **Yaratıcı test kurulumu** | 1 gün | §7 — Faz 1 ile paralel koşar |

**Çıktı:** Çalışan bir build, yazılı motor kararı, yayında bir yaratıcı test.

---

## 4. Faz 1 — Tamirhane çekirdeği · 4–5 hafta · ~11 adam-hafta

**Tek soru:** *Oyuncu hattaki darboğazı gözle bulup düzeltebiliyor ve buna
geri dönüyor mu?*

Yemekhane yok, şehir yok, battle yok. Kaynaklar sabit oranla akar, kantin rafı
morali 60'ta tutar — **hat ×1.00'de dengeli çalışır.** Halka kapalı: bozuk
oyuncak gelir, onarılır, sevk edilir, para istasyona yatırılır.

### 1a — Ana oyun mekaniği

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 1.1 | İstasyon yeniden adlandırma + ikon (TEŞHİS·SÖKME·ONARIM·CİLA) | 0.3 | 0.3 |
| 1.2 | **Bozuk oyuncak girdi modeli** — sonsuz hammadde kaldırılır | 1.1 | 0.8 |
| 1.3 | **2 hasar tipi + hareketli darboğaz** | 1.2 | 1.0 |
| 1.4 | Çıktı tamponu dolan istasyon **dursun** (§18 #8) | 1.2 | 0.5 |
| 1.5 | Üç kaynak + istasyon girdi maliyeti + aç kalma (§18 #9) | 1.2 | 0.8 |
| 1.6 | **Moral tek kanal:** düşüş hızları, kantin rafı, 60 tavanı | 1.5 | 1.0 |
| 1.7 | Psycho sistemi: dönüşüm, ×2, %18 hatalı, üç çıkış (§18 #5) | 1.6 | 0.8 |
| 1.8 | Birleştirme paneli 3 aynı / 5 karışık (§18 #11) | — | 0.6 |
| 1.9 | Sipariş seviyeleri + prim + plan çıktısı (§18 #12) | 1.8 | 0.6 |
| 1.10 | Upgrade matrix'i tabloya bağla (§18 #10) | 1.5 | 0.5 |
| 1.11 | Enerji + overdrive + geri dönüşüm (§18 #13, #14) | 1.7 | 0.8 |
| 1.12 | Öneri motoru: boştaki işçileri saysın (§18 #7) | 1.6 | 0.3 |

### 1b — Ekran ve his

| # | İş paketi | Efor |
|---|---|---|
| 1.13 | Panel sistemi %66 × %90 + `overflow-y: auto` (§18 #2, #20) | 0.5 |
| 1.14 | Yaşam alanı dokunulmazlığı — çakışan dokunuşları temizle (§18 #3) | 0.5 |
| 1.15 | **Dönüş deltası koreografisi** — zorunlu | 0.5 |
| 1.16 | Sevkiyat kutlaması (§18 #4) | 0.5 |
| 1.17 | Yürüme sprite'ları kullanılsın (§18 #17) | 0.3 |
| 1.18 | Mikro geri bildirim + ilerleme çubuğu (§18 #16, #18) | 0.5 |
| 1.19 | **İlk 10 dakika akışı** (`LUUPIE-SPEC.md` §16) | 1.0 |
| 1.20 | İç test turu + denge iterasyonu | 1.5 |

**Kritik yol:** 1.2 → 1.3 → 1.6 → 1.7. Hareketli darboğaz (1.3) en riskli
kalem — hasar tipi karışımı hattı gerçekten kaydırmıyorsa fikir çalışmıyor
demektir ve bunu **Faz 1'de** öğrenmek gerekir.

**Faz 1 sonunda elde:** 1 bölge · 4 istasyon · 5 karakter · 2 hasar tipi.
**Tek başına yayınlanabilir bir oyun.**

---

## 5. Faz 2 — Yemekhane · 2–3 hafta · ~6 adam-hafta

**Tek soru:** *Aktif oynanış pasif kazanca dönüşünce oyuncu daha çok kalıyor mu?*

Faz 1'de kantin rafı morali 60'ta tutuyordu. Bu faz **60–100 bandını** açıyor —
mimarinin §4'teki dört kuralı burada kodlanıyor.

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 2.1 | 🥕 Malzeme kaynağı + depo (Faz 2'de sabit oranlı vekil) | 1.6 | 0.4 |
| 2.2 | Kantin rafı: 1 🥕 → +4 moral, tavan 60 | 2.1 | 0.4 |
| 2.3 | Mutfak zinciri: doğra → pişir → tabakla, dokunuşla | 2.1 | 1.2 |
| 2.4 | Yanma: fazla pişen çöp olur, **malzeme yanar** | 2.3 | 0.3 |
| 2.5 | Masa + işçi sabrı + bekleyenin morali düşer | 2.3 | 0.8 |
| 2.6 | Servis → +25 moral, tavan 100 | 2.5 | 0.4 |
| 2.7 | **Sahneden giriş:** aç işçi baloncuğu · vardiya sonu kartı | 2.6 | 0.4 |
| 2.8 | Psycho'dan çıkış yolu olarak besleme | 1.7, 2.6 | 0.3 |
| 2.9 | Telemetri: aktif servis oranı ↔ retansiyon | 0.4 | 0.3 |
| 2.10 | Denge iterasyonu (malzeme oranı, servis kazancı) | hepsi | 1.0 |

**Denge hedefi:** Yemekhane oynamayan oyuncu ×1.00'de, düzenli oynayan
×1.20–1.25 civarında oturmalı. ×1.30 tavanı sürekli tutulabiliyorsa malzeme
çok bol demektir.

---

## 6. Faz 3 — Genişleme · 3–4 hafta · ~8 adam-hafta

**Tek soru:** *Ekonomi 14 gün boyunca tavana vurmadan ve tıkanmadan ilerliyor mu?*

Faz 1–2'nin sabit oranlı kaynak vekilleri burada **gerçek binalara** devrediliyor.

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 3.1 | Şehir sahnesi + 📋 plan para birimi | 1.9 | 1.0 |
| 3.2 | Kaynak binaları: Pamuk · İplik · Parça (depo/dolunca dur) | 3.1 | 1.0 |
| 3.3 | **Mutfak Serası** — malzeme vekilini devralır | 2.1, 3.2 | 0.4 |
| 3.4 | **Hurdalık** — nadir parça, 1/6 sa | 3.2 | 0.4 |
| 3.5 | İstasyon Sv. 10+ nadir parça kapısı | 3.4, 1.10 | 0.3 |
| 3.6 | Bölge restorasyonu: çok aşamalı proje, inşaat hâli görünür | 3.1 | 1.5 |
| 3.7 | **3. ve 4. hasar tipi** bölge açılışıyla | 1.3, 3.6 | 0.6 |
| 3.8 | Yeni istasyon slotu (hat uzar, katlanmaz) | 3.6 | 0.8 |
| 3.9 | Görevler + öneri motoru genişlemesi | — | 0.5 |
| 3.10 | Koleksiyon atölyesi (nihai sink) | 1.8 | 0.7 |
| 3.11 | 14 günlük ekonomi simülasyonu + denge | hepsi | 1.0 |

**3.11 gözden kaçmasın:** Bu bir tasarım işi değil, bir **hesap tablosu işi**.
14 günlük ilerleme oyun oynanmadan tabloda simüle edilmeli; kapı ondan sonra
oynanarak doğrulanmalı.

---

## 7. Faz 4 — Battle · 4–5 hafta · ~12 adam-hafta

**Tek soru:** *Battle bir kısayol olarak kalıyor mu, yoksa fiilen zorunlu mu oldu?*

Üç katmanın en pahalısı — sıfırdan combat.

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 4.1 | Battle sahnesi + dalga iskeleti | 3.8 | 1.5 |
| 4.2 | Düşman davranışı + 3 düşman tipi | 4.1 | 2.0 |
| 4.3 | Kadro seçimi — **savaşan hatta çalışamaz** | 4.1 | 0.8 |
| 4.4 | **Ekipman kilidi:** onarılmış oyuncak rehin, siparişle yarışır | 1.9, 4.3 | 0.8 |
| 4.5 | Yatkınlık sisteminin savaşa uyarlanması | 4.3 | 1.0 |
| 4.6 | Ödül: nadir parça + hasarlı düşman oyuncak → hatta girdi | 3.4, 4.2 | 0.6 |
| 4.7 | Kayıp: ekipman kırılır → bozuk oyuncak olarak hatta döner | 4.4 | 0.5 |
| 4.8 | Kadro −15 moral → yemekhane talebi | 2.6, 4.3 | 0.3 |
| 4.9 | Günlük giriş sayacı + etkinlik iskeleti | 4.1 | 0.6 |
| 4.10 | Dalga tasarımı + zorluk eğrisi | 4.2 | 1.5 |
| 4.11 | **Kısayol denetimi:** battle'sız ilerleme hızı ölçümü | hepsi | 1.0 |

**4.11 planın en önemli maddelerinden:** Battle oynamayan bir hesapla oynayan
bir hesap 14 gün paralel koşturulur. Hedef oran **1.8×–2.2×**. 2.5×'in üstü
"battle zorunlu oldu" demektir → Hurdalık hızlanır.

---

## 8. Faz 5 — Yumuşak lansman · 4–6 hafta · ~10 adam-hafta

| # | İş | Efor |
|---|---|---|
| 5.1 | Mağaza build'i, sarmalayıcı, cihaz matrisi | 2.0 |
| 5.2 | Analitik + kohort raporlama | 1.0 |
| 5.3 | Reklam SDK + ödüllü reklam yerleşimleri | 1.5 |
| 5.4 | Mağaza ekonomisi (paket, kaynak, hızlandırma) | 1.5 |
| 5.5 | Ses tasarımı (§18 #23) | 1.0 |
| 5.6 | Yerelleştirme iskeleti | 0.5 |
| 5.7 | UA kampanyası + iterasyon | 2.5 |

**Ödüllü reklam kuralı:** Reklam **moral satmaz.** Yemekhane'nin %30'luk bandı
oynanarak kazanılır; reklam yalnızca kaynak/hızlandırma tarafında durur. Aksi
halde Faz 2'de kurulan tek gerçek aktif-oyun sebebi çöker.

---

## 9. Motor kararı

Planın en büyük çatalı. Mevcut build **web** (DOM + canvas, bağımlılıksız).

| | Web (mevcut) | Unity |
|---|---|---|
| Faz 1'e varış | **Çok hızlı** — kod tabanı hazır | Yavaş — sıfırdan kurulum |
| 60 fps, çok sprite | Riskli | **Güçlü** |
| **Faz 4 combat** | **Zayıf** | **Güçlü** |
| Mağaza dağıtımı | Sarmalayıcı gerekir | **Yerel** |
| Yaratıcı test | Anında link | Build gerekir |
| Reklam SDK / analitik | Zahmetli | **Standart** |

**Öneri: Faz 1 web'de, KAPI 1 sonrası Unity'ye geç.** Gerekçe: KAPI 1'in
sorusu ("darboğaz okunuyor mu") **tamamen tasarım sorusu** — motorla ilgisi
yok ve mevcut kod oraya en hızlı varır. KAPI 1 geçilirse Faz 2 Unity'de
kurulur; Faz 1 kodu baştan **atılacak** ilan edilir.

Bedel: Faz 2 başında ~1 hafta kurulum. Kazanç: yanlış türe 4 ay harcamama.

> Ekip Unity'de belirgin şekilde hızlıysa Faz 1 de Unity'de yapılabilir;
> takvim ~1 hafta uzar, Faz 2 kurulumu düşer. Karar ekip aşinalığına bağlı ve
> **Faz 0'da yazılı olarak** verilmeli.

---

## 10. Paralel iş — yaratıcı test

Pano bunu genre kilidinden **önce** istiyordu; kilit verildi ama test yine de
Faz 1 ile **paralel** koşmalı — sonucu Faz 2 kapsamını belirler.

| # | İş | Efor |
|---|---|---|
| 10.1 | 3–5 statik konsept: Cute→Psycho dönüşümü, tamirhane kaosu, psycho işçi | 0.5 |
| 10.2 | $500–1.500 bütçeyle test (Meta / TikTok) | 0.3 |
| 10.3 | Sonuç okuma: **CPI ve IPM** birincil, CTR ikincil | 0.2 |

**Kıyas ölçütü:** Pano casual ortalamasını Android **$0.14**, iOS **$1.41**
olarak veriyor. Bunun belirgin altına inemiyorsak hook zayıf demektir.

---

## 11. Sanat üretim listesi

En büyük maliyet kalemi ve en uzun teslim süresi olan taraf.

### Faz 1 — Tamirhane (üretim kalitesi)

| Varlık | Adet | Efor |
|---|---|---|
| Tamirhane sahnesi (izometrik, 4 istasyon) | 1 | **2.0** |
| Bozuk / onarılmış oyuncak · 2 hasar tipi görünümü | 5 tür × 3 hâl | 1.2 |
| Karakter animasyonları — **5 karakter × 4 durum** | 20 set | **2.0** |
| Efekt: duman, kıvılcım, psycho aurası, sevkiyat | — | 0.8 |
| UI: panel çerçevesi, HUD, baloncuklar | — | 1.0 |

### Faz 2 — Yemekhane

| Varlık | Adet | Efor |
|---|---|---|
| Mutfak + yemekhane salonu | 1 | 1.5 |
| Yemek: ham / pişmiş / tabaklı / yanmış | 4 × 4 | 0.8 |
| Karakter: oturma + yeme durumu | 5 × 2 | 0.6 |

### Faz 3 — Genişleme

| Varlık | Adet | Efor |
|---|---|---|
| Şehir sahnesi + 5 bina × 3 seviye görünümü | — | 2.5 |
| Bölge inşaat aşamaları | 5 bölge × 3 | 1.5 |

### Faz 4 — Battle

| Varlık | Adet | Efor |
|---|---|---|
| Battle arenası | 1 | 1.0 |
| Düşman: 3 tip × (yürü / saldır / öl) | 9 set | 1.5 |
| Karakter: savaş durumu | 5 × 2 | 0.8 |

### Karakter kapsamı — dikkat

9 karakter × 6 durum = **54 animasyon seti** olur, kapsam patlar.

**Karar: 5 karakterle başla** (Pofu, Şefo, Vako, Mırmır, Çako — dört
istasyon yatkınlığı + bir serbest). Diğer 4'ü Faz 3'te bölge açılışlarıyla
gelir. Faz 1 animasyon yükü **20 sete** iner.

---

## 12. Karar kapıları

### KAPI 1 — Faz 1 sonu · "Darboğaz okunuyor mu?"

| Ölçüt | Eşik |
|---|---|
| Ekran görüntüsü testi | Arayüz kırpılmış görüntüden darboğaz **bulunabiliyor** |
| 30 saniye testi | Oyunu hiç görmemiş kişi doğru istasyonu gösteriyor: ≥ %70 |
| İç test | En az 8 kişi, her biri 3 oturum |
| Kendiliğinden dönüş | 2. oturumu **hatırlatmasız** başlatan: ≥ %50 |
| Hareketli darboğaz | Oyuncu hasar tipine göre atamayı değiştiriyor mu |
| Yaratıcı test CPI | Hedef aralığın içinde (§10) |
| JS/çalışma hatası | **0** |

Geçemezse: darboğaz **görsel dili** mi zayıf, yoksa mekanik mi sığ — ayırt et.
İkincisiyse Yemekhane'yi (TM) çekirdeğe terfi ettirmek yedek plandır; sahne
dışında her şey ortak.

### KAPI 2 — Faz 2 sonu · "Aktif oyun tutuyor mu?"

| Ölçüt | Eşik |
|---|---|
| D1 retansiyon | ≥ %35 |
| D7 retansiyon | ≥ %12 |
| Oturum/gün | ≥ 2 |
| **Yemekhane oynayan ÷ oynamayan D7** | **≥ 1.4×** |
| Ortalama moral | 65–85 bandında (100'e yapışmıyor) |

Ortadaki satır bu fazın **varlık sebebidir.** 1.4× çıkmazsa yemekhane bir
zaman hırsızıdır; mekanik değil, bağ yanlıştır.

### KAPI 3 — Faz 3 sonu · "Ekonomi 14 gün ayakta mı?"

| Ölçüt | Eşik |
|---|---|
| 14 günlük ilerleme | Tavana vurma **yok**, tıkanma **yok** |
| Kaynak dengesi | Hiçbir kaynak sürekli tavanda / sürekli sıfırda değil |
| Bölge açılış temposu | `LUUPIE-SPEC.md` §14 hedeflerinin ±%30'u |
| D14 retansiyon | ≥ %6 |
| Enflasyon | Koleksiyon sink'i fazla üretimi soğuruyor mu |

### KAPI 4 — Faz 4 sonu · "Battle kilitlemiyor mu?"

| Ölçüt | Eşik |
|---|---|
| Battle'lı ÷ battle'sız ilerleme | **1.8×–2.2×** |
| Battle oynamayanın D14 | Oynayanın %80'inden az değil |
| Ekipman kilidi | Sipariş tamamlama süresini ≤ %25 uzatıyor |

### KAPI 5 — Faz 5 · "Ekonomi para kazanıyor mu?"

| Ölçüt | Eşik |
|---|---|
| D30 ROAS | **Gerçekçi hedef: iOS ~%47, Android ~%15 civarı** |
| ARPDAU | Bütçe modeline göre |
| Reklam gösterimi/oturum | Türe uygun aralıkta |

> %150 net ROAS **planlama varsayımı olarak kullanılmasın** — panonun kendi
> uyarısı. Bütçe gerçek aralığa göre kurulmalı.

---

## 13. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| **Hareketli darboğaz sığ çıkar** | Çekirdek fikir çöker | KAPI 1'de ölçülür, sonraya bırakılmaz |
| **Sanat kapsamı patlar** | Takvim ×2 | 5 karakterle başla; §11 kararı |
| **Malzeme bollaşır** | Yemekhane bedava buff olur | KAPI 2'de "ortalama moral 65–85" ölçütü |
| **Battle fiilen zorunlu olur** | Yan oyun ana oyunu rehin alır | KAPI 4'te 1.8×–2.2× bandı; Hurdalık ayarlanır |
| **Motor kararı gecikirse** | Faz 2'de yeniden yazım | Faz 0'da kapatılır, ertelenmez |
| **Prototip kodu üretime taşınmak istenir** | Teknik borç | Faz 1 kodu **atılacak** ilan edilsin |
| **Reklam moral satmaya başlar** | Aktif oyun sebebi ölür | §8 kuralı sözleşme gibi tutulur |
| **Faz 4'e hiç gelinemez** | Yatırım boşa | Faz 1 tek başına yayınlanabilir tasarlandı |

---

## 14. İlk iki hafta — somut

**1. hafta**
1. Motor kararı toplantısı → **yazılı** karar *(0.1)*
2. Bloke hata düzeltilir, build oynanır hâle gelir *(0.2)*
3. Sanat: tamirhane anahtar karesi *(0.3)*
4. Telemetri olay listesi yazılır *(0.4)*
5. Yaratıcı test konseptleri brief'i *(10.1)*

**2. hafta**
6. Bozuk oyuncak girdi modeli kodlanır *(1.2)*
7. İstasyon adları + ikonlar *(1.1)*
8. Tampon durma kuralı *(1.4)*
9. Yaratıcı test yayına alınır *(10.2)*

İki hafta sonunda elde: **bozuk oyuncakların gerçekten aktığı, tamponu dolunca
duran bir hat** ve **yayında bir yaratıcı test**.

---

## 15. Özet tablo

| Faz | Süre | Efor (kod) | Efor (sanat) | Çıktı | Kapı |
|---|---|---|---|---|---|
| 0 · Kilit | 1 hf | 1.5 | 0.5 | Motor kararı, çalışan build, test yayında | — |
| 1 · Tamirhane | 4–5 hf | ~11 | ~7 | **Yayınlanabilir idle oyun** | Darboğaz okunuyor mu |
| 2 · Yemekhane | 2–3 hf | ~6 | ~3 | Aktif katman, %30 moral bandı | Aktif oyun tutuyor mu |
| 3 · Genişleme | 3–4 hf | ~8 | ~4 | Gerçek kaynak ekonomisi, 4 hasar tipi | 14 gün ayakta mı |
| 4 · Battle | 4–5 hf | ~12 | ~3.5 | Survivor yan mod | Kilitlemiyor mu |
| 5 · Lansman | 4–6 hf | ~10 | ~1 | Mağaza build'i, UA | ROAS |

**Toplam ≈ 48 adam-hafta kod + 19 adam-hafta sanat.**
Üç kişilik ekiple **Faz 1 yayınına ~6 hafta**, tam yumuşak lansmana **~5–6 ay**.

Sanat en dar boğaz; karakter animasyon kapsamı (§11) kontrol altında
tutulursa takvim tutar.
