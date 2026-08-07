# Task Recorder — Yerel Görev Kayıt Sistemi

> **Bu, DecisionOS (vault-driven pazarlık ajanı platformu) ile ilgisiz, bağımsız bir alt-proje.**
> `app/`, `vault/`, `alembic/` altındaki DecisionOS koduna dokunmaz; DecisionOS testleri/migration/vault
> kuralları bu klasör için geçerli değildir. Aynı repo içinde tutuluyor çünkü çalışma oturumu bu repo/branch'e
> pinlenmiş; mantıksal olarak ayrı bir üründür.

## Ne yapar

Unity geliştiricisinin bir görevi (task) yaparken ürettiği tüm sinyalleri, gözetimsiz ve internetsiz şekilde
yerel diske kaydeder. Amaç: sonradan "buyer format"a (bir alıcı/veri seti tüketicisinin beklediği şemaya)
dönüştürülebilecek ham görev kayıtları üretmek.

**Kasıtlı olarak dışarıda bırakılanlar:** kullanıcı hesabı, cloud/sunucu, dashboard, disk şifreleme, PII/şifre
maskeleme, API key yönetimi. Sebep: sistem hiçbir zaman şifre/kişisel veri/API key işlemiyor — bunlar girdi
olarak sisteme hiç girmiyor, o yüzden maskeleme veya şifreleme katmanı gereksiz karmaşıklık.

## Bileşenler

| Bileşen | Dil/Platform | Sorumluluk |
|---|---|---|
| `Recorder/` | C# / .NET (Windows, WinForms tray app) | Start/Stop Task, global mouse+klavye hook, OBS WebSocket ile ekran kaydı start/stop, git diff snapshot, görev klasörü yazımı |
| `UnityPlugin/Editor/` | C# / Unity Editor script | Unity Editor olayları (play mode, sahne değişimi, derleme) + Console log akışını görev klasörüne yazar |
| `tools/to_buyer_format.py` | Python | Bir görev klasörünü okuyup tek bir `buyer_manifest.json` özetine dönüştürür |

Bağımlılık yönü tek yönlü: Recorder görev klasörünü ve `session_pointer.json`'ı oluşturur → Unity plugin bu
pointer'ı okuyup aynı klasöre yazar. İki taraf arasında ağ/IPC yok, sadece dosya sistemi.

## Görev klasörü formatı

Bkz. [`docs/FORMAT.md`](docs/FORMAT.md).

## Durum

Bu, mimari kararın kod iskeletidir — 5-7 günlük ilk sürümün planı `docs/SPEC.md`'de. C#/Unity parçaları bu
ortamda derlenip test edilemedi (Windows/.NET SDK/Unity yok); bir geliştirme makinesinde derleme + gerçek
OBS/Unity ile duman testi gerekir. `tools/to_buyer_format.py` bu ortamda yazıldı, çalıştırıldı ve test edildi
(`tests/test_to_buyer_format.py`, `pytest -q` ile).
