# RUNBOOK

Operasyonel referans — deploy, rollback, olay müdahalesi. `README.md`'nin
Setup bölümünün üretim-spesifik eki; geliştirme kurulumu için oraya bakın.

## Deploy

1. `alembic upgrade head` — deploy pipeline'ının bir parçası olarak, uygulama
   başlamadan ÖNCE çalışır (migration'lar geri alınabilir şekilde yazılır,
   bkz. `migration-disiplini` skill — ama yine de önce migration, sonra kod).
2. Uygulamayı başlat (`uvicorn app.main:app`).
3. `.env`'deki tüm `change-me` değerlerinin gerçek değerlerle doldurulduğunu
   doğrula — özellikle `REVIEW_TOKEN`, `WHATSAPP_APP_SECRET`,
   `STRIPE_WEBHOOK_SECRET` (bunlar olmadan ilgili guard'lar/doğrulamalar
   ya reddeder ya da — daha kötüsü — varsayılan zayıf değerle "çalışır
   görünür").
4. `GET /health/deep` ile DB + vault manifest + Stripe config kontrolü.
5. Railway cron: `scripts/run_intel.py` (günlük) ve `scripts/daily_report.py`
   (günlük, önceki gün için) job'larının tanımlı olduğunu doğrula.

## Rollback

1. Önceki imaja/deploy'a dön.
2. Migration geriye dönük uyumsuzsa (yeni migration eski kodun beklemediği
   bir NOT NULL/DROP içeriyorsa) `alembic downgrade -1` — ama V1'deki hiçbir
   migration bunu yapmıyor (her yeni sütun nullable veya server_default'lu),
   bu yüzden çoğu durumda migration'ı geri almadan sadece kodu eski
   imaja döndürmek yeterli.
3. `docs/PROGRESS.md`'ye rollback nedenini not düş.

## Olay müdahalesi

**Stripe webhook imza hataları artıyor**
`POST /payments/webhook` sürekli 401 dönüyorsa: Stripe Dashboard'daki
webhook endpoint'inin `STRIPE_WEBHOOK_SECRET` değeri ile `.env`'deki
değerin eşleştiğini kontrol et. Endpoint URL'i değiştiyse (yeni domain,
yeni path) Stripe tarafında da güncellenmesi gerekir.

**WhatsApp signature 401'leri artıyor**
`POST /channels/whatsapp/webhook` 401 dönüyorsa: `WHATSAPP_APP_SECRET`
Meta App Dashboard > Settings > Basic'teki değerle eşleşiyor mu kontrol et.
Meta tarafında app secret rotate edildiyse burada da güncellenmeli.

**Opt-in guard beklenmedik şekilde gönderimi engelliyor**
`POST /review/{id}/approve` "opt-in required" ile 409 dönüyorsa: bu
Package H'nin guard'ı — alıcıdan son 24 saatte gelen bir inbound WhatsApp
mesajı yok demektir. `/optin/{case_id}` linkine tıklamak TEK BAŞINA yeterli
değildir (bkz. README "Opt-in guard"), alıcının gerçekten WhatsApp'tan
yazması gerekir. Acil durumda operatör manuel olarak `OptIn(method=
manual_operator)` satırı ekleyip guard'ı atlatabilir mi? HAYIR — guard'ın
tek kaynağı gerçek inbound mesajdır (bkz. `_has_valid_opt_in`), bu
kasıtlı: `OptIn` tablosu sadece denetim izi, guard'ı tek başına geçirmez.

**Ödeme ön-onayı olmadan gönderim engelleniyor**
`POST /review/{id}/approve` "payment pre-authorization required" ile 409
dönüyorsa: müşteri henüz checkout linkini tamamlamamış demektir — vaka
detayında (`/admin/cases/{id}`) ödeme durumunu kontrol et. Gerçekten
tahsilat gerekmeyen bir vakaysa (`is_demo` veya fiyatsız dikey) bu guard
zaten devreye girmez; giriyorsa vaka yanlışlıkla `is_demo=False` +
fiyatlı bir dikeyle açılmış olabilir.

**LLM API kesintisi**
Subagent çağrıları başarısız oluyorsa: `app.subagents.call_subagent_json`
zaten bir retry + `SubagentEscalated` ile insan kuyruğuna düşürüyor — vaka
`escalated=True` olur, ek bir aksiyon gerekmez, sadece `llm_calls` hata
oranını (`/admin/costs`) izle. Kesinti uzun sürerse yeni vakalar sürekli
eskale olacaktır — bu durumda müşteri iletişimini geçici olarak durdurmak
(intake webhook'unu devre dışı bırakmak) operatörün insiyatifinde bir
karar, kodda otomatik bir devre kesici yok.

**Migration sorunları**
Her migration'ın `upgrade + downgrade + upgrade` döngüsü deploy öncesi
doğrulanmalı (`migration-disiplini` skill). Bir migration yarıda kalırsa
(`alembic upgrade head` hata verirse) veritabanı tutarsız bir ara durumda
kalabilir — Postgres DDL'i transactional olduğu için genelde tek migration
içindeki adımlar ya hep ya hiç uygulanır, ama birden fazla migration
art arda çalıştırılıyorsa hangi revizyonda kaldığını `alembic current`
ile kontrol et.
