---
karar_id: KR-002
baslik: Dikey sırası
durum: aktif
etki_alani: ["dikey"]
gozden_gecirme: "kira-bae kazanma oranı >= %60"
guncelleme: 2026-07-24
---
# KR-002: Dikey sırası

## Bağlam
Playbook motoru dikey-bağımsız tasarlandı (bkz. one-pager, "Hendek"); ama hangi dikeyin gerçek
müşteriye açık olacağına, hangisinin demo/fikstür kalacağına karar vermemiz gerekiyor.

## Seçenekler
- Aynı anda birden fazla dikeyi aktive et — hız kazanılır ama playbook/taktik verisi her dikeyde
  soğuk başlar, hiçbirinde derinlik oluşmaz
- Tek dikeyde derinleş, ikinciyi demo/fikstür olarak tut — playbook verisi (hendek) tek yerde birikir

## Karar
`kira-bae` birincil ve tek gerçek müşteriye açık dikey; `arac-bae` demo statüsünde
(`vault/07-Fiyatlama/arac-bae.md`'de `durum: demo`) — gerçek vakalarda kullanılmaz, sadece
motorun dikey-bağımsızlığını göstermek için var.

## Gerekçe
Hendek (bkz. one-pager) satıcı-bazlı playbook verisidir; veri tek dikeyde biriktiğinde daha hızlı
derinleşir. İkinci dikeyi erken açmak bu birikimi seyreltir.

## Başarı kriteri (gözden geçirmede neye bakılacak)
`kira-bae`'de kazanma oranı ≥%60 olmadan dikey 2 (`arac-bae` veya başka bir dikey) aktive edilmez.
