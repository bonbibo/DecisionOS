# Basitleştirilmiş Kapsam (v1)

Karar: şifre / kişisel bilgi / API key sistemin hiçbir noktasından geçmiyor → maskeleme, cloud, kullanıcı
hesabı, disk şifreleme katmanları kapsam dışı.

## Sistem sadece

1. **Start Task / Stop Task** — Recorder tray app'inde iki komut. Start: görev açıklaması sorulur, klasör
   açılır, git başlangıç snapshot'ı alınır, OBS kaydı başlatılır, hook'lar aktive olur. Stop: OBS kaydı
   durdurulur, git final diff alınır, başarı durumu (evet/hayır/kısmi) sorulur, `task.json` finalize edilir.
2. **Lokal ekran kaydı** — OBS Studio, `obs-websocket` (v5) üzerinden Recorder tarafından start/stop edilir.
   Recorder video dosyasını encode etmez; sadece OBS'i tetikler ve OBS'in yazdığı dosyanın yolunu görev
   klasörüne kaydeder/taşır.
3. **Fare koordinatları ve tıklamalar** — Win32 `WH_MOUSE_LL` low-level hook. Hareket örnekleme (throttled,
   örn. 30 Hz) + her tıklama olayı ham olarak. `input_events.jsonl`.
4. **Klavye tuşları/kısayolları** — Win32 `WH_KEYBOARD_LL` low-level hook. Tuş + modifier state (Ctrl/Alt/
   Shift/Win). `input_events.jsonl`'de aynı akışta, `type: "key"`.
5. **Unity Editor olayları ve Console logları** — Unity Editor eklentisi: `EditorApplication.playModeStateChanged`,
   `EditorSceneManager.sceneOpened/sceneClosed`, `CompilationPipeline` derleme başlangıç/bitiş, ve
   `Application.logMessageReceived` (Log/Warning/Error/Exception). `unity_events.jsonl`.
6. **Git başlangıç/final diff'i** — Recorder, Start'ta hedef repo yolunda `git rev-parse HEAD` +
   `git diff` (uncommitted) alır; Stop'ta aynısını tekrarlar. İki diff + iki commit hash + branch adı
   `git_meta.json` ve `git_diff_start.patch` / `git_diff_end.patch` olarak yazılır.
7. **Görev açıklaması ve başarı durumu** — Start'ta serbest metin açıklama, Stop'ta başarı enum'u
   (`success` / `partial` / `failed`) + opsiyonel not. `task.json`.
8. **Doğrudan HDD'ye kayıt** — Her şey, konfigüre edilebilir bir kök dizin altında (örn. `D:\TaskRecordings\`)
   `<task_id>/` klasörüne senkron/append-only dosya yazımıyla iner. Ağ çağrısı yok, buffer'lar periyodik
   flush edilir (crash'te veri kaybını sınırlamak için).

## Kapsam dışı (bilinçli)

- Kullanıcı hesabı / login
- Cloud senkron / sunucu / API
- Dashboard / UI raporlama (buyer format dönüşümü offline script ile yapılır)
- PII maskeleme (girdi olarak PII toplanmıyor varsayımı — ekran kaydı görsel olarak içerik gösterebilir,
  bu bilinen ve kabul edilen bir risktir, kullanıcıya Start ekranında hatırlatılır)
- Disk şifreleme (işletim sistemi seviyesinde ele alınır, bu araç sorumlu değil)

## Zaman çizelgesi (kaba)

- **Gün 1-2:** Recorder iskeleti — tray UI, Start/Stop akışı, `task.json`/`git_meta.json` yazımı, git diff
  komutları.
- **Gün 3:** Global mouse/keyboard hook + `input_events.jsonl` (throttle + flush).
- **Gün 4:** OBS WebSocket entegrasyonu (start/stop recording, dosya yolu callback).
- **Gün 5:** Unity Editor plugin — event hook'ları + Console log yakalama + JSONL yazımı, `session_pointer.json`
  okuma.
- **Gün 6-7:** Uçtan uca duman testi (gerçek görev kaydı), `to_buyer_format.py` ilk sürüm.
- **+1 hafta (stabilizasyon):** Hata durumları (OBS kapalıysa/bağlanamıyorsa, git repo yoksa, disk doluysa),
  crash recovery (Stop çağrılmadan uygulama kapanırsa klasör "incomplete" işaretlenir), temel dokümantasyon.

## Buyer format dönüşümü

`tools/to_buyer_format.py`, bir görev klasörünü okuyup satılabilir/paylaşılabilir tek bir özet
(`buyer_manifest.json`) üretir: süre, event sayıları, git özeti, video dosya adı + checksum. Ham event
dosyaları (`input_events.jsonl`, `unity_events.jsonl`) olduğu gibi kalır; script bunları silmez/değiştirmez,
sadece üstüne bir özet ekler. Alıcıya özgü şema farklıysa bu script'in çıktısı ara format olarak kullanılır.
