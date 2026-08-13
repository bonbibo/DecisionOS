---
name: vault-mantigi
description: Vault dosyası oluştururken veya VaultReader'a dokunurken kullan. Frontmatter şemaları, manifest kuralları, hot-reload ilkeleri.
---
# Vault Mantığı
- Frontmatter = makine parametresi, gövde = insan bağlamı. Parametre eklemek istiyorsan frontmatter'a ekle, gövdeye gömme.
- Yeni klasör = manifest'e satır + VaultReader testine vaka. Koda rol→klasör eşlemesi yazmak YASAK.
- Dosya sıralaması deterministik (path sort) — LLM context tutarlılığı için.
- `durum` alanı yaşam döngüsüdür: taslak→aktif→pasif/iptal. `aktif` olmayan içerik LLM context'ine girmez (kutuphaneci hariç).
- Şablonlar `vault/_sablonlar/` altında; yeni tip eklerken önce şablonunu yaz.
- Vault değişikliği davranış değişikliğidir: her vault yapısal değişikliğinde en az bir davranış testi güncellenir.
