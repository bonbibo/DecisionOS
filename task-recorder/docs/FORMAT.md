# Görev Klasörü Formatı (v1)

Her görev, kök kayıt dizini altında tek bir klasördür: `<root>/<task_id>/` burada
`task_id = <yyyyMMdd-HHmmss>_<kısa-slug>` (örn. `20260807-143012_fix-navmesh-bug`).

```
<task_id>/
  task.json              # görev meta verisi (aşağıda)
  git_meta.json           # başlangıç/final commit + branch bilgisi
  git_diff_start.patch    # Start anındaki uncommitted diff (varsa)
  git_diff_end.patch      # Stop anındaki uncommitted diff (varsa)
  input_events.jsonl      # fare + klavye ham olayları, satır satır JSON
  unity_events.jsonl      # Unity Editor olayları + Console logları, satır satır JSON
  session_pointer.json    # Recorder'ın Unity plugin'e "buraya yaz" dediği dosya (Unity proje kökünde de bir kopyası olabilir)
  screen.<ext>            # OBS'in ürettiği video dosyası (Recorder tarafından buraya taşınır/kopyalanır)
  buyer_manifest.json     # tools/to_buyer_format.py çıktısı (opsiyonel, sonradan üretilir)
```

## `task.json`

```json
{
  "task_id": "20260807-143012_fix-navmesh-bug",
  "description": "NavMesh agent'ların kapı eşiğinde takılması sorununu düzelt",
  "repo_path": "C:\\Projects\\MyGame",
  "started_at": "2026-08-07T14:30:12+03:00",
  "ended_at": "2026-08-07T15:12:44+03:00",
  "success": "success",
  "success_note": "Kök neden bulundu, NavMeshObstacle carve ayarı düzeltildi",
  "recorder_version": "0.1.0"
}
```

`success` ∈ `{"success", "partial", "failed", "incomplete"}`. `incomplete`: Stop hiç çağrılmadan uygulama
kapandıysa Recorder bir sonraki açılışta bu değeri otomatik yazar (crash recovery).

## `git_meta.json`

```json
{
  "branch": "feature/navmesh-fix",
  "start_commit": "a1b2c3d4...",
  "end_commit": "a1b2c3d4...",
  "start_dirty": true,
  "end_dirty": false
}
```

## `input_events.jsonl` (satır formatı)

```json
{"t": 1723030212.481, "type": "mouse_move", "x": 812, "y": 430}
{"t": 1723030212.910, "type": "mouse_down", "x": 812, "y": 430, "button": "left"}
{"t": 1723030213.002, "type": "mouse_up", "x": 812, "y": 430, "button": "left"}
{"t": 1723030213.500, "type": "key_down", "key": "Ctrl", "combo": ["Ctrl", "S"]}
```

## `unity_events.jsonl` (satır formatı)

```json
{"t": 1723030220.0, "type": "play_mode_changed", "state": "EnteredPlayMode"}
{"t": 1723030225.3, "type": "scene_opened", "scene": "Assets/Scenes/Level1.unity"}
{"t": 1723030230.1, "type": "compile_finished", "success": true, "warnings": 2, "errors": 0}
{"t": 1723030235.7, "type": "console_log", "level": "Error", "message": "NullReferenceException...", "stack_trace": "..."}
```

## Tasarım notları

- **Append-only + periyodik flush:** Her iki JSONL yazıcısı da satırı hemen diske flush eder (crash-safe);
  buffer'da veri tutulmaz.
- **Saat senkronu:** Tüm zaman damgaları Unix epoch (float, saniye). Recorder ve Unity plugin farklı
  process'ler olduğu için mutlak saat kullanılır, göreli sayaç değil.
- **Video dosyası taşınmıyor/kopyalanmıyor değil:** OBS kendi dosya adını seçer; Recorder Stop anında bu
  dosyayı bulup görev klasörüne taşır (aynı disk varsayımıyla rename, hızlı).
