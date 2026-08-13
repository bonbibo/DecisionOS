# PROGRESS — MASTER-SPEC-v3 (Package F-K)

Final report per `AUTONOMOUS-RUN.md`'s format. All packages ran to
completion, back to back, per the confirmed onay modu (no per-PR stop) —
no package hit the 3-failed-review-round threshold.

## Paket tablosu

| Paket | Durum | Test sayısı (bu paket / kümülatif) | İNSAN GEREKLİ |
|---|---|---|---|
| F — Market Intel | ✅ Tamamlandı | 19 / 146 | Property Finder/Bayut'un gerçek CSS seçicilerinin siteye bakılarak doğrulanması + ToS/robots.txt kontrolü; Railway cron job kurulumu (`scripts/run_intel.py`, günlük) |
| G — Stripe pre-auth → capture | ✅ Tamamlandı | 35 / 181 | Gerçek Stripe hesabı + webhook endpoint kaydı; `STRIPE_SECRET_KEY`/`STRIPE_PUBLISHABLE_KEY`/`STRIPE_WEBHOOK_SECRET` env değerlerinin doldurulması |
| H — E-posta-önce ilk temas + opt-in guard | ✅ Tamamlandı | 15 / 196 | `WHATSAPP_PUBLIC_NUMBER` + Gmail OAuth env değerleri; gerçek click-to-WhatsApp davranışının canlıda doğrulanması |
| I — Landing + waitlist | ✅ Tamamlandı | 7 / 203 | Gerçek domain/DNS kurulumu |
| J — Üretim sertleştirme | ✅ Tamamlandı | 13 / 216 | Railway cron job (`scripts/daily_report.py`, günlük); gerçek log aggregator/alerting bağlantısı (Sentry vb. — spec'te istenmedi, kapsam dışı bırakıldı) |
| K — Ses kapısı | ✅ Tamamlandı | 13 / 229 | Yok (kod tarafı tamamen kendi kendine yeterli — kalan tek şey insan kararı: `KR-003`'ü ne zaman `aktif`'e çekeceğine dair, eşik veriye ulaştığında) |
| Uçtan uca kabul testi | ✅ Tamamlandı | 1 / 230 | — |

**Toplam:** 230 test (v2'nin 98'inden başlayıp v3 boyunca hiç gerilemeden
büyüdü), 13 migration (hepsi upgrade+downgrade+upgrade doğrulanmış).

## Kabul kriteri

> Waitlist'ten capture'a uçtan uca akış, elle DB müdahalesi sıfır.

**Karşılandı.** `tests/test_end_to_end_flow.py::test_waitlist_to_capture_
end_to_end` bu akışı uçtan uca, sadece HTTP/webhook/script çağrılarıyla
(hiç doğrudan DB yazımı olmadan) çalıştırıp doğruluyor: waitlist kaydı →
web intake onayı → `Payment(pending)` → Stripe checkout + webhook →
`Payment(pre_authorized)` → karşı tarafın ilk WhatsApp mesajı (opt-in) →
Kritik APPROVE → `POST /review/{id}/approve` (opt-in + ön-onay guard'ları
geçilir) → anlaşma kapanışı → otomatik `capture_for_won_case` →
`Payment(captured)` → `daily_report`'ta doğru sayılar.

## İnsanın yapması gereken sıralı kurulum listesi

1. **Stripe** (Paket G): hesap aç, `STRIPE_SECRET_KEY`/`STRIPE_
   PUBLISHABLE_KEY` al, webhook endpoint'i (`POST /payments/webhook`)
   Stripe Dashboard'da tanımla, `STRIPE_WEBHOOK_SECRET`'ı `.env`'e yaz.
2. **WhatsApp** (mevcut v2 kurulumuna ek, Paket H): `WHATSAPP_PUBLIC_
   NUMBER`'ı (gerçek genel numara, `+` olmadan) `.env`'e yaz; click-to-
   WhatsApp linkinin (`/optin/{case_id}`) gerçek bir telefonda doğru
   açtığını test et.
3. **Gmail** (mevcut v2 kurulumuna ek, Paket H): ilk-temas e-postalarının
   gerçekten gittiğini doğrula (OAuth refresh token zaten v2'de kuruldu
   varsayılıyor).
4. **Market Intel** (Paket F): `app/intel/property_finder.py` ve
   `app/intel/bayut.py`'deki `_default_fetch`'in gerçek CSS/XPath
   seçicilerini siteye bakarak yaz (şu an bilinçli olarak stub — bkz. o
   dosyaların docstring'i); ToS/robots.txt'i kontrol et. Railway'de günlük
   cron: `python scripts/run_intel.py`.
5. **Günlük rapor cron'u** (Paket J): Railway'de günlük cron: `python
   scripts/daily_report.py`. İsteğe bağlı: `OPS_EMAIL` doldurulursa rapor
   ayrıca o adrese e-postalanır.
6. **Domain/DNS** (Paket I): `PUBLIC_BASE_URL`'i gerçek domain'e göre
   güncelle; landing sayfasının (`GET /`) o domain'de eriştiğini doğrula.
7. **KR-003 / KR-004** (Paket K): ikisi de vault'ta `durum: taslak`.
   KR-003 — `phone_request` oranı günlük raporda `%40`'ı geçtiğinde bu
   kararı gözden geçir (aktif'e çek ya da eşiği güncelle). KR-004 — şirket
   adı/marka kararı verildiğinde `IDENTITY_NAME` env değerini güncelle ve
   bu kararı `aktif`'e çek.
8. Tüm `.env`'deki `change-me` değerlerinin doldurulduğunu `docs/RUNBOOK.md`
   → "Deploy" adım 3'teki gibi doğrula, sonra `GET /health/deep` ile
   son kontrol.

## Bilinçli olarak kapsam dışı bırakılanlar

Kullanıcı onayıyla (bu depoyu tetikleyen görevde açıkça belirtildi):
hukuk görüşmesi konusu için ayrı bir akış (mevcut genel `ESCALATE`'e
düşmeye devam ediyor), şirket kimliği/isim kararının kendisi (kod
`IDENTITY_NAME` ile bekliyor, `KR-004` taslak), ve talep doğrulama
görüşmeleri (tamamen insan işi).
