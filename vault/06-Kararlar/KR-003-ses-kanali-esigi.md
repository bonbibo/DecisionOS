---
karar_id: KR-003
baslik: Ses kanalı eşiği
durum: taslak
etki_alani: ["urun", "kanal"]
gozden_gecirme: "eskalasyonların %40'ı telefon talebi olduğunda"
guncelleme: 2026-07-24
---
# KR-003: Ses kanalı eşiği

## Bağlam
Karşı taraflar zaman zaman telefonla konuşmak istiyor (Kritik madde 7 — eskalasyon sinyali).
Ses kanalına (sesli arama/IVR) ne zaman yatırım yapılacağına dair kararı hislere göre değil,
ölçülebilir bir eşiğe bağlamamız gerekiyor.

## Seçenekler
- Şimdiden ses kanalına yatırım yap — büyük mühendislik + uyum (kayıt izni, KVKK/GDPR) maliyeti,
  spekülatif; henüz gerçek talebin ne kadar büyük olduğunu bilmiyoruz
- Hiç yatırım yapma, telefon taleplerini her zaman eskalasyonla insan operatöre yönlendir — basit
  ama talep gerçekten büyükse operatör darboğazı oluşturur
- Eşik tanımla, eşik aşılana kadar bekle — kararı veriye bağlar, erken yatırım riskini önler

## Karar
Ses kanalına (sesli arama/IVR) yatırım yapılmaz, ta ki eskalasyon nedenleri arasında "telefon
talebi" (Kritik madde 7'nin `phone_request` alt kategorisi — bkz. `Case.escalation_category`,
`app.orchestrator._categorize`) oranı toplam eskalasyonların **%40'ını GEÇENE** kadar.

## Ölçüm
`scripts/daily_report.py` / `reports/YYYY-MM-DD.md`'deki eskalasyon kırılımı kaynak alınır:
`phone_request` kategorisindeki eskalasyon sayısı / toplam eskalasyon sayısı. Bu depoda kod
sadece bu oranı ölçülebilir/raporlanabilir kılar — yatırım kararının kendisini vermez, o
insan kararıdır.

## Gerekçe
Ses kanalı büyük mühendislik + uyum yatırımı ister; erken yapılırsa spekülatif kalır. Telefon
talebi oranı zaten "karşı taraf bizi insan sanıp arayı istiyor" sinyalinin ölçülebilir vekilidir —
gerçek talep büyüdükçe bu oran da büyür.

## Başarı kriteri (gözden geçirmede neye bakılacak)
`phone_request` oranı %40'ı geçtiğinde bu karar gözden geçirilir ve (durum aktif'e çekilir ya da
eşik güncellenir).
