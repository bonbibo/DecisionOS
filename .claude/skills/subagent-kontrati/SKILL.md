---
name: subagent-kontrati
description: app/prompts/ dosyalarına veya subagent JSON şemalarına dokunurken kullan.
---
# Subagent Kontratı
- Her subagent SADECE JSON döndürür; şemadaki zorunlu alanlar app/subagents.py doğrulamasıyla birebir aynı olmalı.
- Prompt değişikliği yaparken: (1) zorunlu alan ekliyorsan doğrulama + tüm çağıran testler aynı PR'da güncellenir, (2) alan silmek breaking change'dir — önce deprecated işaretle.
- Kritik'in kontrol listesi numaralıdır; yeni madde SONA eklenir, numaralar değişmez (testler numaralara referans verir).
- Prompt dosyasının başındaki "# SUBAGENT:" satırı ve çağrılma koşulu korunur.
- LLM çıktı doğrulaması engine'de: yüzde/tutar gibi kritik rakamlar her zaman frontmatter kaynağıyla karşılaştırılır.
