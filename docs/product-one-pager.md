# Ürün & Fiyatlama One-Pager

**Ürün (çalışma adı):** Pazarlık Ajanı · **Dikey 1:** BAE Kira · **Tarih:** Temmuz 2026

---

## Ne yapar

Kullanıcı WhatsApp'a ne istediğini yazar ("kiram 100K'ya çıktı, düşür"). AI ajan kullanıcı adına ev sahibi/emlakçıyla yazılı pazarlığı yürütür, en iyi anlaşmayı onaya sunar. Kullanıcı tek bir sohbet görür; perde arkasında 4 uzman subagent (Stratejist, Yazıcı, Kritik, Analist) + insan onay katmanı + sürekli öğrenen taktik kütüphanesi (Obsidian vault) çalışır.

**Konumlandırma:** "Pactum for consumers" — kurumsal pazarlık otomasyonunun tüketici versiyonu. Küresel rakip haritasında çoklu-dikey tüketici oyuncusu yok (CarEdge=sadece araç/ABD, Pine=sadece fatura/ABD).

## Neden BAE kira

| Kriter | Durum |
|---|---|
| İşlem büyüklüğü | Yıllık kira 60-200K AED, pazarlık payı 4-8K AED |
| Fiyat opaklığı | Yüksek — RERA endeksi var ama uygulanmıyor |
| Yazılı kanal | WhatsApp ticaretin ana dili |
| Tekrar | Her yıl yenileme = doğal abonelik |
| Rekabet | AI ajan yok; insan aracılar pahalı |

## Kullanıcı akışı

1. WhatsApp'a yaz → Intake ajanı 4-5 mesajda brief'i toplar
2. Özet + ücret onayı → vaka açılır
3. Ajan pazarlığı yürütür, kullanıcıya durum mesajları düşer
4. Anlaşma → tasarruf raporu → ödeme (Stripe)
5. Hafıza: ikinci vakada ajan kullanıcıyı tanır (tercih, risk toleransı, geçmiş)

## Birim ekonomi (vaka başı)

| Kalem | Tutar |
|---|---|
| Gelir (tasarrufun %25'i, min 500 AED) | 1.000-2.000 AED (~$270-540) |
| Claude API (Sonnet+Haiku karışımı) | $3-6 |
| WhatsApp Cloud API | <$1 |
| Ödeme komisyonu (Stripe) | ~%3 |
| **Brüt marj** | **%95+** |
| Kısıt | Operatör onay süresi (~30-60 dk/vaka) → V3'te güven skorlu otomatik onay |

Sabit giderler: hosting ~$50/ay, market intel API (V2) ~$200-500/ay.

## Monetizasyon

1. **Başarı ücreti (ana):** tasarrufun %25'i, min 500 AED — "kazandırmazsak ödemezsin"
2. **Sabit ücret:** 750 AED peşin (risk sevmeyen segment + nakit akışı)
3. **Abonelik (V2):** 99-199 AED/yıl — yenileme takibi + yıl boyu tüm pazarlıklar; hafıza değeri churn'ü düşürür
4. **Veri yan geliri:** anonimleştirilmiş çok-turlu müzakere transcript'leri → AI laboratuvarlarına lisans (Datora envanteri). Her vaka çift değer üretir.

## Yol haritası

- **Şimdi:** motor + intake hazır (66/66 test), deploy + sandbox uçtan uca test sırada
- **+2 hafta:** 5 ücretsiz pilot
- **+1 ay:** 20 ücretli vaka, birim ekonomi doğrulama
- **+3 ay:** güven skorlu yarı-otomatik onay, abonelik lansmanı
- **+6 ay:** Dikey 2 (BAE araç veya sağlık faturası) — playbook motoru dikey-bağımsız tasarlandı

## Hendek

Model değil, **satıcı-bazlı playbook verisi**: hangi taktik hangi karşı taraf arketipinde işliyor — her vaka ile bileşik büyüyen, soğuk başlayan rakibin kopyalayamayacağı varlık. Agent-to-agent pazarlık çağı geldiğinde (CarEdge ilk alıcı-AI/satıcı-AI işlemini yaptı bile) en çok gerçek müzakere verisine sahip olan kazanır.
