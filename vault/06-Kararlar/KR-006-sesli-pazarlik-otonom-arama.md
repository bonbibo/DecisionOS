---
karar_id: KR-006
baslik: Sesli pazarlık — canlı, tam otonom arama
durum: taslak
etki_alani: ["urun", "kanal"]
gozden_gecirme: "KR-003 eşiği geçildiğinde VE hukuk görüşü (kayıt izni) tamamlandığında"
guncelleme: 2026-07-25
---
# KR-006: Sesli pazarlık — canlı, tam otonom arama

## Bağlam
KR-003, ses kanalına **ne zaman** yatırım yapılacağına karar veriyor (eşik: eskalasyonların
%40'ı `phone_request`) ama **nasıl** çalışacağına değinmiyor. Bu karar o boşluğu dolduruyor:
eşik geçildiğinde inşa edilecek şeyin şeklini şimdiden netleştiriyor — kod değil, tasarım.

Metin akışının güvenlik modeli şu ana kadar tek bir ilkeye dayanıyordu: **hiçbir mesaj insan
onayından geçmeden karşı tarafa gitmez** (`app/review.py`, `/admin` approve/edit/reject —
`docs/product-one-pager.md`'de "insan onay katmanı" olarak konumlandırılan şey). Canlı bir
telefon görüşmesinde bu ilke uygulanamaz: AI konuşurken duraklatıp onay bekleyemez. Sesli
pazarlığı otonom yapmak, bu tek ilkeyi ortadan kaldırmak değil, ona **alternatif bir güvenlik
modeli** koymak demektir.

## Seçenekler
- **Asenkron sesli mesaj**: WhatsApp sesli notu — AI script yazar, operatör metin akışındaki
  gibi onaylar, TTS ile seslendirilip gönderilir. Mevcut onay mekanizması aynen korunur, canlı
  konuşma yok.
- **Canlı arama, insan hatta gözlemci**: AI gerçek zamanlı konuşur, bir operatör dinler ve
  gerekirse anında müdahale/kapatma yetkisi taşır. Onay-öncesi değil ama insan kontrolü hatta.
- **Canlı arama, tam otonom**: AI telefonla arar, uçtan uca kendi başına pazarlık yapar, insan
  aramanın içinde yok. En yüksek risk — hatalı/taahhüt niteliğinde bir cümle anında karşı
  tarafa gider, geri alınamaz.

## Karar
**Tam otonom canlı arama** seçildi. Metin akışındaki "önce onay" ilkesinin yerini, aramaya
girmeden önce uygulanan **deterministik kısıtlar** alır — bunlar insan onayı değil, bugün
Kritik'in floor kontrolü yaptığı mantığın (bkz. playbook'lardaki "Kırmızı çizgiler") arama
öncesine taşınmış hali:

1. Arama başlamadan önce Stratejist aynı `anchor`/`target`/`floor`/`concession_ladder` planını
   üretir (metin akışıyla aynı kontrat). Ajan **floor altı bir rakamı sesli olarak telaffuz
   edemez** — bu bir prompt talimatı değil, konuşma-üretim katmanının önünde çalışan bir sayı
   kontrolü olmalı (örn. teklif edilecek rakam her seferinde plan sınırlarına karşı programatik
   doğrulanır, sınır dışıysa TTS'e hiç gitmez).
2. Her arama tam olarak kaydedilir (rıza şartıyla — bkz. açık soru) ve biter bitmez transkript +
   özet insan incelemesine düşer; bu **arama-sonrası** bir güvenlik ağıdır, arama-öncesi onayın
   yerini tutmaz ama bir "kill switch"in olmayışını kısmen dengeler.
3. Vaka floor'un altında/üstünde bir sonuçla kapanırsa (yanlışlıkla dahi) `Case.escalated`
   otomatik `True` olur ve ödeme akışı (`require_pre_auth`) devreye girmeden insan onayı ister —
   yani hasar sesli görüşmede oluşsa bile, parasal sonuç yine mevcut ödeme güvenlik ağından geçer.

## Açık sorular (hukuk görüşü olmadan kapanmaz)
- **Kayıt izni**: BAE'de iki taraflı rıza mı gerekiyor, tek taraflı bildirim yeterli mi? Şu an
  bilmiyoruz — KR-003'ün "kayıt izni, KVKK/GDPR" notu bu kararla somutlaşıyor, hukuk görüşü
  şart (bkz. `KR-004-sirket-kimligi.md`'nin taslak kalma gerekçesiyle aynı kategori sorun).
- Karşı taraf, aradığı şeyin bir AI olduğunu her aramanın başında biliyor mu (şeffaflık) —
  metin akışında kimlik zaten açık ("X Danışmanlık adına... asla yanıltıcı kimlik"); sesli
  aramada bu açıklamanın nasıl/ne zaman yapılacağı ayrı bir tasarım maddesi.
- Telefoni/STT/TTS sağlayıcı seçimi (Twilio Voice + streaming STT + TTS — Miso One dahil
  adaylar değerlendirilecek) burada karara bağlanmadı, ayrı bir teknik taslak gerektirir.

## Gerekçe
Kullanıcı talebi net: sesli pazarlığı da AI yapsın, insan hatta olmasın. Ama "önce onay"
ilkesinin canlı konuşmada uygulanamaz olması, riski ortadan kaldırmıyor, biçim değiştiriyor —
bu karar o riski nerede karşılayacağımızı (arama öncesi sayı kısıtı, arama sonrası inceleme,
kapanış sonrası ödeme onayı) yazılı hale getiriyor ki KR-003 eşiği geçildiğinde inşaat
hislere değil bu kayda göre başlasın.

## Başarı kriteri (gözden geçirmede neye bakılacak)
KR-003'ün `phone_request` eşiği (%40) geçilmeden bu kararın "durum"u `aktif`e çekilmez.
Eşik geçilse bile, kayıt izni hukuk görüşü tamamlanmadan mühendislik başlamaz. Aktif olunca:
ilk 10 sesli vakada floor ihlali **sıfır** (deterministik kısıt çalışıyor mu ölçütü) ve
kazanma oranı metin akışının gerisinde kalmıyor.
