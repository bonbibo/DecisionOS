# Luupie — Üretim Planı

Üç katmanlı mimarinin (`OYUN-MIMARISI.md`) faz haritası, iş paketleri, sanat
listesi ve karar kapıları.

Efor **adam-hafta** cinsinden verilir; takvim ekip büyüklüğüne göre değişir.
Referans takvim **1 geliştirici + 1 sanatçı + yarım zamanlı tasarım** varsayar.

> 🔁 **Aynı işin akışa göre kesilmiş hâli:** `ISLEYIS-PLANI.md` — hangi
> davranış ne zaman gerçek olur, çalıştığı nasıl anlaşılır, neden o sırada.
> Bu doküman *ne kadar sürer*, o doküman *ne çalışır* sorusunu yanıtlar.

> ⚙️ **Motor kararı verildi: oyun baştan sona Unity'de yazılacak.** Web
> prototipi ürün değil; §9'da tanımlanan üç işi görür ve orada kalır.
> Ara geçiş, yeniden yazım veya çift kod tabanı **yoktur**.

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
FAZ 0          FAZ 1            FAZ 2         FAZ 3          FAZ 4        FAZ 5
Unity iskelet→ Tamirhane    →   Yemekhane →   Genişleme  →   Battle   →   Yumuşak
2 hf           6–7 hf           2–3 hf        3–4 hf         4–5 hf       lansman
               ▲                ▲             ▲              ▲            4–6 hf
            KAPI 1           KAPI 2        KAPI 3         KAPI 4
          "darboğaz        "aktif oyun   "ekonomi       "battle
           okunuyor mu"     tutuyor mu"   14 gün         kilitlemiyor
                                          ayakta mı"      mu"
```

Her kapı **geçilemezse durulur veya yön değişir**. Kriterler §12'de.
Mimari aşamalarıyla eşleşme: Aşama 1 → Faz 1 · Aşama 2 → Faz 2 ·
Aşama 3 → Faz 3 · Aşama 4 → Faz 4.

---

## 3. Faz 0 — Unity iskeleti · 2 hafta · ~3.5 adam-hafta

Motor kararı verildiği için Faz 0 artık bir "karar haftası" değil, **temel
atma** haftası. Buradaki her madde Faz 1–4'ün üstüne bineceği zemin; sonradan
değiştirilmesi pahalı olan şeyler burada kilitlenir.

| # | İş | Efor | Not |
|---|---|---|---|
| 0.1 | Unity projesi + sürüm kilidi + repo/LFS/CI | 0.4 | §9.1 |
| 0.2 | **Simülasyon tick mimarisi** (10 Hz, offline ile ortak kod yolu) | 1.0 | §9.2 — en kritik madde |
| 0.3 | **ScriptableObject veri katmanı** — hiçbir denge sayısı kodda değil | 0.8 | §9.3 |
| 0.4 | İzometrik sahne iskeleti: sıralama, kamera, çözünürlük/güvenli alan | 0.6 | §9.4 |
| 0.5 | Sprite atlası + mevcut PNG'lerin içe aktarım hattı | 0.3 | §9.5 |
| 0.6 | Kayıt/yükleme + çevrimdışı zaman doğrulaması | 0.4 | §9.6 |
| 0.7 | Telemetri olay şeması (kapılar buradan ölçülecek) | 0.2 | — |
| 0.8 | Sanat stili kilidi: tamirhane anahtar karesi | *(sanat)* | Faz 1 ile paralel |
| 0.9 | Web prototipinde bloke hatayı düzelt — **yalnız referans/test için** | 0.2 | §9.7 |

**Çıktı:** Boş ama doğru kurulmuş bir Unity projesi — içinde tek bir istasyon
10 Hz'de tikliyor, verisi ScriptableObject'ten geliyor, uygulamayı kapatıp
açınca çevrimdışı geçen süre doğru işleniyor.

**Faz 0'ın kabul testi:** Uygulamayı kapat, cihaz saatini 3 saat ileri al, aç.
İstasyon **canlı çalışmış gibi** aynı sonucu vermeli. Bu tek test, idle bir
oyunun en pahalı hatasını (çevrimdışı ile çevrimiçi matematiğin ayrışması)
başta yakalar.

---

## 4. Faz 1 — Tamirhane çekirdeği · 6–7 hafta · ~14 adam-hafta

**Tek soru:** *Oyuncu hattaki darboğazı gözle bulup düzeltebiliyor ve buna
geri dönüyor mu?*

Yemekhane yok, şehir yok, battle yok. Kaynaklar sabit oranla akar, kantin rafı
morali 60'ta tutar — **hat ×1.00'de dengeli çalışır.** Halka kapalı: bozuk
oyuncak gelir, onarılır, sevk edilir, para istasyona yatırılır.

> Bu faz Unity'de **sıfırdan** yazılır. Web prototipi kopyalanacak kod değil,
> okunacak şartname: hangi sayının ne yaptığı, hangi görsel dilin çalıştığı
> orada denenmiş durumda. `LUUPIE-SPEC.md` yetkili kaynak, prototip onun
> çalışan örneği.

### 1a — Ana oyun mekaniği

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 1.1 | Dört istasyon + bant + tampon (TEŞHİS·SÖKME·ONARIM·CİLA) | 0.2, 0.4 | 1.5 |
| 1.2 | **Bozuk oyuncak girdi modeli** — sonsuz hammadde yok | 1.1 | 0.8 |
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
| 1.13 | Karakter yürüme/çalışma davranışı + izometrik yol bulma | 0.4 | 1.0 |

### 1b — Ekran ve his

| # | İş paketi | Efor |
|---|---|---|
| 1.14 | UI iskeleti: Canvas Scaler, güvenli alan, üç ekran bölgesi (`LUUPIE-SPEC.md` §11) | 0.8 |
| 1.15 | Panel sistemi %66 × %90 + kaydırılabilir içerik (§18 #2, #20) | 0.5 |
| 1.16 | Yaşam alanı dokunulmazlığı — raycast katmanları ayrılır (§18 #3) | 0.4 |
| 1.17 | **Dönüş deltası koreografisi** — zorunlu | 0.5 |
| 1.18 | Sevkiyat kutlaması (§18 #4) | 0.5 |
| 1.19 | Mikro geri bildirim + ilerleme çubuğu (§18 #16, #18) | 0.5 |
| 1.20 | **İlk 10 dakika akışı** (`LUUPIE-SPEC.md` §16) | 1.0 |
| 1.21 | Cihaz matrisi ilk geçiş + performans profili | 0.5 |
| 1.22 | İç test turu + denge iterasyonu | 1.5 |

**Kritik yol:** 1.1 → 1.2 → 1.3 → 1.6 → 1.7. Hareketli darboğaz (1.3) en riskli
kalem — hasar tipi karışımı hattı gerçekten kaydırmıyorsa fikir çalışmıyor
demektir ve bunu **Faz 1'de** öğrenmek gerekir.

**Unity'nin buraya kattığı:** 1.13, 1.17, 1.18, 1.19 web'de en zorlanan
kalemlerdi (animasyon, tween, parçacık, sıralama). Unity'de bunlar hazır
sistemler; Faz 1'in "his" tarafı web'e göre daha ucuz, mekanik tarafı daha
pahalı. Net etki yaklaşık **+3 adam-hafta**.

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

## 7. Faz 4 — Battle · 4–5 hafta · ~10 adam-hafta

**Tek soru:** *Battle bir kısayol olarak kalıyor mu, yoksa fiilen zorunlu mu oldu?*

Üç katmanın en pahalısı — sıfırdan combat. **Motor kararının en çok karşılığını
verdiği faz burası:** dalga yönetimi, çarpışma, hedefleme, animasyon geçişleri
ve nesne havuzu Unity'de hazır sistemler.

| # | İş paketi | Bağımlılık | Efor |
|---|---|---|---|
| 4.1 | Battle sahnesi + dalga iskeleti | 3.8 | 1.2 |
| 4.2 | Düşman davranışı + 3 düşman tipi | 4.1 | 1.5 |
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

## 8. Faz 5 — Yumuşak lansman · 4–6 hafta · ~8 adam-hafta

| # | İş | Efor |
|---|---|---|
| 5.1 | Mağaza build'i (iOS + Android), imzalama, cihaz matrisi | 1.2 |
| 5.2 | Analitik + kohort raporlama | 1.0 |
| 5.3 | Reklam SDK (LevelPlay / AppLovin MAX) + ödüllü yerleşimler | 1.0 |
| 5.4 | Mağaza ekonomisi (paket, kaynak, hızlandırma) | 1.5 |
| 5.5 | Ses tasarımı (§18 #23) | 1.0 |
| 5.6 | Yerelleştirme iskeleti | 0.5 |
| 5.7 | UA kampanyası + iterasyon | 2.5 |

**Ödüllü reklam kuralı:** Reklam **moral satmaz.** Yemekhane'nin %30'luk bandı
oynanarak kazanılır; reklam yalnızca kaynak/hızlandırma tarafında durur. Aksi
halde Faz 2'de kurulan tek gerçek aktif-oyun sebebi çöker.

---

## 9. Unity mimarisi

**Karar: oyun baştan sona Unity.** Ara motor, geçiş fazı veya çift kod tabanı
yok. Bu bölüm Faz 0'da kurulacak zemini tanımlar — sonradan değiştirilmesi
pahalı olan her şey burada.

**Takasın açık hâli:** Faz 1'e varış web'e göre **~2–3 hafta geç**, ama
motor geçişi riski **sıfır**, Faz 4 combat'ı **~2 adam-hafta ucuz**, Faz 5
mağaza/SDK tarafı **~2 adam-hafta ucuz**. Toplam efor neredeyse aynı; fark
**riskin kaybolması.**

### 9.1 Sürüm ve paketler

| | Seçim | Gerekçe |
|---|---|---|
| Sürüm | **Unity 6 LTS** — tam sürüm Faz 0'da yazılı olarak sabitlenir | Faz 4'e kadar sürüm yükseltmesi yok |
| Render | **URP 2D** + 2D Renderer | Sprite ışıklandırma, tek geçişte mobil performans |
| Girdi | **Input System** | Çoklu dokunuş, mini oyunlardaki swipe eşikleri |
| UI | **UI Toolkit** (paneller) + Canvas (diegetic baloncuklar) | Paneller veri odaklı; baloncuklar sahneye demirli |
| Varlık | **Addressables** | Bölge sanatı Faz 3'te akışla gelir, ilk indirme şişmez |
| Depo | **Git + Git LFS** | Sprite atlasları ve ses ikili dosyalar |

Faz 5'e kadar **üçüncü parti eklenti alınmaz** (tween/kayıt/UI kütüphaneleri
dâhil). Tek istisna: reklam/analitik SDK'ları, Faz 5'te.

### 9.2 Simülasyon tick'i — planın teknik kalbi

Idle bir oyunun en pahalı hatası, çevrimiçi ve çevrimdışı matematiğin
ayrışmasıdır. Panzehir tek kural:

> **Tek bir `Simulate(deltaTime)` fonksiyonu vardır. Canlı oyun onu saniyede
> 10 kez çağırır; çevrimdışı dönüş onu hızlandırılmış olarak çağırır. Başka
> hiçbir yerde üretim hesabı yapılmaz.**

| | Kural |
|---|---|
| Tick | Sabit **10 Hz**, `Time.deltaTime`'dan bağımsız |
| Çevrimdışı | Aynı fonksiyon, blok blok ileri sarılır (tavan 4 saat) |
| Görsel | Bant, karakter, animasyon **kare hızında** akar — simülasyondan ayrı |
| Belirlilik | Aynı girdi = aynı çıktı; kare hızı sonucu değiştirmez |

Görsel katman simülasyonu **okur**, ona yazmaz. Bu ayrım Faz 0'da kurulmazsa
Faz 3'teki 14 günlük ekonomi doğrulaması (3.11) yapılamaz hâle gelir.

### 9.3 Veri katmanı — hiçbir denge sayısı kodda değil

`LUUPIE-SPEC.md`'deki her sayı **ScriptableObject** olarak yaşar: istasyon
hızları, upgrade matrix altı parametresi, moral düşüş hızları, kantin rafı
verimi, sipariş primleri, hasar tipi ağırlıkları, bina üretim eğrileri.

Sebep tek: tasarımcı dengeyi geliştirici olmadan çevirebilmeli, ve 14 günlük
simülasyon (3.11) aynı verinin üzerinden koşabilmeli. Sabit sayı yazılmış her
yer, ileride bir denge iterasyonunun bloke olduğu yerdir.

### 9.4 İzometrik sahne

| | Seçim |
|---|---|
| Projeksiyon | Ortografik kamera, sprite tabanlı sahte izometri (Tilemap değil) |
| Sıralama | **Özel eksen sıralaması** (`Custom Axis Sort` Y+Z) — karakterler makinelerin önünden/arkasından geçebilmeli |
| Referans çözünürlük | **1920 × 886** (932 × 430 tasarımının 2×'i), yalnız **yatay** |
| Güvenli alan | Çentik/ada dinamik okunur; köşe kromu ona demirlenir |
| Kural | `LUUPIE-SPEC.md` §11 — yaşam alanına arayüz giremez; ayrı raycast katmanı ile zorlanır |

Sahte izometri seçilmesinin sebebi mevcut sanat: karakterler ve fabrika zaten
elde çizilmiş izometrik sprite'lar. Tilemap gerçek bir grid dayatır ve bu
sanatı yeniden üretmeyi gerektirirdi.

### 9.5 Sprite hattı

`tools/extract_sprites.py` **korunuyor** — karakter sayfasından PNG üreten
tekrarlanabilir hat o. Unity tarafında çıktılar **Sprite Atlas**'a girer
(karakter atlası / makine atlası / UI atlası ayrı).

Animasyon: kare kare sprite sheet. Faz 1'de 5 karakter × 4 durum = 20 set
(`§11`). İskeletsel animasyona (Spine vb.) **girilmiyor** — sanat stili kare
kareye uygun ve ek lisans/eğitim maliyeti taşımıyor.

### 9.6 Kayıt ve çevrimdışı

| | Kural |
|---|---|
| Format | JSON, sürümlenmiş şema, ileri uyumlu okuma |
| Yazma | Atomik (geçici dosya + taşıma) — yarım kayıt olmaz |
| Zaman | Cihaz saati **doğrulanır**; ileri alma tespit edilirse kazanç verilmez |
| Tavan | 4 saat (`LUUPIE-SPEC.md` §17 offline tavanı) |
| Bulut | Faz 5'te; Faz 1–4 yerel |

### 9.7 Web prototipinin yeni rolü

Prototip **ürün değil** ama atılmıyor da. Üç işi var:

| İş | Ne zaman |
|---|---|
| **Şartname referansı** | Sürekli — hangi sayının ne yaptığı ve hangi görsel dilin çalıştığı orada denenmiş |
| **Yaratıcı test malzemesi** | §10 — ekran görüntüsü ve video üretebiliyor, Unity build'ini beklemez |
| **Oynanabilir demo** | Yatırımcı/ekip gösterimi; link yeterli, kurulum gerekmez |

Bunun için Faz 0'daki tek bakım işi kalıyor: **bloke hatayı düzelt** (0.9).
Ondan sonra prototibe kod eklenmez.

> ⚠️ **Kural:** Prototip kodu Unity'ye **taşınmaz**. Referans olarak okunur,
> kopyalanmaz. Aksi hâlde JavaScript'in yapısal alışkanlıkları C#'a sızar ve
> §9.2'deki tick mimarisi baştan bozulur.

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
| **Performans** | Hedef cihazda **60 fps**, 10 karakter + 4 istasyon aktifken |
| **Çevrimdışı tutarlılığı** | 4 saatlik dönüşün sonucu, canlı koşturmayla **birebir** aynı |
| Çalışma hatası | **0** |

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
| **Simülasyon ile görsel iç içe geçer** | Çevrimdışı ≠ çevrimiçi; ekonomi doğrulanamaz | §9.2 tek `Simulate()` kuralı; Faz 0 kabul testi |
| **Denge sayıları koda sızar** | Her iterasyon geliştirici ister, 3.11 bloke olur | §9.3 ScriptableObject kuralı; kod incelemesinde aranır |
| **Prototip kodu Unity'ye taşınır** | JS alışkanlıkları mimariyi bozar | §9.7 — referans olarak okunur, kopyalanmaz |
| **Unity kurulumu Faz 1'i yer** | İlk yayın gecikir | Faz 0 ayrı fazlandı (2 hf); Faz 1 kurulumla uğraşmaz |
| **Sürüm/paket yükseltmesi ortada gelir** | Kırılma, kayıp gün | Faz 0'da sürüm kilidi; Faz 4'e kadar yükseltme yok |
| **Reklam moral satmaya başlar** | Aktif oyun sebebi ölür | §8 kuralı sözleşme gibi tutulur |
| **Faz 4'e hiç gelinemez** | Yatırım boşa | Faz 1 tek başına yayınlanabilir tasarlandı |

---

## 14. İlk iki hafta — somut

**1. hafta — proje ayağa kalkar**
1. Unity projesi kurulur, sürüm yazılı olarak sabitlenir, repo + LFS + CI *(0.1)*
2. **`Simulate(deltaTime)` iskeleti**: tek istasyon, 10 Hz, kare hızından bağımsız *(0.2)*
3. Denge verisi ScriptableObject'e taşınır — istasyon hızı koda yazılmaz *(0.3)*
4. Sanat: tamirhane anahtar karesi başlar *(0.8)*
5. Web prototipindeki bloke hata düzeltilir — demo/test malzemesi olarak *(0.9)*

**2. hafta — zemin kapanır**
6. İzometrik sahne: kamera, özel eksen sıralaması, güvenli alan *(0.4)*
7. Sprite atlası + mevcut PNG'lerin içe aktarımı *(0.5)*
8. Kayıt/yükleme + çevrimdışı ileri sarma, **aynı `Simulate()` üzerinden** *(0.6)*
9. Telemetri olay şeması yazılır *(0.7)*
10. Yaratıcı test yayına alınır *(10.1, 10.2)*

**İki hafta sonunda elde:** Tek istasyonun 10 Hz'de tiklediği, verisini
ScriptableObject'ten okuyan, kapatıp açınca çevrimdışı süreyi doğru işleyen
bir Unity projesi — ve yayında bir yaratıcı test.

Az görünebilir; öyle değil. Bu iskelet doğru kurulursa Faz 1–4'ün tamamı onun
üzerine **eklenerek** gelir. Yanlış kurulursa Faz 3'te fark edilir ve orada
düzeltmenin bedeli haftalarla ölçülür.

---

## 15. Özet tablo

| Faz | Süre | Efor (kod) | Efor (sanat) | Çıktı | Kapı |
|---|---|---|---|---|---|
| 0 · Unity iskeleti | 2 hf | ~3.5 | ~0.5 | Tick + veri + sahne + kayıt zemini | Çevrimdışı = çevrimiçi |
| 1 · Tamirhane | 6–7 hf | ~14 | ~7 | **Yayınlanabilir idle oyun** | Darboğaz okunuyor mu |
| 2 · Yemekhane | 2–3 hf | ~6 | ~3 | Aktif katman, %30 moral bandı | Aktif oyun tutuyor mu |
| 3 · Genişleme | 3–4 hf | ~8 | ~4 | Gerçek kaynak ekonomisi, 4 hasar tipi | 14 gün ayakta mı |
| 4 · Battle | 4–5 hf | ~10 | ~3.5 | Survivor yan mod | Kilitlemiyor mu |
| 5 · Lansman | 4–6 hf | ~8 | ~1 | Mağaza build'i, UA | ROAS |

**Toplam ≈ 50 adam-hafta kod + 19 adam-hafta sanat.**
Üç kişilik ekiple **Faz 1 yayınına ~8–9 hafta**, tam yumuşak lansmana
**~6–7 ay**.

### Web planına göre fark

| | Web-önce | **Full Unity** |
|---|---|---|
| Faz 1 yayını | ~6 hafta | **~8–9 hafta** |
| Toplam kod eforu | ~48 a-hf | ~50 a-hf |
| Motor geçişi riski | 1 hafta + yeniden yazım | **Yok** |
| Faz 4 combat | ~12 a-hf | **~10 a-hf** |
| Faz 5 mağaza/SDK | ~10 a-hf | **~8 a-hf** |
| 60 fps garantisi | Riskli | Ölçülebilir |

İlk yayın 2–3 hafta gecikiyor, karşılığında **bir motor geçişi ve onun
getireceği yeniden yazım tamamen ortadan kalkıyor.** Faz 4'e gidilecekse bu
takas her koşulda kârlı.

Sanat hâlâ en dar boğaz; karakter animasyon kapsamı (§11) kontrol altında
tutulursa takvim tutar.
