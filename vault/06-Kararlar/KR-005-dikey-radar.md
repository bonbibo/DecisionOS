---
karar_id: KR-005
baslik: Dikey genişleme radarı ve aktivasyon kapıları
durum: aktif
etki_alani: ["dikey", "urun"]
gozden_gecirme: 2026-10-01
guncelleme: 2026-07-25
---
# KR-005: Dikey Radarı

## Bağlam
Pazarlık edilebilirlik sıralaması (kriter: işlem büyüklüğü × fiyat opaklığı × yazılı kanal uygunluğu × tekrar):

| Sıra | Dikey | Not | Durum |
|---|---|---|---|
| 1 | Kira (BAE) | Canlı — birincil | aktif |
| 2 | Araç (BAE) | Playbook hazır | demo |
| 3 | Sağlık/diş (sigortasız, BAE) | Klinikler arası teklif farkı %40; hassas veri → KVKK/HIPAA-benzeri süreç gerekir | radar |
| 4 | Okul ücretleri (BAE) | Yıllık, tekrar eden, veli segmenti = kira müşterisiyle aynı | radar |
| 5 | Düğün/etkinlik | Yüksek tutar, sezonluk | radar |
| 6 | İkinci el (Dubizzle) | Abonelik girişi ürünü olarak | taslak |
| 7 | Ev tadilat/usta teklifleri | Teklif toplama doğal uyum | radar |
| 8 | Mobilya/beyaz eşya (mağaza) | Orta tutar, kampanya dönemli | radar |

## Karar
- Kira'da kazanma oranı ≥%60 VE ≥20 kapanmış vaka olmadan hiçbir demo dikey müşteriye açılmaz (KR-002 ile tutarlı)
- İkinci el aboneliği (KR-005 kapısı): kira+araç canlıyken, operatör yükü vaka başı <15 dk'ya düştüğünde açılır
- Sağlık dikeyi hukuk görüşü olmadan (hassas veri) radar'dan çıkamaz

## Başarı kriteri
Her yeni dikey ilk 10 vakada: kazanma ≥%50, müşteri tasarrufu > ücretin 3 katı.
