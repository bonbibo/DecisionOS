---
karar_id: KR-004
baslik: Şirket kimliği
durum: taslak
etki_alani: ["urun"]
gozden_gecirme: "isim/marka kararı verildiğinde"
guncelleme: 2026-07-24
---
# KR-004: Şirket kimliği

## Bağlam
Yazıcı ve Intake subagent'ları karşı tarafa/müşteriye "X Danışmanlık adına yazıyorum" kimliğiyle
yazıyor — bu bir yer tutucu. Gerçek isim/marka kararı henüz verilmedi.

## Seçenekler
- Kararı bekle, kod IDENTITY_NAME env değişkenini bekleyen bir yer tutucuyla çalışsın — isim kararı
  hiçbir kod değişikliği gerektirmeden, sadece env değeriyle uygulanır
- İsmi şimdiden koda göm — isim değiştiğinde kod/prompt değişikliği gerekir, deploy'a bağımlı olur

## Karar
Kod tarafı `Settings.identity_name` (env: `IDENTITY_NAME`) okur; `app/prompts/yazici.md` ve
`app/prompts/intake.md`'deki kimlik ifadeleri `{{IDENTITY_NAME}}` yer tutucusunu kullanır
(`app.subagents.load_subagent_prompt` bunu enjekte eder). İsmin NE olacağı kararı bu notta
`taslak` kalmaya devam ediyor — kod o kararı beklemeden, varsayılan bir değerle çalışır.

## Gerekçe
İsim/marka kararı ürün-dışı bir süreç (hukuki kontrol, marka müsaitliği vb.) gerektirebilir; kodun
bu sürecin sonucunu beklemesi gereksiz bir bağımlılık yaratır. Env-driven yaklaşım kararı
bloklamadan ilerlemeyi sağlar.

## Başarı kriteri (gözden geçirmede neye bakılacak)
İsim kararı verildiğinde: `IDENTITY_NAME` prod env'de güncellenir, bu not `aktif`'e çekilir, kararı
ve seçilen ismi buraya yazılır.
