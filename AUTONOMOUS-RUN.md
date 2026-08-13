# OTONOM KOŞU PROTOKOLÜ

Bu görevi tek uzun oturumda, paket paket, İNSAN ONAYI BEKLEMEDEN yürüt. Tek durma nedenleri aşağıda.

## Görev
`docs/SYSTEM-UPDATE-v2.md` (A-E) ve `docs/MASTER-SPEC-v3.md` (F-K) paketlerini sırayla, tamamı bitene kadar uygula.

## Döngü (her paket için)
1. **spec-executor** paketi uygular
2. **vault-keeper** (vault'a dokunulduysa) + **test-guardian** denetler
3. FAIL → spec-executor düzeltir → tekrar denetim (max 3 tur; hâlâ FAIL → paketi İNSAN GEREKLİ işaretle, docs/PROGRESS.md'ye yaz, SONRAKİ pakete geç)
4. PASS → **release-manager** commit'ler, PROGRESS.md günceller, sonraki pakete geçer

## Dış bağımlılık kuralı
Gerçek hesap/anahtar gerektiren maddeler (Meta, Stripe, Resend, Railway cron, canlı scrape):
- Kod + mock/fixture testleriyle TAMAMLANIR, canlı entegrasyon maddesi PROGRESS.md'de "İNSAN GEREKLİ: <env/hesap>" olarak listelenir
- Bu maddeler için durma YOK — mock'la bitir, devam et

## Durma koşulları (sadece bunlar)
1. Tüm paketler bitti → final rapor
2. Aynı pakette 3 denetim turu FAIL → işaretle, diğer paketlere devam; hepsi bitince raporla
3. Git/ortam felaketi (çözemediğin bozulma)

## Final rapor formatı (docs/PROGRESS.md sonuna)
- Paket tablosu: durum / test sayısı / İNSAN GEREKLİ maddeleri
- Toplam test, toplam migration
- İnsanın yapması gereken sıralı kurulum listesi (hesaplar, env'ler, deploy adımları)
- Kabul kriterlerinden (v3 bölümü) karşılananlar/karşılanmayanlar
