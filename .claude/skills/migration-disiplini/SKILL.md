---
name: migration-disiplini
description: Alembic migration yazarken kullan. Geri alınabilirlik, veri güvenliği, sıra kuralları.
---
# Migration Disiplini
- Her migration çifti: upgrade + gerçek çalışan downgrade. `pass` downgrade YASAK.
- Kolon ekleme: nullable ekle → backfill → gerekirse ayrı migration'da NOT NULL.
- Enum genişletme: Postgres'te yeni değer ekleme ayrı migration; enum daraltma YASAK (yeni enum + veri taşıma).
- Doğrulama komutu her migration sonrası: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
- Migration'da uygulama kodu import etme (model sınıfları değil, tablo/op düzeyinde çalış).
