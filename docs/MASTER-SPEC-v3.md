# MASTER-SPEC-v3 — F-K Paketleri

> **Köken notu:** Bu dosya, kullanıcının sohbette verdiği F-K madde özetinden
> (zip'te yalnızca `AUTONOMOUS-RUN.md` + `CLAUDE.md` + agent/skill iskeleti
> geldi, spec'in kendisi gelmedi) Claude Code tarafından v2 (`SYSTEM UPDATE
> v2`, PR-A..E) tarzında, uygulanabilir seviyede yazıldı. Stripe (Paket G) ve
> WhatsApp opt-in guard (Paket H) gibi para/uyumluluk riski taşıyan kısımlarda
> yapılan varsayımlar **"Varsayım:"** etiketiyle işaretlidir — bunlar
> onaylanmadan o paketin ilgili maddesi kodlanmaz.
>
> Bu depoda daha önce commit edilen "PR-F: human-in-the-loop question/answer +
> LLM call dataset" işi bu dosyadaki **Paket F (Market Intel)** ile aynı şey
> DEĞİL — v2'nin doğal bir uzantısıydı, harf çakışması tesadüf. Bu belgede
> harfler sadece F-K paketlerini işaret eder.

## Konum ve öncelik

`autonom/CLAUDE.md`'nin belirttiği hiyerarşi geçerli: bu dosya >
`SYSTEM UPDATE v2` (sohbette verilmişti, `docs/`'a asıl metin olarak hiç
yazılmamıştı — README zaten onun uygulanmış halini belgeliyor) > diğer
dosyalar. Çakışma çıkarsa PR açıklamasına yazılır.

## Ortak kurallar (v2'den değişmeden devam eder)

1. Vault'a kod içinden yazma yok (istisnalar bu belgeyle genişler: `05-Metrikler/dashboard.md` + **Paket F'nin `09-Piyasa-Verisi/*.md`'si** — ikisi de "insan yazmaz, script üretir" sınıfında).
2. Fiyat/taktik/segment/karar/şablon metni hardcode yok.
3. Karşı tarafa opt-in'siz WhatsApp gönderimi kod seviyesinde imkânsız (Paket H bunu somutlaştırıyor).
4. Her davranış değişikliği testli; mevcut testler kırılmaz (şu an 127/127 yeşil — bu sayı her paket sonunda büyümeli, küçülmemeli).
5. Migration'lar geri alınabilir (upgrade+downgrade doğrulanır) — `migration-disiplini` skill'i burada da geçerli.
6. Secret'lar sadece env'den.
7. Subagent'lar sadece JSON döndürür.
8. `subagent-kontrati` ve `vault-mantigi` skill'leri F-K boyunca da geçerli (Kritik'in numaralı checklist'i SONA ekleme kuralı dahil).

## Paket sırası ve onay modu

F → G → H → I → J → K, sırayla. Onay modu: **AUTONOMOUS-RUN.md protokolü**
(paketler arası durmadan ilerle; sadece hepsi bitince, bir paket 3 denetim
turunda hâlâ FAIL veriyorsa, ya da git/ortam felaketinde dur). Gerçek
hesap/anahtar gerektiren maddeler (Stripe, Meta/WhatsApp template onayı,
gerçek Property Finder/Bayut erişimi, Railway cron, Resend/e-posta gönderim
hesabı) kod + mock/fixture testiyle TAMAMLANIR; canlı entegrasyon
`docs/PROGRESS.md`'ye "İNSAN GEREKLİ: <ne>" olarak yazılır, paket buna
takılmadan geçilir.

---

## Paket F — Market Intel

**Amaç:** Stratejist'in çıpa/hedef hesaplarken kullandığı `INTEL` alanı bugün
her zaman boş (`{}`) — hiçbir çağıran doldurmuyor. F, karşılaştırılabilir
piyasa verisini (Property Finder / Bayut ilan fiyatları) otomatik toplayıp
Stratejist'e günlük tazelenen gerçek veri olarak besler.

### Mimari kararı

Piyasa verisi *üretilen* içeriktir, insan tarafından yazılmaz — tıpkı
`05-Metrikler/dashboard.md` gibi. Aynı deseni tekrar ederiz: script
topluyor, vault'a yazıyor, `VaultReader` okuyor. Yeni bir "intel reader"
icat etmeye gerek yok.

**Basitleştirme (V1):** bölge bazlı değil, **dikey bazlı** tek agregasyon
(`vault/09-Piyasa-Verisi/<dikey>.md`). Bölge (Dubai Marina vs JVC vb.)
kırılımı gerçek trafikte ihtiyaç görülürse V2'de `Case.area` alanı + intake
sorusu eklenerek yapılır — şimdi eklemek intake kontratını büyütür, spec'te
istenmedi.

### Adaptörler (`app/intel/`)

```
app/intel/
  __init__.py         Listing dataclass, Adapter Protocol
  property_finder.py   PropertyFinderAdapter
  bayut.py              BayutAdapter
  aggregate.py           adapters'tan MarketIntel üretir + vault'a yazar
```

```python
@dataclass
class Listing:
    price: float
    currency: str
    bedrooms: int | None
    url: str

class Adapter(Protocol):
    async def fetch_listings(self, dikey: str) -> list[Listing]: ...
```

- `PropertyFinderAdapter` / `BayutAdapter`: **Crawlee (Python paketi,
  `pip install crawlee`)** + bu ortamda zaten kurulu Playwright ile
  (`PLAYWRIGHT_BROWSERS_PATH` ayarlı, bkz. ortam notları) `PlaywrightCrawler`
  kullanır. Gerçek site seçicileri (CSS/XPath) test sırasında elde
  edilemeyeceğinden (canlı siteye gitmek scope dışı — bkz. Dış bağımlılık
  kuralı) adaptörler **injectable bir `fetch_fn` seam**'i ile yazılır (tıpkı
  `AnthropicSubagentClient`'ın `client` param'ı gibi): gerçek Crawlee çağrısı
  `_default_fetch()` içinde, testler sahte HTML/JSON fixture'larıyla
  `Adapter(fetch_fn=...)` enjekte eder. **İNSAN GEREKLİ:** gerçek CSS
  seçicilerin siteye bakılarak doğrulanması + ToS/robots.txt kontrolü —
  kod hazır, canlı doğrulama insan işi.
- `aggregate.py::run_intel(vault_dir="vault") -> None`: her aktif dikey için
  (vault'taki `07-Fiyatlama/*.md` `durum: aktif` olanlar) iki adaptörü
  çağırır, `ortalama/min/max` hesaplar, `vault/09-Piyasa-Verisi/<dikey>.md`
  yazar:

  ```yaml
  ---
  intel_id: PV-kira-bae
  dikey: kira-bae
  ortalama_kira: 92500
  min_kira: 78000
  max_kira: 115000
  para_birimi: AED
  ilan_sayisi: 34
  kaynaklar: [property-finder, bayut]
  toplanma_tarihi: 2026-07-25
  durum: aktif
  ---
  Otomatik toplanmış piyasa özeti — elle düzenlenmez.
  ```

### Entegrasyon

- `vault/_manifest.md`: `stratejist` rolüne `"09-Piyasa-Verisi"` eklenir.
- `app/orchestrator.py`: yeni `_get_intel(case, vault_dir) -> dict` (tıpkı
  `_get_segment` gibi) — `VaultReader(vault_dir).read_folder("09-Piyasa-Verisi")`
  içinde `frontmatter.dikey == case.vertical and frontmatter.durum ==
  "aktif"` olan dosyayı bulur, frontmatter'ı döner (yoksa `{}`).
  `run_turn`'ün `intel` parametresi `None` ise (mevcut varsayılan) artık
  otomatik `_get_intel(...)` çağrılır — çağıranların (`whatsapp.py`,
  `web.py`, `intake.py`) hiçbirinin değişmesi gerekmez, imza aynı kalır.
  Mevcut testler vault'ta `09-Piyasa-Verisi` olmadığı sürece `{}` almaya
  devam eder — regresyon riski yok.

### Script + cron

- `scripts/run_intel.py`: `aggregate.run_intel()`'i çağıran CLI giriş
  noktası (CLAUDE.md'de zaten `python scripts/run_intel.py` olarak anıldı).
- Railway cron job (günlük, örn. `03:00 UTC`) — **İNSAN GEREKLİ**: Railway
  hesabında cron tanımı. Kod tarafında `railway.json`'a (yoksa oluşturulur)
  bir cron servis tanımı eklenir, dokümante edilir.

### Testler

- Adaptör: fixture HTML/JSON'dan `Listing` parse doğruluğu.
- `aggregate.run_intel`: iki adaptörden `MarketIntel` hesaplama +
  `vault/09-Piyasa-Verisi/<dikey>.md` dosyasının doğru frontmatter'la
  yazıldığı (geçici bir test vault dizininde).
- `_get_intel`: dosya varken/yokken/`durum: aktif` değilken davranış.
- `run_turn`: `INTEL` payload'ının artık otomatik dolduğu (Stratejist
  payload'ında).

### DoD

Kod + testler yeşil, `vault/_manifest.md` güncel, README'de "Market Intel"
bölümü, `docs/PROGRESS.md`'de Crawlee canlı doğrulama + Railway cron için
İNSAN GEREKLİ maddesi.

---

## Paket G — Stripe pre-auth → capture

**Amaç:** "Kazandırmazsak ödemezsin" modelinde risk şu: kazandırırız, müşteri
ödemez. Vaka açılışında karta ön-onay (hold) alınır, kapanışta (anlaşma
sağlandıysa) gerçek tutar tahsil edilir.

### Varsayım (onay gerekir)

- **Ön-onay tutarı = vault fiyatlama'nın `min_ucret`'i** (garanti taban),
  gerçek/nihai ücret değil — kapanışta hesaplanan gerçek ücret bundan
  yüksek çıkarsa (örn. büyük bir tasarruf sağlandıysa) Stripe kuralı gereği
  ön-onaylanandan fazlası tahsil edilemez; **V1 bu durumda tahsilat
  ön-onaylanan tutarla sınırlanır ve fark `Case.escalation_reason` tarzı bir
  nota düşülür (ikinci bir manuel tahsilat insan işi, kod kapsamı dışı)**.
  Doğru/adil çözüm (örn. ön-onayı dinamik güncellemek, `tavan_kira`'dan
  tahmini tavan ücret hesaplamak) V2'ye bırakılıyor.
- **Ödeme yöntemi toplama:** Stripe Checkout Session (hosted, `capture_
  method=manual`), link olarak müşteriye (WhatsApp/web) gönderilir — Stripe
  Elements'i kendi arayüzümüze gömmek yok (PCI kapsamı + zaman kısıtı).
- **Tetikleyici:** vaka `discovery`'den `anchoring`'e geçtiği an (yani
  `_confirm_and_create_case` / web eşdeğeri) `Payment` satırı `pending`
  olarak açılır ve checkout linki müşteriye case-created mesajının bir
  parçası olarak gider. Stratejist'in ilk çıpa taslağı **karşı tarafa
  onay kuyruğuna ön-onay tamamlanmadan da girer** (mevcut akış bozulmasın
  diye) — ama gerçek gönderim (`POST /review/{id}/approve`) ön-onay
  `pre_authorized` olmadan **409 döner** (aşağıda).

### Model / Migration

```python
class PaymentStatusEnum(str, enum.Enum):
    pending = "pending"
    pre_authorized = "pre_authorized"
    captured = "captured"
    canceled = "canceled"
    failed = "failed"

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID]
    case_id: Mapped[uuid.UUID]  # FK cases.id, unique=True (bire-bir)
    stripe_payment_intent_id: Mapped[str | None]  # unique, nullable (checkout tamamlanana kadar yok)
    stripe_checkout_session_id: Mapped[str | None]
    access_token: Mapped[str]  # unique, 32 byte urlsafe — checkout linkindeki tek kullanımlık token
    amount: Mapped[float]        # Numeric(12,2) — ön-onay tutarı (min_ucret)
    captured_amount: Mapped[float | None]
    currency: Mapped[str]        # String(3)
    status: Mapped[PaymentStatusEnum]
    created_at, pre_authorized_at, captured_at, canceled_at: Mapped[datetime | None]
```

`Case.outcome: OutcomeEnum | None` eklenir:

```python
class OutcomeEnum(str, enum.Enum):
    won = "won"      # Analist "close" önerdi (anlaşma)
    walked = "walked"  # Analist "walk" önerdi (vazgeçildi)
```

`_apply_recommended_state` (orchestrator.py) genişler: `recommended_state
== "walk"` → `case.outcome = OutcomeEnum.walked`; `recommended_state ==
"close"` → `case.outcome = OutcomeEnum.won`. Diğer state'lerde dokunulmaz.

### `app/payments.py`

```python
class StripeClient(Protocol):  # gerçek stripe SDK'sı bu şekli sağlar; testte sahte enjekte edilir
    def create_checkout_session(self, amount_cents, currency, metadata) -> CheckoutSession: ...
    def capture_payment_intent(self, id, amount_to_capture_cents) -> PaymentIntent: ...
    def cancel_payment_intent(self, id) -> PaymentIntent: ...
    def construct_webhook_event(self, payload, sig_header, secret) -> Event: ...

def create_pre_auth(db, case, pricing: dict, stripe: StripeClient | None = None) -> Payment: ...
def capture_for_won_case(db, case, stripe: StripeClient | None = None) -> Payment | None: ...
def cancel_for_walked_case(db, case, stripe: StripeClient | None = None) -> Payment | None: ...
def compute_success_fee(case, pricing: dict) -> float:
    """savings = max(0, ilk_karsi_teklif - son_anlasma_fiyati); fee = max(min_ucret, savings * basari_yuzdesi/100)"""
```

`run_turn`'e (orchestrator.py) bir kanca eklenir: state `close` olduğunda ve
`case.outcome is OutcomeEnum.won` ve `case.payment` `pre_authorized` ise,
çağıran (whatsapp.py/web.py/review answer endpoint) `payments.
capture_for_won_case(db, case)` çağırır — bu, run_turn'ün kendisine değil,
run_turn'ü saran handler'lara eklenir (run_turn saf kalır, DB/Stripe yan
etkisi yok — mevcut mimari ilkeyle tutarlı: run_turn zaten "callers persist"
diyor). `outcome is walked` ise aynı yerde `cancel_for_walked_case` çağrılır
(ön-onayı serbest bırak).

### Endpoint'ler

- `GET /payments/checkout/{token}` — public, auth yok (token tek kullanımlık
  ve tahmin edilemez). Stripe Checkout Session URL'ine 302 redirect (ya da
  session zaten yoksa oluşturup redirect).
- `POST /payments/webhook` — Stripe imza doğrulaması (`Stripe-Signature`
  header, `STRIPE_WEBHOOK_SECRET`) — WhatsApp'ın `X-Hub-Signature-256`
  deseninin birebir eşleniği. `checkout.session.completed` →
  `Payment.status = pre_authorized`, `stripe_payment_intent_id` set edilir.
  `payment_intent.payment_failed` → `status = failed`.
- Admin panel: `/admin/payments` liste, case detayında ödeme durumu +
  manuel `POST /admin/cases/{id}/payment/capture|cancel` (operatör
  override — otomatik tetikleyici bir vakayı kaçırırsa).

### Guard

`app/review.py::approve()` içine: `item.audience is AudienceEnum.
counterparty` VE case'in vertical'i vault'ta ücretli (aktif `07-Fiyatlama`
kaydı var) İSE `case.payment is None or case.payment.status not in
{pre_authorized, captured}` → `409 "payment pre-authorization required"`.
Demo/ücretsiz vakalar (`case.is_demo` veya pricing yok) bu kontrolden muaf.

### Testler

- `compute_success_fee` hesap doğruluğu (savings/floor/cap senaryoları).
- `create_pre_auth` → sahte Stripe client ile Payment satırı + doğru tutar.
- Webhook: geçerli/geçersiz imza, `checkout.session.completed` durumu.
- `_apply_recommended_state`: walk → outcome=walked, close → outcome=won.
- Capture-on-win, cancel-on-walk uçtan uca (sahte Stripe client).
- `approve()` guard: ön-onaysız counterparty gönderimi 409.
- Ön-onaylanandan fazla hesaplanan ücretin capture'da tavana çekildiği +
  not düşüldüğü senaryo.

### DoD

Kod + testler yeşil, migration doğrulandı, `.env.example`'a
`STRIPE_SECRET_KEY`/`STRIPE_PUBLISHABLE_KEY`/`STRIPE_WEBHOOK_SECRET`,
README'de akış diyagramı, `docs/PROGRESS.md`'de gerçek Stripe hesabı +
webhook URL kaydı için İNSAN GEREKLİ.

---

## Paket H — E-posta-önce ilk temas + opt-in guard

**Amaç:** Karşı taraf (ev sahibi) bizimle hiç konuşmamışken WhatsApp'tan
soğuk mesaj atmak Meta politikasına aykırı (business-initiated + opt-in yok)
ve numarayı banlatma riski taşır. Çözüm: ilk temas **e-posta** ile (opt-in
duvarı yok), e-postadaki link karşı tarafı kendi isteğiyle WhatsApp'ı
AÇMAYA yönlendirir ("click-to-WhatsApp") — bu durumda mesajı ilk gönderen
KARŞI TARAF olur, yani Meta'nın gördüğü şey kullanıcı-başlatan bir konuşma
olur, business-initiated değil. Bu hem politikaya uygun hem de "gerçek
opt-in" — ayrı bir onay mekanizması icat etmeye gerek yok.

### Varsayım (onay gerekir)

- Click-to-WhatsApp linki (`https://wa.me/<numaramız>?text=...`) tek
  başına yeterli opt-in sayılıyor: karşı taraf tıklayıp WhatsApp'tan bize
  ilk mesajı attığı an gerçek opt-in gerçekleşmiş olur. `/optin/{token}`
  sayfasına sadece TIKLAMAK (WhatsApp'ı açmadan) opt-in SAYILMAZ — kayıt
  edilir (`opt_in_method=email_link_click`) ama guard bunu tek başına
  yeterli görmez; guard'ın gerçek şartı her zaman "bu numaradan bize gelen
  bir inbound mesaj var" (Meta'nın 24 saatlik servis penceresi mantığıyla
  birebir).
- Bu nedenle **guard'ın tek gerçek kaynağı**: `messages` tablosunda
  `direction=inbound, channel=whatsapp, sender=<recipient>` olan ve
  `created_at` 24 saatten yeni bir satırın var olması. `OptIn` tablosu ek
  kanıt/denetim izi içindir, guard mantığının birincil kaynağı değildir.

### Model / Migration

```python
class OptInMethodEnum(str, enum.Enum):
    whatsapp_first_message = "whatsapp_first_message"
    email_link_click = "email_link_click"
    manual_operator = "manual_operator"

class OptIn(Base):
    __tablename__ = "opt_ins"
    id, case_id (nullable FK), contact: str, channel: ChannelEnum,
    method: OptInMethodEnum, created_at
```

`Case.counterparty_email: Mapped[str | None]` eklenir (yeni sütun,
nullable). `app/intake.py`'nin `collected_fields` sözleşmesine opsiyonel
`ev_sahibi_email` alanı eklenir — **kontrat genişlemesi, `subagent-kontrati`
skill'inin kuralına göre eski alan silinmiyor, sadece yeni opsiyonel alan
ekleniyor, breaking change değil.**

### Guard'ın somutlaşması

`app/channels/whatsapp.py::send_text_message` bugün `db` parametresi
almıyor — **bu spec onunla kırılan bir imza değişikliği önerir**: `db:
Session` zorunlu parametre olur. Tüm çağıranlar (`review.py::approve`,
`app/admin/__init__.py::approve`) `db`'yi zaten ellerinde tutuyor, tek
satırlık değişiklik.

```python
class OptInRequiredError(Exception):
    def __init__(self, recipient: str):
        self.recipient = recipient

def _has_valid_opt_in(db: Session, recipient: str) -> bool:
    """True <=> son 24 saatte bu numaradan inbound bir mesaj var (Meta servis
    penceresi) — yeni bir case/karşı taraf için tek gerçek opt-in kanıtı budur."""

async def send_text_message(to: str, body: str, db: Session) -> dict:
    if not _has_valid_opt_in(db, to):
        raise OptInRequiredError(to)
    ...  # mevcut gönderim mantığı değişmeden
```

`review.py::approve()` ve `app/admin/__init__.py::approve()`:
`OptInRequiredError` yakalanır → `409 "opt-in required: no inbound message
from <recipient> in the last 24h — see Paket H"`. Bu, mevcut "channel not
wired up" 501 kontrolünün yanına eklenir, onu değiştirmez.

**Önemli:** bu guard SADECE `audience=counterparty` gönderimlerinde
anlamlıdır — `audience=client` (kendi müşterimiz) zaten bize kendisi yazarak
başlattığı için her zaman geçerli bir inbound mesaj geçmişine sahiptir,
guard'ı doğal olarak geçer, ayrı bir muafiyet kodu gerekmez.

### E-posta akışı

`app/channels/email.py` genişler (bugün stub):
- `send_initial_contact_email(db, case) -> None`: `case.counterparty_email`
  doluysa, kısa bir e-posta gönderir (gövde: `docs/product-one-pager.md`
  tonuyla tutarlı, güven odaklı, tehdit içermeyen bir "X Danışmanlık adına
  arıyoruz" metni + `/optin/{token}` linki). Konu/gövde şablonu kod içinde
  sabit metin olarak kalır — bu bir *fiyat/taktik/segment/karar* değil,
  operasyonel bir e-posta şablonu, CLAUDE.md madde 2'nin kapsamına girmez
  (netlik için burada açıkça not düşülüyor).
- `GET /optin/{token}` (`app/channels/optin.py`, yeni router): Jinja sayfa
  (admin'in template altyapısı aynı şekilde kullanılır, public erişim, auth
  yok) — kısa güven metni + "WhatsApp'ta devam et" butonu
  (`https://wa.me/<WHATSAPP_PHONE_NUMBER>?text=...`). Sayfa GET'inde
  `OptIn(method=email_link_click)` kaydı düşülür (denetim izi, guard'ı tek
  başına geçirmez — yukarıya bkz).
- Case oluşturulurken (`_create_case_from_fields` ve web eşdeğeri)
  `counterparty_email` doluysa case-created sonrası `send_initial_contact_
  email` tetiklenir; boşsa **mevcut davranış hiç değişmez** (bugünkü akış
  zaten karşı tarafa WhatsApp'ı intake sırasında hiç göndermiyor, ilk
  gönderim her zaman `POST /review/*/approve` ile insan onaylı — dolayısıyla
  bugünkü sistem zaten "kör soğuk mesaj" atmıyor; H asıl riski **gelecekte
  biri approve'a basarsa ne olur** sorusuna kod seviyesinde kilit koyuyor).

### Testler

- `_has_valid_opt_in`: inbound mesaj var/yok/24h'den eski senaryoları.
- `send_text_message`: opt-in yokken `OptInRequiredError`, varken normal gönderim.
- `approve()` (review + admin): guard tetiklenince 409, mesaj içeriği.
- `send_initial_contact_email`: e-posta var/yok dallanması, gönderilen içerikte `/optin/{token}` linki.
- `GET /optin/{token}`: 200 + `OptIn` satırı oluşur, `https://wa.me/` linki sayfada var.
- Regresyon: mevcut `approve()` testleri `db` parametresi eklenmesiyle kırılmamalı (fixture güncellemesi gerekebilir, iş bu PR'da yapılır).

### DoD

Kod + testler yeşil, migration doğrulandı, README'de opt-in guard'ın
somut çalışma şekli anlatılır (bu, spec'in "kod seviyesinde imkânsız"
maddesinin nasıl sağlandığının kanıtı olarak README'de açık yazılmalı),
`.env.example`'a e-posta gönderim ayarları (mevcut Gmail ayarları
yeniden kullanılır, yeni env gerekmeyebilir), `docs/PROGRESS.md`'de gerçek
Meta "click-to-WhatsApp" davranışının canlıda doğrulanması İNSAN GEREKLİ.

---

## Paket I — Landing + waitlist

**Amaç:** Güven yüzü (kim olduğumuz, nasıl çalıştığı) + talep sinyali
(kaç kişi ilgileniyor) aynı sayfada.

### Model / Migration

```python
class WaitlistSignup(Base):
    __tablename__ = "waitlist_signups"
    id, email: Mapped[str]  # unique
    phone: Mapped[str | None]
    note: Mapped[str | None]
    source: Mapped[str | None]  # ör. "landing", "twitter" — query param'dan
    created_at
```

### Endpoint'ler + sayfa

- `GET /` — public landing (Jinja, `app/public/templates/`, admin'den ayrı
  bir template dizini — public sayfa asla auth gerektirmemeli, admin'in
  Basic-auth'lu router'ıyla karışmasın diye ayrı `app/public/` paketi).
  İçerik `docs/product-one-pager.md`'nin konumlandırmasından türetilir:
  "Kiranız yükseldi mi? Sizin adınıza pazarlık ederiz — kazandırmazsak
  ödemezsiniz." + nasıl-çalışır 3 adım + waitlist formu.
- `POST /waitlist` — `{email, phone?, note?, source?}` → `WaitlistSignup`
  satırı (aynı email tekrar gönderirse `409` değil, mevcut satırı
  günceller — waitlist'te "zaten kayıtlısın" sürtünmesi istenmez).
- `GET /waitlist/thanks` — teşekkür sayfası.
- Admin: `/admin/waitlist` liste (email, phone, source, tarih), CSV
  export'a gerek yok V1'de (spec'te istenmedi).

### Testler

- `POST /waitlist`: yeni kayıt, tekrar email → update (insert değil).
- `GET /`: 200, form alanı sayfada var.
- `/admin/waitlist`: auth gerektirir, kayıtları listeler.

### DoD

Kod + testler yeşil, README'de landing/waitlist bölümü, gerçek domain/DNS
kurulumu `docs/PROGRESS.md`'de İNSAN GEREKLİ.

---

## Paket J — Üretim sertleştirme

**Amaç:** Loglama, healthcheck, günlük işletme raporu, runbook — "gece 3'te
bir şey patlarsa ne yapılır" sorusuna kod ve doküman seviyesinde cevap.

### Loglama

`app/main.py`'ye JSON log formatter (stdlib `logging` + basit bir
`JsonFormatter` — yeni bağımlılık gerekmez) ve bir `request_id` middleware
(her istek `X-Request-Id` header'ı ile, yoksa üretilir, tüm log satırlarına
eklenir — hata ayıklamada bir isteğin tüm log izini bulmayı sağlar).
Secret'ların (ör. `REVIEW_TOKEN`, `STRIPE_SECRET_KEY`, `ANTHROPIC_API_KEY`)
log'a asla yazılmadığı bir test eklenir (CLAUDE.md madde 6'nın somut
doğrulaması).

### Healthcheck

`GET /health` (mevcut, sadece `{"status": "ok"}`) yanına `GET /health/deep`:
DB bağlantısı (`SELECT 1`), vault manifest okunabilirliği
(`VaultReader("vault")._read_manifest_roles()` warning'siz), Stripe API
erişimi (varsa key; yoksa `skipped` — Paket J, G'den sonra geldiği için
Stripe zaten var) kontrol eder, `{"status": "ok"|"degraded", "checks": {...}}` döner. Auth gerektirmez (deploy platformunun healthcheck'i genelde auth'suz çağırır).

### Günlük işletme raporu

`scripts/daily_report.py`: dünün özetini hesaplar —
- yeni vaka sayısı, kapanan vaka sayısı (won/walked kırılımı, Paket G'nin `Case.outcome`'undan),
- eskalasyon sayısı (**Paket K'nin `escalation_category`'sine göre kırılım**),
- `llm_calls` toplam maliyet-yakın metriği (token toplamı, zaten `/admin/costs`'ta olan sorgunun script versiyonu),
- toplam capture edilen tutar (Paket G),
- yeni waitlist kaydı sayısı (Paket I).

Çıktı: `reports/YYYY-MM-DD.md` dosyasına yazılır (repo'da tutulmaz —
`.gitignore`'a `reports/` eklenir, sadece deploy ortamında disk'te durur)
+ eğer `OPS_EMAIL` env ayarlıysa mevcut Gmail gönderim altyapısıyla
e-postalanır (ayarlı değilse sessizce sadece dosyaya yazar, hata vermez).

### Runbook

`docs/RUNBOOK.md`: deploy adımları (mevcut README'nin Setup bölümüne
referans + prod-specific farklar: migration'ı deploy pipeline'ında
otomatik çalıştırma, `alembic upgrade head` sırası), rollback (önceki
imaja dön + `alembic downgrade -1` gerekiyorsa), olay müdahalesi
kısa senaryoları: Stripe webhook imza hataları artıyor → ne kontrol
edilir; WhatsApp signature 401'leri artıyor → `WHATSAPP_APP_SECRET`
kontrolü; LLM API kesintisi → `SubagentEscalated` zaten insan kuyruğuna
düşürüyor, ek aksiyon yok, sadece `llm_calls` hata oranını izle.

### Testler

- `/health/deep`: DB up/down (mock), vault okunabilir/okunamaz senaryoları.
- Log'da secret sızmadığı testi (regex ile `REVIEW_TOKEN`/`STRIPE_SECRET_KEY` değerinin capture edilen log çıktısında aranması, bulunmaması).
- `daily_report.py`: sahte veriyle rapor içeriğinin doğru sayıları içerdiği.

### DoD

Kod + testler yeşil, `docs/RUNBOOK.md` var, README'de "Üretim" bölümü,
gerçek alerting/monitoring aracı (Sentry vb.) bağlanması İNSAN GEREKLİ
(spec'te istenmedi, kapsam dışı bırakıldı).

---

## Paket K — Ses kapısı (kod yok, ölçüm var)

**Amaç:** Ses kanalına (IVR/sesli arama) ne zaman yatırım yapılacağına dair
kararı veriye bağlamak — "hislere göre değil, eskalasyon oranına göre karar
ver" ilkesi.

### Vault

`vault/06-Kararlar/KR-003-ses-kanali-esigi.md` (`durum: taslak` ile başlar,
insan gözden geçirip `aktif`'e çeker — karar dosyası kararını Claude Code
vermiyor, sadece eşiği ölçülebilir hale getiriyor):

```yaml
---
karar_id: KR-003
durum: taslak
etki_alani: ["urun", "operasyon"]
gozden_gecirme: 2026-10-01
---
## Karar
Ses kanalına (sesli arama/IVR) yatırım yapılmaz, ta ki eskalasyon
nedenleri arasında "telefon talebi" oranı toplam eskalasyonların
%40'ını GEÇENE kadar.

## Ölçüm
`scripts/daily_report.py` / `docs/PROGRESS.md`'deki eskalasyon kırılımı
kaynak alınır (`Case.escalation_category = phone_request` sayısı /
toplam eskalasyon sayısı).

## Gerekçe
Ses kanalı büyük mühendislik + uyum (kayıt izni, KVKK/GDPR) yatırımı
ister; erken yapılırsa spekülatif. Telefon talebi oranı zaten "karşı
taraf bizi insan sanıp arayı istiyor" sinyalinin vekilidir.
```

### Kod (küçük, sadece ölçülebilirlik için)

`escalation_category` bugün yok — Kritik'in `violations` listesi serbest
metin (`"7: telefon istedi"` gibi). Checklist numaraları
`subagent-kontrati` skill'i gereği DEĞİŞTİRİLEMEZ/yeniden numaralandırılamaz
— bu yüzden madde 7 bölünmüyor, sadece 7 numaralı ihlallerin metni
`"telefon"` alt dizesi için ayrıştırılıyor:

```python
class EscalationCategoryEnum(str, enum.Enum):
    floor_violation = "floor_violation"          # madde 1
    info_leak = "info_leak"                        # madde 2
    fabrication = "fabrication"                      # madde 3
    unconditional_concession = "unconditional_concession"  # madde 4
    tactic_mismatch = "tactic_mismatch"                # madde 5
    premature_acceptance = "premature_acceptance"        # madde 6
    phone_request = "phone_request"                        # madde 7, "telefon" alt dizesi
    escalation_signal_other = "escalation_signal_other"      # madde 7, diğer (hukuki/agresyon/kimlik)
    decision_conflict = "decision_conflict"                    # madde 8
    other = "other"                                              # max revizyon/reject, parse hatası vb.
```

`Case.escalation_category: Mapped[EscalationCategoryEnum | None]` eklenir.
`app.orchestrator._escalate()` içine bir `_categorize(violations: list[str]
| None, reason: str) -> EscalationCategoryEnum` fonksiyonu eklenir, ilk
eşleşen madde numarasına göre (ve madde 7 için "telefon" alt dizesine göre)
kategori atar; hiçbiri eşleşmezse `other`.

**Bu, spec'in "kod yok" ifadesiyle çelişmiyor** — asıl karar (ses yatırımı
yapılsın mı) kod yazmıyor, sadece kararın dayanacağı sayıyı üretilebilir
kılıyor. `daily_report.py` (Paket J) bu kırılımı zaten rapor ediyor.

### Testler

- `_categorize`: her checklist maddesi için doğru kategori, "telefon"
  alt-dize eşleşmesi, eşleşmeyen durumda `other`.
- `daily_report.py`: kategoriye göre kırılımın raporda doğru göründüğü.

### DoD

`vault/06-Kararlar/KR-003-ses-kanali-esigi.md` (`durum: taslak`), 1 küçük
migration + birkaç test, README'de kısa not. Bu paket 1 günden kısa sürmeli
— karmaşıklaşıyorsa spec'ten sapılıyor demektir.

---

## Kapsam dışı (bilinçli, kullanıcı onaylı)

- **Hukuk görüşmesi konusu**: Kritik madde 7'nin "hukuki konu" alt sinyali
  bugünkü gibi ESCALATE'e düşmeye devam eder (K'nin `escalation_signal_
  other` kategorisine girer) — ayrı bir hukuk-özel akış kodlanmaz.
- **Şirket kimliği / isim kararı**: `vault/06-Kararlar/KR-004-sirket-
  kimligi.md` `durum: taslak` olarak vault'a girilir (bu spec'in bir
  parçası olarak Paket K ile birlikte eklenir, ayrı paket açılmaz). Kod
  tarafı: `Settings.identity_name: str = "X Danışmanlık"` (`.env.example`'a
  `IDENTITY_NAME`), `app.subagents.load_subagent_prompt` prompt metnindeki
  `{{IDENTITY_NAME}}` yer tutucusunu `settings.identity_name` ile değiştirir
  (`app/prompts/yazici.md`'deki sabit "X Danışmanlık" bu yer tutucuyla
  değiştirilir). İsmin NE olacağı kararı insanın işi — kod onu beklemeden
  çalışır, varsayılan değerle.
- **Talep doğrulama görüşmeleri** (gerçek 5 pilot müşteriyle konuşma,
  pazar araştırması): tamamen insan işi, kod/spec kapsamında değil.

## Kabul kriteri (hedef)

> Waitlist'ten (Paket I) capture'a (Paket G) kadar uçtan uca akış, elle DB
> müdahalesi sıfır.

Somutlaştırılmış test senaryosu (F-K'nin hepsi bittiğinde, tek bir
entegrasyon testinde uçtan uca doğrulanır — `tests/test_end_to_end_flow.py`):

1. `POST /waitlist` → kayıt (I).
2. `POST /web/register` + `POST /web/chat` ile intake tamamlanır, vaka
   açılır (v2, mevcut) → `Payment(pending)` otomatik oluşur (G).
3. Sahte Stripe webhook `checkout.session.completed` → `Payment
   (pre_authorized)` (G).
4. Karşı tarafa ilk mesaj: `counterparty_email` doluysa e-posta + opt-in
   linki akışı tetiklenir (H); sahte inbound WhatsApp mesajı ile opt-in
   koşulu sağlanır.
5. `run_turn` APPROVE üretir → `POST /review/{id}/approve` artık opt-in +
   ön-onay şartları sağlandığı için 200 döner, gönderilir (H+G guard'ları
   geçilir).
6. Analist `"close"` önerir (won) → `capture_for_won_case` otomatik
   tetiklenir, `Payment(captured)` (G).
7. `daily_report.py` çalıştırılır, vaka + tahsilat + eskalasyon kategorisi
   (varsa) doğru sayılarla raporda görünür (J+K).

Bu senaryoda hiçbir adımda elle `psql`/DB düzenlemesi yok — hepsi
endpoint/webhook/script çağrısıyla ilerliyor. Bu test yeşil olduğunda
kabul kriteri karşılanmış sayılır.
