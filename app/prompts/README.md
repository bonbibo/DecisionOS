# Subagent Sistem Promptları

Konum önerisi: repo'da `app/prompts/*.md` — engine her çağrıda ilgili dosyayı okur (hot-reload: prompt değişikliği = git push, kod değişikliği yok).

## Akış (bir tur)
```
Gelen mesaj → Analist(JSON) → state güncelle
→ Yazıcı(taslak JSON) → Kritik(verdict)
   APPROVE  → HITL onay kuyruğu → gönder
   REVISE   → Yazıcı'ya revision_note ile tekrar (max 2)
   REJECT   → Stratejist'i yeniden çağır (plan revizyonu)
   ESCALATE → operatöre devir
```

Stratejist yalnız vaka açılışında + REJECT sonrası çağrılır.
Tüm subagent'lar SADECE JSON döndürür → engine parse eder; parse hatasında 1 retry, sonra ESCALATE.
Model önerisi: Yazıcı/Stratejist için sonnet, Analist/Kritik için haiku yeterli olabilir — maliyet ölçümüyle karar ver.
