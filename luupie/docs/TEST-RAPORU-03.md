# Luupie — Test Raporu 03 + Heyecan Denetimi

**Hedef:** `luupie-toy-factory.gomooo.chatgpt.site`
**Yöntem:** Headless Chromium, yatay 932×430, gerçek dokunuş; ayrıca 90 sn
kesintisiz üretim izleme ve sevkiyat doğrulaması.

**JavaScript hatası: sıfır.**

---

# BÖLÜM 1 — Teknik

## 🛑 Oyunu durduran hata

### Oyun 45 saniyede kilitleniyor

Ölçülen döngü:

```
t=0sn    sipariş 1/8   hat 588/sa   para 350
t=15sn   sipariş 5/8   hat 588/sa   para 350
t=30sn   sipariş 7/8   hat 588/sa   para 350
t=45sn   sipariş 8/8   ← DOLDU
t=60sn   sipariş 8/8   para 350
t=75sn   sipariş 8/8   para 350
t=90sn   sipariş 8/8   para 350   ← hiçbir şey olmuyor
```

Sipariş 8/8'e ulaşınca kart `SEVKİYAT HAZIR · 180 coin · dokun ve gönder`
haline geliyor — **ama o kart navigasyon kümesinin tam altında.**

```
öğe:     ▣ 8/8   ·  aria: "Sipariş durumunu aç"
konum:   (719, 343)  60×43
üstünde: ⌂ FABRİKA ⌁ ŞEHİR ♥ 2 LUUPIES
```

`elementFromPoint` merkezde navigasyonu döndürüyor. Oyuncunun sevk etmesi
fiziksel olarak imkânsız; **para kazanmanın başka yolu yok** (üretim doğrudan
para vermiyor — bu doğru tasarım). Sonuç: 45 saniye sonra oyun ilerlemiyor.

**Mekanik sağlam, sadece z-sırası bozuk.** Düğmeyi programatik tıklattığımda:

```
para:  350 → 530   (+180)
plan:  0 → 1
sipariş: 8/8 → 1/8  (yeni sipariş başladı)
```

Yani tek satırlık bir yerleşim düzeltmesi oyunu açıyor.

**Düzeltme (öncelik 1):** Sipariş göstergesini nav kümesinin dışına al.
En temizi V3'teki plan: sahnede kamyonun üstünde diegetic baloncuk, hazır
olunca `SEVK ET`'e dönüşür. Ara çözüm: nav'ın soluna en az 16 px boşlukla.

## Rapor 02'den devam edenler (hiçbiri kapanmamış)

| # | Madde | Durum |
|---|---|---|
| Y-K1 | Sipariş düğmesi nav altında | ❌ aynı — artık oyunu kilitlediği doğrulandı |
| Y-Y1 | Görev paneli `overflow: hidden`, 7 px taşma | ❌ aynı |
| Y-Y2 | Sahnede dokunma çakışmaları | ❌ aynı: STITCH⨯Bunbun 24×28 · PAINT⨯Zip 25×26 · PACK⨯rozet 35×32 · sipariş⨯ŞEHİR 52×17 |
| O-1 | Panel %82 × %100 (spec %66 × %90) | ❌ aynı |
| O-2 | Şehir `12/0 plan` biçimi | ❌ aynı |
| O-3 | Karşılanamayan aşama düğmesi gizleniyor | ❌ aynı |
| A1 | Öneri motoru boştaki işçileri saymıyor | ❌ aynı |

Bu turda yeni bir dağıtım yapılmamış görünüyor; ölçümler rapor 02 ile birebir
aynı çıktı.

---

# BÖLÜM 2 — Heyecan denetimi

Aşağıdakiler hata değil; **oyunun şu an neden düz hissettirdiği**.
Gözlemlenen çekirdek döngü tek cümleyle: *45 saniye bekle, sevk et, tekrar
et.* Her tur birebir aynı.

## 🔵 A. En büyük eksik: "Cute Meets Crazy"in Crazy'si yok

Konsept dokümanının tamamı bu ikilik üzerine kuruluydu. Şu an oyunda
**yalnızca Cute var.**

Test sırasında: Grizz `♥ %28` ve `!` rozetli — psycho eşiğinin altında.
Ama 90 saniye boyunca hiçbir şey olmadı. Ne 2× overdrive, ne hatalı ürün,
ne bir risk kararı, ne görsel bir değişim.

**Bu, oyunun kimliğini geri getirecek tek hamle:**

| Ne | Nasıl |
|---|---|
| Sevgi düşünce dönüşüm | %25 altında karakter sahnede görünür şekilde psycho'ya döner — renk, duruş, aura |
| Kazanç | İstasyonu **2× hızlandırır** — hat hızı anında zıplar, oyuncu bunu ekranda görür |
| Bedel | Ürettiğinin **%18'i hatalı** — bantta farklı siluetle akar, paketlemeyi tıkar |
| Karar | Zapt et (bitir) · Besle (sakinleştir) · **bırak çalışsın** (riski kabul et) |
| Duygu | İlk kez bir şey ters gidebilir hale gelir |

Şu an oyunda **hiçbir şey ters gidemiyor.** Risk yoksa dikkat de yok.

## 🔵 B. Sevkiyat anı sessiz

Ekonominin tek satış noktası ve en önemli anı. Şu an olan: bir sayı 350'den
530'a değişiyor. Hepsi bu.

**Olması gereken (ucuz, yüksek etki):**

1. Kamyon rampaya yanaşır, kutular yüklenir (1,2 sn)
2. Kamyon çıkarken korna/motor sesi
3. Paralar kamyondan HUD'a **uçar** — 8–12 parça, saçılarak
4. HUD sayacı **sayarak** artar (350→530 arası ~600 ms), bir tık büyür ve
   yerine oturur
5. İşçiler bir an el sallar / zıplar
6. Yeni sipariş kartı yukarıdan düşerek gelir

Bu altı adım hiçbir sistem değiştirmez, sadece var olan olayı görünür yapar.
**Idle oyunların yaşadığı yer burasıdır.**

## 🔵 C. Her tur birebir aynı

Ölçülen: sipariş hep 8 adet, ödül hep 180, süre hep ~45 sn.

**Çeşitlilik önerileri:**

| Tür | Sıklık | Ne değişir |
|---|---|---|
| Normal sipariş | %70 | 6–10 adet, ödül ölçekli |
| Acele sipariş | %15 | Yarı süre, **1.8× ödül**, kaçırırsan kaybolur |
| VIP müşteri | %10 | Belirli bir Luupie'nin ürettiğini ister, ekstra plan verir |
| Toplu sipariş | %5 | 25 adet, büyük ödül, birkaç tur sürer |

Müşteri yüzü de değişsin — şu an anonim. Tanıdık bir yüzün dönmesi
(Hay Day'in yaptığı) bağ kurar.

## 🔵 D. Fabrika kendi kendine bozulmuyor

90 saniye boyunca darboğaz `6.1 sn`de sabit kaldı, hiçbir arıza çıkmadı,
hiçbir işçinin morali düşmedi.

Bir idle oyunun geri çağırma gücü **"gidince bir şeyler bozulur"**
varsayımına dayanır. Şu an gidip 3 saat sonra gelseniz her şey aynı yerde
duruyor olacak.

**Eklenmesi gerekenler:**
- **Sevgi zamanla düşsün** (saatte ~%8). Yemekhane/besleme o zaman anlam kazanır.
- **Rastgele arıza** (ortalama 6–10 dakikada bir, sahnede duman + kıvılcım).
- **Makine yıpranması:** uzun süre bakımsız kalan istasyon %10 yavaşlar.

Bunlar ceza değil, **geri dönme sebebi**. Ve hepsi zaten tasarlanmış mini
oyunlara bağlanır — şu an mini oyunları tetikleyen hiçbir şey yok, bu yüzden
test boyunca bir kez bile açılmadılar.

## 🔵 E. Mikro geri bildirim yok

Sahnede sürekli olan hiçbir şey yok:

- Ürün tamamlandığında **hiçbir şey uçmuyor** (`+1 🧸` çıkmalı)
- Tampon dolduğunda görsel bir baskı yok — küçük turkuaz kareler hep aynı
- İşçiler çalışırken hiçbir efekt yok (dikiş kıvılcımı, boya sıçraması,
  presten buhar)
- Karakterlerin **yürüme sprite'ları yüklü** (`luupie-*-walk.png`) ama
  karakterler sabit duruyor — yüklenen varlık kullanılmıyor

Öneri: her ürün tamamlanışında istasyonun üstünde 1 saniyelik küçük bir
parçacık + `+1`. 20 saniyede 5 kez olan bir olay, ekranı canlı tutar.

## 🔵 F. İlerleme hissi görünmüyor

`GECE VARDİYASI · LV 1` yazıyor ama:

- XP çubuğu yok
- Bir sonraki açılışın ne olduğu yazmıyor
- Şehirde kazanılan planların fabrikada ne işe yaradığı belli değil

**Öneri:** HUD'da ince bir ilerleme çubuğu ve tek satır hedef:
`LV 2'ye 3 sevkiyat · Repair Alley açılıyor`. Oyuncu neye doğru gittiğini
bilmeli.

## 🔵 G. Boş işçiler ve boş kapasite

Test anında 6 karakterden **2'si boştaydı** (LUUPIES rozetinde `2`), biri de
psycho eşiğindeydi. Fabrika bunu hiçbir yerde söylemiyor; sadece sekmede bir
rozet var.

Boşta bir işçi varken hat yavaş çalışıyorsa oyun bunu **bağırmalı** —
sahnede o işçi elleri cebinde dolaşmalı, üstünde `👤?` baloncuğu olmalı.

## 🔵 H. Sessizlik

Ses testi yapamadım (headless), ama kontrol edin: bant uğultusu, dikiş
makinesi, pres tokması, sevkiyat kornası, sipariş dolduğunda tek bir tatmin
edici "ding". Idle oyunlarda ses, ekran kapalıyken bile devam eden şeyin
yaşadığını hissettirir.

---

# Öncelik sırası

| # | İş | Etki | Emek |
|---|---|---|---|
| 1 | **Sipariş düğmesini nav'ın altından çıkar** | Oyun oynanabilir hale gelir | Çok az |
| 2 | **Sevkiyat anına juice ekle** (kamyon, uçan para, sayan sayaç) | En sık tekrarlanan an keyifli olur | Az |
| 3 | **Psycho sistemini aç** (dönüşüm, 2×, hatalı ürün, üç seçenek) | Marka vaadi geri gelir, risk doğar | Orta |
| 4 | **Sevgi düşüşü + rastgele arıza** | Mini oyunlar tetiklenir, geri dönme sebebi oluşur | Orta |
| 5 | **Sipariş çeşitliliği** (acele / VIP / toplu) | Her tur farklı hissettirir | Az-orta |
| 6 | **Mikro geri bildirim** (`+1` parçacıkları, istasyon efektleri, yürüyen karakterler) | Sahne canlanır | Az |
| 7 | **İlerleme çubuğu + sonraki hedef** | Yön duygusu | Az |
| 8 | Rapor 02'nin kalan teknik maddeleri | Cila | Az |

İlk iki madde birlikte yarım günlük iş ve oyunu "çalışmıyor"dan
"keyifli"ye taşır. 3. ve 4. maddeler onu **oyun** yapar.

---

# Test edilemeyenler

- **Mini oyunlar** — üçüncü turda da tetiklenmedi; arıza/kalite olayı hiç
  oluşmuyor (bkz. D maddesi)
- **Offline dönüş / kasa toplama**
- **Şehir aşama tamamlama** — sevkiyat kilitli olduğu için plan birikmiyor
- **Ses**

Bir `?debug=1` modu (olay zorlama, para/plan verme, zaman hızlandırma)
koyarsanız bunların hepsini tek geçişte gezebilirim.
