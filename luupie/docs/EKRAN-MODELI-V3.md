# Luupie — Ekran Modeli V3: Tam Panel + Temiz Sahne

> ⚠️ **Bu doküman `LUUPIE-SPEC.md` içinde birleştirildi.**
> Tek yetkili tasarım dokümanı odur; bu dosya tarihsel kayıt olarak duruyor.

**Bu doküman `FACTORY-HOME-V2.md` bölüm 5'teki "çekmece ≤%38" kuralını
geçersiz kılar.** Referans: Hay Day.

İki kural:

1. **Her alt yüzey büyük panel olarak açılır.** İstasyon, geliştirme, işçi,
   karakter, mini oyun, şehir — hepsi. Kapatılınca ana ekrana dönülür.
2. **Ana ekranda krom yalnızca köşelerde durur.** Düğmeler sadece
   okunabilecek kadar büyük olur ve **karakterlerin bulunduğu alana asla
   değmez.**

---

## 0. Neyi feda ediyoruz, nasıl telafi ediyoruz

Çekmece kuralı tek bir şey içindi: işçiyi değiştirdiğinde bandın hızlandığını
**aynı anda** görmek. Tam panelde bu kaybolur — panel kapanana kadar sahneyi
göremezsin.

Telafisi zorunlu, yoksa ilk teşhise geri döneriz ("menüler arasında dolaşmak").
Çözüm: **dönüş deltası** (bölüm 6). Etkiyi panel açıkken değil, **panel
kapanırken** göster. Kapanış bir geçiş değil, ödül anı olur.

Bu telafi olmadan V3 uygulanmasın.

---

## 1. Ana ekran bölgeleri

Üç bölge var ve sınırları katı:

```
┌──────────────────────────────────────────────────────────────┐
│ ⭐11 🪙145                                   💎34  🎁4   ⚙   │ ← KÖŞE KROMU
│                                                              │
│                  ╭──────╮                                    │
│                  │ 9:55 │      ← GÖK ŞERİDİ                 │
│                  ╰───┬──╯        (diegetic baloncuklar)      │
│   ┌────┐   ┌────┐  ┌─┴──┐   ┌────┐                          │
│  ─┤    ├─▪─┤    ├──┤    ├─▪─┤    ├──   YAŞAM ALANI          │
│   └────┘   └────┘  └────┘   └────┘     krom giremez         │
│    Press    Stitch   Paint    Pack                           │
│      ●        ●        ●        ●      ← karakterler        │
│                                                              │
│ 📋                                        [🏭][🏙][💜]       │ ← KÖŞE KROMU
└──────────────────────────────────────────────────────────────┘
```

| Bölge | Ne girer | Ne giremez |
|---|---|---|
| **Köşe kromu** | Para, seviye, bildirim, navigasyon, görev düğmesi | Oyun durumu anlatan hiçbir şey |
| **Gök şeridi** | Makineye ait diegetic baloncuk (süre, uyarı, sipariş) | Buton, panel, kart |
| **Yaşam alanı** | Makineler, bant, tampon, ürün, karakterler | **Hiçbir arayüz öğesi** |

### Ölçüler · 932 × 430, güvenli alan 59 yan / 21 alt

| Öğe | Konum | Maksimum boyut |
|---|---|---|
| Sol üst küme | (67, 10) | 210 × 56 |
| Sağ üst küme | sağdan 67 | 250 × 56 |
| Sol alt düğme | (67, alttan 24) | 56 × 56 (tek düğme) |
| Sağ alt navigasyon | sağdan 67 | 210 × 56 |
| **Yaşam alanı** | (67, 76) – (865, 352) | **798 × 276 — dokunulmaz** |
| Gök şeridi | yaşam alanının üst 60 px'i | baloncuklar buraya |

Köşe kümeleri toplamı ≈ %9 ekran. Kalan her piksel sahne.

### Karakterlere değmeme kuralı

Diegetic baloncuk **makinenin tepesine** demirlenir ve alt kenarı bant
şeridinin üstünden en az `24 px` yukarıda durur. Karakterler bant şeridinde ve
önünde yürüdüğü için baloncuk onları hiçbir konumda örtmez.

Bir karakter baloncuğun altından geçerse baloncuk **kaybolmaz**, karakter
üstte çizilir. Sahne her zaman kazanır.

---

## 2. Sahneden kalkacaklar

Mevcut build'de yaşam alanına giren ve kaldırılması gereken öğeler:

| Kalkacak | Yerine |
|---|---|
| Büyük daire istasyon ikonları | Makine sanatının kendisi |
| `PRESS · LV 1 · 3.7sn` pill etiketleri | Makinenin altında küçük isim (oyun fontu), sayılar panelde |
| `YAVAŞ` rozeti | Darboğaz baloncuğu (gök şeridinde) |
| Sipariş kartı (üst sol) | Sahnedeki kamyon + sipariş panosu |
| `HAT CANLI 215/SA` | Sağ üst köşe kümesine küçük rozet |
| Vardiya kartları şeridi (alt) | Makine üstü baloncuklar + sol alt görev düğmesi |
| `20/20` tampon sayıları | Fiziksel yığın; sayı yalnızca panelde |

Sipariş artık sahnede yaşar: kamyon rampada bekler, üstünde küçük baloncuk
(`🧸 ×20 · 14/20`). Hazır olduğunda kamyon parlar ve baloncuk `SEVK ET`
düğmesine döner — **tek dokunuşla sevkiyat, panel açmadan.**

---

## 3. Panel sistemi

### Ölçü

Hay Day oranı bu en-boy oranında (2.17:1) şuna denk gelir:

- **Genişlik %66** → 620 px
- **Yükseklik %90** → 385 px
- **Ortalanmış**, kenarlardan ~156 px sahne görünür

Arkadaki sahne **%35 karartılır ama gizlenmez**. Bu %20'lik kenar payı boşuna
değil: kapatınca "geri döndüm" hissini o veriyor. Tam kaplama panel yapmayın.

### Çerçeve anatomisi

```
              ┌═══════════════════════┐
        ╭─────┤    STITCH BENCH       ├─────╮  ⊗
        │     └───────────────────────┘     │
        │  ┌ Üretim ┐ ┌ İşçi ┐ ┌ Yükselt ┐  │  ← sekmeler (opsiyonel)
        │  │        └─┴──────┴─┴─────────┘  │
        │                                   │
        │           içerik alanı            │
        │                                   │
        │  ┌──────────────┐ ┌─────────────┐ │
        │  │  İŞÇİ ATA    │ │ YÜKSELT·340 │ │  ← alt eylem sırası
        │  └──────────────┘ └─────────────┘ │
        ╰───────────────────────────────────╯
```

- **Başlık levhası** üst kenara binen ayrı bir parça
- **Kapat (⊗)** sağ üst köşeye binen büyük yuvarlak düğme, min `56 × 56`
- **Sekmeler** üst kenarda, en fazla 3
- **Alt eylem sırası** en fazla 2 geniş düğme
- **Panel zemini** sahneden açık ama krem değil — koyu paletin bir tık
  aydınlığı. Gece vardiyası dünyası korunur.

### Kapatma yolları

Üçü de çalışmalı: ⊗ düğmesi, panel dışına dokunma, geri hareketi.
Kaçış her zaman tek dokunuş.

---

## 4. Yüzey haritası

| Yüzey | Tip | Not |
|---|---|---|
| İstasyon (üretim/işçi/yükseltme) | **Panel** | Üç sekme tek panelde |
| Karakter detayı | **Panel** | Durum + eylem + kozmetik |
| Luupies listesi | **Panel** | Zaten sekme; panel çerçevesine girer |
| Şehir | **Panel** | Tam sayfa değil, aynı çerçeve |
| Mini oyunlar | **Panel** | Kamera önce makineye yaklaşır, sonra panel açılır |
| Görev listesi | **Panel** | Sol alt düğmeden |
| Sipariş detayı | **Panel** | Kamyona dokununca |
| **Sevk etme** | **Diegetic** | Kamyon baloncuğu — panel açmaz |
| Üretim durumu | **Diegetic** | Makine üstü baloncuk |
| Darboğaz uyarısı | **Diegetic** | Makine üstü baloncuk |
| Tampon doluluğu | **Diegetic** | Fiziksel yığın |
| Tıkalı istasyon | **Diegetic** | Makine durur, işçi kollarını indirir |

Kural: **bilgi diegetic, karar panelde.** Bakılan şey sahnede, dokunulan şey
panelde.

---

## 5. Diegetic baloncuk dili

Hay Day'in "9 min 55 sec / Waiting…" kalıbı. Tek tip baloncuk, içerik değişir:

| Durum | Baloncuk | Renk |
|---|---|---|
| Üretiyor | `3.2 sn` sayaç | Nötr |
| Tampon doldu / tıkalı | `⛔` + yığın görünür | Kırmızı |
| Darboğaz | `⏳ yavaş` | Amber |
| İşçi yok | `👤?` | Amber |
| Psycho işçi | `💢 ×2` | Mor |
| Sipariş hazır | `SEVK ET` (kamyonda) | Yeşil, nabız |

En fazla **iki baloncuk** aynı anda görünür — en yüksek öncelikli ikisi.
Üçüncüsü sol alt görev düğmesindeki sayıya yazılır. Sahne bildirim panosuna
dönmemeli.

---

## 6. Dönüş deltası — V3'ün zorunlu parçası

Panel kapanırken çalışan koreografi. Bu olmadan V3 uygulanmasın.

| ms | Ne olur |
|---|---|
| 0 | Panel, ait olduğu makineye doğru küçülerek kapanır (180 ms) |
| 180 | Makine kısa bir parlama yapar |
| 220 | Makinenin üstünde delta çipi belirir: `19.3 → 3.2 sn` |
| 220–1000 | Bant hızı **rampayla** yeni değere çıkar — anında değil, göz yakalasın |
| 220–1200 | Tampon yığını gözle görülür şekilde erimeye başlar |
| 1700 | Delta çipi solar |
| 1700 | Darboğaz değiştiyse yeni darboğazın baloncuğu yumuşak bir pop ile gelir |

Aynı koreografi yükseltmede, işçi atamasında ve mini oyun bitiminde çalışır.
Değişmeyen tek şey: **oyuncu ne değiştirdiyse onun sonucunu sahnede görür.**

Hiçbir şey değişmediyse (sadece bakıp kapattıysa) koreografi çalışmaz, panel
sessizce kapanır.

---

## 7. Mini oyun akışı

1. Sahnedeki baloncuğa dokun
2. **Kamera o makineye yaklaşır** (400 ms) — nerede olduğunu öğretir
3. Panel açılır, mini oyun oynanır
4. Panel kapanır, kamera yakınlıkta kalır
5. Dönüş deltası çalışır: hatalılar bantta yok olur, işçi sevinir
6. Kamera yavaşça geniş açıya döner (600 ms)

Mini oyun paneli de %66 × %90'dır; arkada yakınlaşmış makine görünür.
Ne düzelttiğini görmeden çıkmazsın.

---

## 8. Hay Day'den alınacaklar

- **Köşe kromu disiplini.** Merkez tamamen oyun.
- **Diegetic üretim göstergeleri.** Süre ve durum makinenin üstünde.
- **Tutarlı panel çerçevesi.** Aynı başlık levhası, aynı ⊗, aynı alt eylem
  sırası — her panelde.
- **Kenarlardan görünen sahne.** Panel tam kaplamaz.
- **Tek büyük CTA.** Panelin dibinde en fazla iki geniş düğme.
- **Karakterlerin üstüne hiçbir şey konmaması.**

## Alınmayacaklar

- **Krem/parlak palet.** Luupie gece vardiyası; panel koyu kalır.
- **Kalabalık köşe rozetleri.** Hay Day'de 8–10 köşe öğesi var; bizde 4'ü
  geçmesin.
- **Sekmeli mega panel** (Farm Pass gibi 3 sekme + alt sekme). Bizde panel
  başına en fazla 3 sekme, alt sekme yok.
- **Sayaçlı satış baskısı.** `23h 59m` tarzı geri sayım banner'ları sahneye
  girmesin.

---

## 9. Bu değişiklikle kapanan eski maddeler

| Eski madde | V3'teki karşılığı |
|---|---|
| Rev-01 G5 · Nav ↔ kart yeri | Vardiya kartları sahneden kalktı; nav sağ altta kalabilir |
| Rev-01 G3 · Kart metin kesilmesi | Kart yok, baloncuk var; kesilecek metin kalmadı |
| Rev-02 B5 · Çekmece etiketleri kesiyor | Çekmece yok; panel ortalanmış |
| Rev-02 E2 · Çekmece listeyi örtüyor | Aynı sebeple kapandı |
| Rev-02 C1 · Tampon yığını | Sahne temizlendiği için artık yer var |

## Hâlâ açık kalanlar

V3 bunları çözmez, ayrıca yapılmalı:

- **Rev-02 A1 · Öneri motoru atanmamış işçileri saymıyor.** Baloncuk `👤?`
  gösterse bile, görev listesi doğru eylemi sıralamalı.
- **Rev-02 C2 · Tıkalı istasyon görsel durumu.** Artık diegetic dilin parçası.
- **Rev-02 D1/D2 · Şehir etiket ve fiyat tutarsızlıkları.**

---

## 10. Uygulama sırası

| # | İş |
|---|---|
| 1 | Yaşam alanını boşalt: daireler, pill etiketler, kartlar, sipariş kartı kalksın |
| 2 | Panel çerçevesini tek bileşen olarak yaz (başlık + ⊗ + sekme + alt CTA) |
| 3 | İstasyon çekmecesini panele taşı, üç sekmeyi birleştir |
| 4 | **Dönüş deltası koreografisini yaz** — panelden önce bu bitmeli |
| 5 | Diegetic baloncuk sistemi + öncelik kuralı (maks 2) |
| 6 | Kamyon/sipariş sahneye, sevk etme tek dokunuş |
| 7 | Tampon yığınları ve tıkalı istasyon durumu |
| 8 | Diğer yüzeyleri (karakter, Luupies, şehir, mini oyun) aynı çerçeveye al |

4. madde 3'ten önce bitmeli. Panel sistemi telafisi olmadan yayına
girerse ilk teşhise geri döneriz.

---

## Kabul testi

Ana ekranın **ekran görüntüsünü alın ve arayüzü kırpın.** Geriye kalan görüntü
tek başına şunları anlatabiliyorsa V3 çalışıyor:

- Hangi istasyon yavaş
- Nerede yığılma, nerede boşluk
- Kim nerede çalışıyor
- Sipariş hazır mı

Kırpılan arayüz olmadan bu sorular cevapsız kalıyorsa, bilgi hâlâ kromda
duruyor demektir.
