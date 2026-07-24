# DecisionOS — Proje Anayasası (Claude Code her oturumda okur)

## Ne inşa ediyoruz
Vault-driven pazarlık ajanı platformu. Kod = motor, `vault/` = beyin.
Spec hiyerarşisi: `docs/MASTER-SPEC-v3.md` > `docs/SYSTEM-UPDATE-v2.md` > bu dosya.
Çakışmada üstteki kazanır ve fark PR açıklamasına yazılır.

## Değişmez kurallar
1. Vault'a kod içinden yazma (tek istisna: 05-Metrikler/dashboard.md üretimi)
2. Fiyat, taktik, segment, karar, şablon metni ASLA hardcode edilmez — vault/content'ten okunur
3. Karşı tarafa opt-in'siz WhatsApp gönderimi imkânsız kalmalı (guard'a dokunulmaz)
4. Her davranış değişikliği test ister; mevcut testler hiçbir commit'te kırılmaz
5. Migration'lar geri alınabilir olmalı (upgrade+downgrade test edilir)
6. Secret'lar sadece env'den; koda/log'a sızmaz
7. Subagent'lar SADECE JSON döndürür; kontrat değişikliği = test değişikliği aynı PR'da

## Komutlar
- Test: `pytest -q`  · Migration: `alembic upgrade head` / `alembic downgrade -1`
- Metrik: `python scripts/update_metrics.py` · Intel: `python scripts/run_intel.py`
- Günlük rapor: `python scripts/daily_report.py`

## Definition of Done (her iş paketi için)
Kod + testler yeşil + migration doğrulandı + README/spec işaretlendi + PR açıklamasında kapatılan spec maddeleri listeli.
