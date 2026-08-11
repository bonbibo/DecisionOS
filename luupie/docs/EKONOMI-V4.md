# Luupie — Ekonomi V4

> ⚠️ **Bu doküman `LUUPIE-SPEC.md` içinde birleştirildi.**
> Tek yetkili tasarım dokümanı odur; bu dosya tarihsel kayıt olarak duruyor.

**Karar:** Oyun Luupie olarak kalır (yatay izometrik üretim hattı, karakterler,
darboğaz okuması). **Ekonomi** `Ponchics Mobile Game Mechanics` dokümanından
alınır ve hat oyununa uyarlanır.

Bu doküman `CEKIRDEK-DONGU.md`'nin ekonomi bölümünü günceller. Arayüz
kuralları (`EKRAN-MODELI-V3.md`) aynen geçerli.

---

## 1. Ne alındı, ne alınmadı

| Ponchics'ten | Karar | Gerekçe |
|---|---|---|
| Üç kaynak (Wool / Oil / Mine) | ✅ **Alındı** | Hattın girdisi "HAMMADDE (sonsuz)" olmaktan çıkıp gerçek bir kısıt olur |
| Depo limiti + dolunca durma | ✅ **Alındı** | Zaten tampon olarak var; "tıkalı istasyon" eksiğini de kapatır |
| Upgrade matrix (6 parametre) | ✅ **Aynen alındı** | Elimizdeki en temiz ayar çerçevesi |
| Merge: 3 aynı / 5 karışık → üst seviye | ✅ **Alındı** | Hatta kalite/değer katmanı ekler |
| Geri dönüşüm (alt seviye / enerji / kaynak) | ✅ **Alındı** | Hatalı karara karşı emniyet valfi |
| Görev listesi | ✅ **Alındı** | Vardiya günlüğü genişler |
| Enerji | ⚠️ **Rolü değişti** | Duvar değil, **overdrive yakıtı** (bkz. §6) |
| HORN → NFT | ⚠️ **Yapı alındı, yükü değişti** | Üst seviye çıkış kapısı korunur; çıktının zincir üstü NFT mi koleksiyon mu olduğu ekonomiyi değiştirmez (bkz. §9) |
| Bina yerleştirme haritası | ❌ Alınmadı | Luupie'nin ana ekranı hat; kaynak binaları Şehir sekmesine oturur |
| CIRCUS (şans tesisi) | ❌ Alınmadı | 7+ hedef kitle ve mağaza politikalarıyla ayrı ele alınmalı |

---

## 2. Katman haritası

```
  ŞEHİR                    FABRİKA                      SİPARİŞ
  ┌──────────┐            ┌───────────────────────┐    ┌─────────┐
  │ WOOL     │──┐         │ PRESS→STITCH→PAINT→   │    │ L1 ×8   │
  │ OIL      │──┼────────▶│ PACK                  │───▶│ L2 ×4   │──▶ ● COIN
  │ MINE     │──┘         │ çıktı: L1 oyuncak     │    │ L3 ×2   │
  └──────────┘            └───────────┬───────────┘    └─────────┘
   depo dolar,                        │                      ▲
   durur, toplanır              ┌─────▼─────┐                │
                                │ BİRLEŞTİR │────────────────┘
                                │ 3 aynı /  │
                                │ 5 karışık │
                                └─────┬─────┘
                                      │ L3
                                ┌─────▼──────┐
                                │ KOLEKSİYON │  (HORN eşdeğeri)
                                └────────────┘

  ⚡ ENERJİ ──▶ istasyon overdrive (×2, 30 sn)
  ♻ GERİ DÖNÜŞÜM ──▶ oyuncak → alt seviye / enerji / kaynak
```

**Tek satırla:** Şehir kaynak üretir → hat kaynağı L1 oyuncağa çevirir →
birleştirme değeri katlar → sipariş **tek para kaynağıdır** → coin hattı ve
şehri büyütür.

---

## 3. Kaynaklar ve depo kuralı

Üç kaynak, her biri Şehir'de bir bina:

| Kaynak | Bina | Başlangıç üretim | Periyot | Maks seviye |
|---|---|---|---|---|
| 🧶 Wool | Yün Çiftliği | 45 | 40 sn | 50 |
| 🛢 Oil | Yağhane | 35 | 40 sn | 50 |
| ⛏ Mine | Maden | 28 | 40 sn | 50 |

Ponchics'in kuralları aynen:

1. **Bina depo miktarına kadar üretir, sonra durur.**
2. **Oyuncu toplayana kadar kaynak fabrikaya gitmez.**
3. **Seviye yükseltme sırasında bir alt seviyeden üretim devam eder.**

Aynı kural hatta da geçerli ve zaten eksikti: **çıktı tamponu dolan istasyon
durur.** Yani sevk etmezsen PACK tıkanır, PACK tıkanınca PAINT tıkanır, zincir
geriye doğru kilitlenir. Sevkiyat artık isteğe bağlı değil, **hattı açan
eylem**.

> Bu, test raporu 03'teki "45 saniyede kilitleniyor" durumunu hatadan
> **tasarıma** çevirir — sipariş düğmesi erişilebilir olduğu anda.

Her istasyonun girdi ihtiyacı (L1 oyuncak başına):

| İstasyon | Wool | Oil | Mine |
|---|---|---|---|
| PRESS | 3 | 1 | — |
| STITCH | 2 | — | 1 |
| PAINT | — | 2 | 2 |
| PACK | 1 | 1 | 1 |

Bir istasyon kaynağı olmadığında **aç kalır** — mevcut "aç kalma" görsel dili
zaten bunu anlatıyor, artık gerçek bir sebebi olur.

---

## 4. Upgrade matrix

Ponchics'in altı parametresi aynen alınır ve her istasyona + her kaynak
binasına uygulanır:

| Parametre | Ne yapar |
|---|---|
| `STARTER` | Seviye 1'deki üretim miktarı |
| `PRODUCTION` | Seviyeye bağlı üretim oranı |
| `UPGRADE MATRIX` | Seviyeye bağlı **logaritmik** artan üretim çarpanı |
| `UPGRADE MULTIPLIER` | Yükseltme maliyetinin artış çarpanı |
| `PRODUCTION LIMIT` | Depo/tampon üst sınırı |
| `TIME MULTIPLIER` | Yükseltme ve enerji üretim sürelerinin seviyeye bağlı değişimi |
| `DEPOT MULTIPLIER` | Depo miktarının üretim oranına bağlı hesabı |

Başlangıç sabitleri (Ponchics tablosundan):

| Bina tipi | Maks seviye | Up Mltp | Time Mltp |
|---|---|---|---|
| Kaynak binaları | 50 | 0.22 | 0.11 |
| Hat istasyonları | 16 | 0.22 | 0.11 |
| Koleksiyon kasası | 8 | 0.41 | 0.33 |

**Kritik kural:** `UPGRADE MULTIPLIER > UPGRADE MATRIX`. Maliyet üretimden
hızlı büyür — yoksa tek istasyona sonsuz yatırım optimal olur ve darboğaz
oyunu ölür.

Mevcut yükseltme paneli bu matrisi zaten doğru gösteriyor
(`MEVCUT 3.9 sn → SONRA 3.3 sn · YÜKSELT 120 ●`); sadece arkasındaki formül
bu tabloya bağlanacak.

---

## 5. Birleştirme (merge)

Hat **yalnızca Seviye 1 oyuncak** üretir. Değer birleştirmeden gelir.

| Kural | Değer |
|---|---|
| Aynı türden **3** oyuncak | → 1 üst seviye, **aynı tür** |
| Karışık türden **5** oyuncak | → 1 üst seviye, **rastgele tür** |
| Maksimum seviye | 3 |
| Depo limiti | Tüm seviyeler toplam 100 |

Türler karakterlere bağlanır — Pofu Ayıcık, Mırmır Kedisi, Şefo Domuzu…
Böylece koleksiyon hissi karakter kadrosuyla aynı dili konuşur.

**Neden hat L1 üretiyor:** Üretim hızı (darboğaz oyunu) ile ürün değeri (merge
oyunu) birbirinden ayrılır. Hızlı hat çok L1 verir; akıllı oyuncu onları L3'e
çıkarıp aynı emekle 1.7 katı kazanır. İki farklı beceri, tek ekonomi.

---

## 6. Enerji — duvar değil, yakıt

**Bu tek sapma bilinçli.** İlk konsept dokümanı enerjiyi açıkça reddediyordu:
*"Enerji sistemi yoktur. Oyuncuyu geri getiren 'duvar' değil, dolan kova
merakıdır."* Ponchics ise enerjiyi üretim kapısı yapıyor.

Uzlaşma: **enerji üretimi engellemez, hızlandırır.**

| | Nasıl |
|---|---|
| Kazanılır | Zamanla dolar (fabrika seviyesine bağlı tavan) + geri dönüşümden |
| Harcanır | Bir istasyonu **30 sn boyunca ×2** çalıştırmak: **10 enerji** |
| Tavan | Fabrika seviyesi × 20 |

Ve bu, Psycho sistemine tam oturur — **iki hızlanma yolu, biri riskli ve
bedava, diğeri güvenli ve maliyetli:**

| Yol | Hız | Bedel | Risk |
|---|---|---|---|
| ⚡ Enerji overdrive | ×2 | 10 enerji | Yok |
| 💢 Psycho | ×2 | Bedava | Ürünün %18'i hatalı, paketlemeyi tıkar |

Oyuncu her darboğazda seçim yapar. "Cute Meets Crazy" ikiliği ilk kez
ekonomik bir karara dönüşür.

---

## 7. Geri dönüşüm

Ponchics'in üç kuralı aynen — Fabrika'da **Sökme Tezgahı**:

| Dönüşüm | Sonuç |
|---|---|
| Alt seviyeye | Seviye N → 3× Seviye N−1 (rastgele tür), enerji harcanır |
| Enerjiye | Seviye N → 1× Seviye N−1 + **enerji deposu dolar** |
| Kaynağa | Seviye N → 1× Seviye N−1 + yükseltmede harcanan kaynak iade |

Bu, oyunun emniyet valfi: yanlış türde birleştirme yapan oyuncu tıkanıp
kalmaz. Idle oyunlarda en sık bırakma sebebi "elimde işe yaramaz yığın var"
hissidir; bu üç kural onu ortadan kaldırır.

---

## 8. Sipariş ekonomisi

Sipariş **tek para kaynağı** olarak kalır. Yenilik: istenen **seviye**.

| Sipariş | İçerik | Ödeme | Ham değere göre |
|---|---|---|---|
| Standart | 8 × L1 | 160 ● | — |
| Kaliteli | 4 × L2 | 480 ● | 12 L1 eder → **+33% prim** |
| Butik | 2 × L3 | 1.100 ● | 18 L1 eder → **+53% prim** |
| Acele | 6 × L1, yarı süre | 290 ● | **+81%**, kaçarsa kaybolur |

Prim, birleştirmeye harcanan zamanın karşılığıdır. Oyuncu her turda seçer:
hızlı ve ucuz mu, yavaş ve değerli mi?

Aynı anda **bir aktif + bir sıradaki** sipariş kuralı korunur.

---

## 9. Koleksiyon kasası (HORN eşdeğeri)

3 × Seviye 3 aynı tür → o türün **nadir koleksiyon parçası**.
5 karışık L3 → rastgele nadir parça.

- Üretim süresi uzun (başlangıç 1200 sn), maks seviye 8, enerji harcar
- Çıktı oyuna geri girmez — **prestij ve kalıcı bonus** verir
  (her parça global üretim hızına kalıcı **+%2**)
- Mezunlar Albümü ile aynı vitrinde yaşar

> **Not:** Bu kasanın çıktısının zincir üstü NFT mi yoksa oyun içi koleksiyon
> parçası mı olduğu **ekonomiyi hiç değiştirmez** — akış, maliyet ve sink
> aynıdır. Zincir üstü tarafı isterseniz ayrı bir ürün/uyum başlığı olarak ele
> alalım; ekonomi bu kararı beklemeden ilerleyebilir.

---

## 10. Görevler

Ponchics'in görev listesi Vardiya günlüğü'ne eklenir:

- Bina seviye artırımı · İstasyon seviye artırımı
- Farklı seviyelerde **ilk** oyuncak üretimi
- Farklı seviyelerde **x adet** oyuncak üretimi
- Koleksiyon parçası üretimi
- Toplam kaynak üretimi / harcaması
- Toplam enerji harcaması

Ödüller: enerji deposunun yenilenmesi, kaynak, coin, plan.

---

## 11. Yeni çekirdek döngü

```
1. Şehre git, dolu kaynak depolarını topla        (10 sn)
2. Hattı oku: hangi istasyon aç, hangisi tıkalı   (5 sn)
3. Müdahale: işçi ata / overdrive ver / tamir et  (30-60 sn)
4. Biriken L1'leri birleştir → L2/L3              (20 sn)
5. Siparişi sevk et → coin                        (5 sn)
6. Coin'i darboğaza veya kaynak binasına yatır    (10 sn)
7. Çık — depolar dolmaya devam eder
```

**Geri dönme sebebi üçe çıkar:** dolan kaynak deposu, biten sipariş,
dolan enerji. Şu an tek sebep vardı ve o da 45 saniyede tükeniyordu.

---

## 12. Uygulama sırası

| # | İş | Not |
|---|---|---|
| 0 | **Sipariş düğmesini nav'ın altından çıkar** | Rapor 03; bu olmadan hiçbiri test edilemez |
| 1 | Üç kaynak + depo/dolunca durma kuralı | Hattın girdisi gerçek kısıt olur |
| 2 | Çıktı tamponu dolan istasyon **dursun** | Sevkiyatı zorunlu kılar; "tıkalı" görsel dili açılır |
| 3 | Upgrade matrix'i tabloya bağla | Mevcut panel hazır, arkası değişecek |
| 4 | Birleştirme paneli (3 aynı / 5 karışık) | Tam panel modeli, V3 çerçevesi |
| 5 | Sipariş seviyeleri + prim | Merge'e sebep verir |
| 6 | Enerji + overdrive | Psycho ile ikili yol |
| 7 | Geri dönüşüm (Sökme Tezgahı) | Emniyet valfi |
| 8 | Kaynak binaları Şehir sekmesine | Şehir ekonomik iş kazanır |
| 9 | Koleksiyon kasası + görev genişlemesi | Uzun yol |

---

## 13. Açık sorular

1. **Kaynak binaları Şehir'de mi, fabrikanın arkasında mı?** Şehir'i öneriyorum
   — sekmeye ekonomik iş verir. Alternatif: hattın solunda görünür silolar.
2. **Enerji tavanı neye bağlansın?** Fabrika seviyesi öneriyorum; Ponchics'te
   HQ vardı, bizde HQ yok.
3. **Oyuncak türü sayısı?** Ponchics 8 diyor (A–E+). Karakter kadromuz 9;
   tür sayısını karakter sayısına eşitlemeyi öneriyorum.
4. **Ponchics'in sayısal tablosu** (seviye seviye üretim/maliyet) elimizde
   yok — sadece başlangıç sabitleri var. `simulation.php` çıktısını
   paylaşırsanız matrisi birebir kurabilirim.
