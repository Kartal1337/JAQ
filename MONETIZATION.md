# JAQ-AI — Para Kazanma Stratejisi (Monetization Strategy)

> Amaç: Bu repoda **zaten var olan** iki varlıktan gerçek gelir üretmek.
> 1. **JAQ-AI / ForgeApp** — Telegram + dashboard üzerinden çalışan hiyerarşik multi-agent "sanal ofis" (SaaS potansiyeli).
> 2. **`affiliate_factory`** — Otomatik TikTok affiliate içerik hattı (doğrudan gelir motoru).
>
> Bu doküman strateji + uygulama planıdır. Hayalî rakam vaat etmez; her kanalın gerçek ekonomisini, ön koşullarını ve ilk adımlarını yazar.

---

## 0. Yönetici Özeti (TL;DR)

İki paralel yol var ve **ikisi de bugün başlatılabilir**:

| Yol | Ne | İlk gelir ne zaman | Sermaye | Risk |
|-----|----|--------------------|---------|------|
| **A. affiliate_factory** | TikTok affiliate içerik üretimini otomatikleştir, komisyon kazan | 2–6 hafta | Düşük (API maliyeti) | Orta (platform/komisyon bağımlı) |
| **B. JAQ-AI SaaS** | "Sanal ofis"i abonelikli ürüne çevir (ForgeApp) | 1–3 ay | Orta (multi-user altyapı) | Düşük-orta |

**Tavsiye:** Önce **A** ile nakit akışı yarat (hızlı, ucuz, mevcut kod %80 hazır), bu geliri **B**'nin multi-user altyapısını (Supabase + pgvector, billing) finanse etmek için kullan. A, B'nin hem motoru hem de en güçlü demo/pazarlama vakası olur.

---

## A. affiliate_factory ile Doğrudan Gelir

### A.1 Gelir modeli nasıl çalışır?
TikTok Shop / affiliate programlarında bir ürünü tanıtan kısa video, izleyici linkten alışveriş yapınca **komisyon** kazandırır (tipik %5–%20). Bu hattın değer önerisi: **insan eli değmeden günde N adet test-edilebilir video konsepti üretmek** ve kazananları ölçekleyip kaybedenleri elemek.

Birim ekonomisi (örnek, muhafazakâr):
- 1 video ortalama 2.000–20.000 görüntülenme (çoğu düşük, az sayıda viral).
- 100 video/ay → birkaç tanesi tutar → asıl gelir "kazanan" videolardan gelir.
- Strateji portföy mantığıdır: **ucuz çok deneme + acımasız eleme** (zaten `optimizer.py` ve `weekly_review.py` bunun için var).

### A.2 Mevcut varlık (kod zaten yazılmış)
`affiliate_factory/agents/` altında hat tam: `trend_miner → offer_research → competitor_scout → brief_builder → script_forge → visual_prompt → caption_agent → optimizer → performance_logger`. Günlük (`daily_pipeline.py`) ve haftalık (`weekly_review.py`) graph'lar mevcut. Çıktı: TikTok'a yüklenmeye hazır script + görsel prompt + caption paketleri.

### A.3 Eksik olan (kapatılması gereken boşluk)
Kod **içerik üretiyor** ama gelir **dağıtım + yükleme + dönüşüm** ile gelir. Eksikler:
1. **Niş seçimi** — Hangi kategori? (güzellik, ev gereçleri, gadget, fitness). Komisyon oranı yüksek + görsel demo'ya uygun nişler seç.
2. **TikTok Shop affiliate hesabı** — başvuru + onay (ülke uygunluğu kontrol et).
3. **Yükleme adımı** — README'de `"video_id": "..."` placeholder; gerçek yükleme şu an manuel. İlk fazda **manuel yükle**, otomasyonu sonra ekle.
4. **Higgsfield/görsel üretim** ve **TikTok posting API** key'leri (`.env`: `AFFILIATE_HIGGSFIELD_API_KEY`, `AFFILIATE_TIKTOK_ACCOUNT_HANDLE`).

### A.4 30 günlük uygulama planı
- **Gün 1–3:** Niş seç (1 tane, dağıtma). TikTok Shop affiliate başvurusu. API key'leri `.env`'e gir, `daily_pipeline`'ı dry-run et.
- **Gün 4–10:** Günde 3–5 video manuel üret + yükle. Tek değişken: hook formülü (`prompts/script_templates/hook_formulas.py`). `performance_logger` ile gerçek metrikleri SQLite'a yaz.
- **Gün 11–20:** `weekly_review` ile kazanan hook/format desenlerini çıkar. Kaybeden formatları kes, kazananları 2–3 katına çıkar.
- **Gün 21–30:** İlk komisyonları ölç. CAC yerine "video başına maliyet" (API $) vs "video başına komisyon" tablosunu çıkar. Pozitifse → ölçekle (gün başına video sayısını artır, posting'i otomatikleştir).

### A.5 Başarı metriği
- **Kuzey yıldızı:** Aylık net affiliate komisyonu − API maliyeti.
- Ara metrik: kazanan video oranı (>%5 hedef), kazanan başına ortalama komisyon.
- Eleme kuralı: 2 hafta üst üste negatif birim ekonomisi → nişi değiştir, hattı değil.

---

## B. JAQ-AI'yi SaaS'a Çevirmek (ForgeApp)

### B.1 Değer önerisi
"Tek bir arayüzden CEO yönlendirmesiyle araştırma → pazar analizi → kod → içerik → finans → hukuk yapan sanal ofis." Hedef müşteri: **solo kurucular, indie hacker'lar, küçük ajanslar** — tam ekip tutamayan ama çok fonksiyonlu yardım isteyenler.

### B.2 Fiyatlandırma (önerilen)
Kullanım maliyetin (Anthropic + Tavily API) müşteriye yansıması net olmalı.

| Plan | Fiyat/ay | Kapsam | Hedef |
|------|----------|--------|-------|
| **Free** | $0 | Günde N istek, tek agent, geçmiş yok | Funnel girişi |
| **Pro** | $19–29 | Tüm agent'lar, kalıcı hafıza, dashboard | Solo kurucu |
| **Team** | $79–99 | Multi-user, paylaşılan hafıza, öncelik | Küçük ekip |
| **Usage add-on** | maliyet+marj | API kullanım üstü | Ağır kullanıcı |

> Kritik kural: LLM maliyeti değişken. **Token-bazlı limit + add-on** olmadan flat fiyat seni zarara sokar. Plan başına aylık token tavanı koy.

### B.3 SaaS için teknik ön koşullar (CLAUDE.md'deki "Gelecek plan" ile uyumlu)
1. **Multi-user altyapı:** SQLite + ChromaDB → **Supabase + pgvector** (CLAUDE.md'de zaten planlı). Per-user izolasyon şart.
2. **Auth & billing:** Şu an tek kullanıcı (`telegram_chat_id` gate). Stripe/LemonSqueezy + kullanıcı yönetimi gerekir.
3. **Kullanım ölçümü:** Plan limitleri için token sayacı + rate limit (zaten `core/rate_limiter.py` var, plan-bazlı yapılmalı).
4. **Çok kiracılı (multi-tenant) güvenlik:** Prompt injection koruması var (`core/input_validator.py`); kiracı veri sızıntısı testleri eklenmeli.

### B.4 90 günlük uygulama planı
- **Ay 1:** Supabase + pgvector migrasyonu, basit auth, Stripe entegrasyonu, plan limitleri. Dashboard'u landing + login + billing ile ürünleştir.
- **Ay 2:** 10–20 ücretsiz beta kullanıcı (indie hacker toplulukları, Türkiye startup grupları). Hangi agent gerçekten kullanılıyor? Ona odaklan, gerisini sadeleştir.
- **Ay 3:** Ücretli plana geçiş. İlk 5–10 ödeyen müşteri hedefi. Retention ölç (haftalık aktif / kayıt).

### B.5 Hızlı pazar testi (kod yazmadan)
Tam SaaS'a yatırım yapmadan **talebi doğrula**: tek bir agent'ı (örn. MarketAnalysisAgent veya WriterAgent) "managed servis" olarak Telegram üzerinden elle sat. 5 kişi ödemeye razıysa SaaS'a yatırım mantıklı; değilse fiyat/niş yanlış.

---

## C. Diğer Gelir Kanalları (ikincil, opsiyonel)

1. **"Done-for-you" içerik ajansı:** affiliate_factory'i kendi ürünün için değil, **müşteri markaları için** çalıştır (aylık retainer). Hızlı nakit, ama emek yoğun.
2. **Skill marketplace:** `skills/` dinamik beceri modülleri (örn. `content-repurposing`). Premium skill'leri SaaS add-on olarak sat.
3. **API/affiliate as a service:** Affiliate hattını başka içerik üreticilerine API olarak aç.
4. **Eğitim/şablon satışı:** Kazanan hook formülleri + script şablonları paketi (en düşük efor, en düşük gelir).

---

## D. Önerilen Sıra ve Karar Çerçevesi

```
Hafta 0       → A.4 başlat (affiliate, ucuz nakit akışı)
Hafta 0–2     → B.5 yap (SaaS talebini elle doğrula, kod yazmadan)
Hafta 2–4     → A pozitif birim ekonomisi gösterirse ölçekle
Ay 1–3        → B.4 (SaaS altyapısı) — A'nın gelirini buraya yatır
```

**Devam/dur kuralları:**
- A negatif kalıyorsa → niş değiştir (hattı değil), 2 deneme sonra A'yı duraklat.
- B.5'te 5 ödeyen yoksa → SaaS'a kod yatırma, A'ya yüklen.
- İkisi de tutarsa → A motor, B ürün; A'nın çıktısı B'nin pazarlama vakası olur.

---

## E. Şeffaf Riskler ve Uyarılar

- **Platform riski:** TikTok affiliate kuralları/komisyonları ülkeye göre değişir ve değişebilir. Tek platforma bağımlı kalma — Instagram Reels / YouTube Shorts'a aynı içeriği repurpose et (`skills/content-repurposing` zaten bunun için).
- **API maliyeti:** Hem A hem B değişken LLM/görsel maliyeti taşır. Her özelliği "token başına maliyet" ile ölç; sınırsız flat plan koyma.
- **Yasal/şeffaflık:** Affiliate içerikte sponsorluk açıklaması (disclosure) zorunludur. Otomasyon spam'e dönüşmemeli; platform ban riski gerçektir.
- **Garanti yok:** Bu bir strateji ve altyapıdır, otomatik para basan makine değil. Gelir, niş seçimi + dağıtım + iterasyon disiplinine bağlıdır.

---

## F. Bu Hafta İçin Net İlk Adımlar (Aksiyon Listesi)

- [ ] **A:** TikTok Shop affiliate başvurusu yap, uygunluğu doğrula.
- [ ] **A:** Tek niş seç (komisyon yüksek + görsel demoya uygun).
- [ ] **A:** `.env`'e affiliate key'lerini gir, `daily_pipeline`'ı dry-run et (`python affiliate_factory/data/chromadb_init.py --db`).
- [ ] **A:** 3 video üret + manuel yükle, `performance_logger` ile metrikleri kaydet.
- [ ] **B:** 1 agent'ı seç, 5 potansiyel müşteriye elle "managed" olarak sun (talep testi).
- [ ] **Karar:** 2 hafta sonra A birim ekonomisi + B talep sinyaline göre kaynağı tek yöne yığ.
