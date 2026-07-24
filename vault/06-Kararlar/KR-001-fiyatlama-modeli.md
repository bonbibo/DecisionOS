---
karar_id: KR-001
baslik: Fiyatlama modeli
durum: aktif
etki_alani: ["fiyatlama"]
gozden_gecirme: "pilot bitişi"
guncelleme: 2026-07-24
---
# KR-001: Fiyatlama modeli

## Bağlam
İlk ücretli pilotlara girmeden önce hangi fiyatlama modelinin ana teklif olacağına karar vermemiz
gerekiyor: saf başarı ücreti mi, sabit ücret mi, yoksa hibrit mi?

## Seçenekler
- Saf başarı ücreti — risksiz ama nakit akışı yavaş, güven inşa etmesi zaman alır
- Saf sabit ücret — nakit akışı hızlı ama "kazandırmazsak ödemezsin" konumlandırmasını kaybederiz
- Hibrit — başarı ücreti ana teklif, sabit ücret risk almak istemeyen segment için alternatif

## Karar
Hibrit model: ana teklif başarı ücreti (bkz. `vault/07-Fiyatlama/kira-bae.md`), sabit ücret sadece
müşteri açıkça isterse alternatif olarak sunulur.

## Gerekçe
"Kazandırmazsak ödemezsin" konumlandırması güven inşa etmek için kritik (bkz. one-pager); sabit ücret
alternatifi nakit akışı + risk sevmeyen segmenti kaybetmemek için var, ama ana teklif değil.

## Başarı kriteri (gözden geçirmede neye bakılacak)
20 ücretli vakada: sabit/başarı ücreti seçim oranı, ücret itirazı sayısı. Sabit ücret seçim oranı
beklenenden çok yüksekse (örn. >%50) model dengesini gözden geçiririz.
