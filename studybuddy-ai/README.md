# StudyBuddy AI 📚🔥 — Ders Arkadaşım AI

Türkiyeli lise ve üniversite öğrencileri (özellikle YKS) için **Pomodoro + AI Koç**
birleşimi, motive edici bir çalışma uygulaması. Tamamen Türkçe, dark mode, animasyonlu.

> Expo SDK 52 · React Native 0.76 · Expo Router · Reanimated 3 · TypeScript · Zustand

---

## 🚀 Hızlı Başlangıç

```bash
cd studybuddy-ai

# Bağımlılıkları kur
npm install

# Geliştirme sunucusunu başlat
npx expo start
```

Sonra:
- **Telefonda:** App Store / Play Store'dan **Expo Go** uygulamasını indir, terminaldeki
  QR kodu okut.
- **Emülatörde:** `i` (iOS) veya `a` (Android) tuşuna bas.

İlk açılışta onboarding (ad, sınıf, dersler) gelir. AI sohbeti için
**Profil → AI API Anahtarı** bölümünden kendi anahtarını gir (OpenAI / Grok / Claude).

---

## 📁 Proje Yapısı

```
studybuddy-ai/
├── app/                          # Expo Router (file-based routing)
│   ├── _layout.tsx               # Root: provider'lar, gesture handler, bildirim ayarı
│   ├── index.tsx                 # Açılış yönlendirici (onboarding mı tabs mı?)
│   ├── onboarding.tsx            # 3 adımlı ilk kurulum
│   └── (tabs)/
│       ├── _layout.tsx           # Bottom tab navigation
│       ├── index.tsx             # 🏠 Ana Sayfa / Dashboard
│       ├── timer.tsx             # ⏱️ Pomodoro
│       ├── chat.tsx              # 🤖 AI Koç
│       ├── history.tsx           # 📊 İlerleme
│       └── profile.tsx           # 👤 Profil & Ayarlar
├── src/
│   ├── components/               # Yeniden kullanılabilir UI (Button, Card, Txt, ProgressRing, BarChart...)
│   ├── hooks/usePomodoro.ts      # Zaman damgası tabanlı timer motoru (arka plan güvenli)
│   ├── lib/                      # ai.ts, notifications.ts, stats.ts, achievements.ts, date.ts
│   ├── store/useStore.ts         # Zustand + AsyncStorage kalıcı durum
│   ├── theme/theme.ts            # Tasarım token'ları (renk, boşluk, radius)
│   ├── locale/tr.ts              # TÜM Türkçe metinler tek dosyada
│   └── constants/quotes.ts       # Motivasyon sözleri
├── app.json · babel.config.js · tsconfig.json · package.json
```

### Mimari kararlar
- **Stil:** Ekstra native config gerektirmeyen, performanslı **tasarım-token + StyleSheet**
  sistemi (Expo Go'da %100 çalışır). İstersen NativeWind/Tamagui'ye geçmek kolaydır.
- **Durum:** `zustand` + `persist` (AsyncStorage). Gereksiz re-render olmaması için
  selector'lar (`useStore(s => s.x)`) kullanılır.
- **Timer:** Bitiş zaman damgasına göre çalışır; uygulama arka plana alınıp dönünce
  süre yeniden hesaplanır ve yerel bildirim planlanır.
- **AI:** Sağlayıcı-bağımsız `complete()`. Anahtar yalnızca cihazda saklanır.

---

## 🤖 AI Entegrasyonu

`src/lib/ai.ts` tek dosyada OpenAI, Grok (xAI) ve Claude'u destekler. Kullanıcı kendi
API anahtarını girer; istek doğrudan sağlayıcıya gider (backend yok). Yanıt tek seferde
alınır ama UX için **kelime kelime "akıtılır"** (daktilo efekti).

> İleride: anahtarı backend'e taşıyıp gerçek SSE streaming ve soru-fotoğrafı (vision)
> eklenebilir.

---

## ✅ Test Rehberi (ekran ekran)

| Ekran | Nasıl test edilir |
|-------|-------------------|
| **Onboarding** | Uygulamayı ilk kez aç (veya Profil → Verileri Sıfırla). Ad gir, sınıf ve ders seç. |
| **Ana Sayfa** | Streak, bugünkü odak ve pomodoro sayısının göründüğünü kontrol et. "Hızlı Pomodoro Başlat" timer'a götürmeli. AI önerisi için anahtar girilmiş olmalı. |
| **Pomodoro** | 25/5 ↔ 50/10 değiştir, **Başla** → halkanın dolduğunu izle. **Duraklat/Devam**, **Bitir** (≥1 dk sonra seans kaydedilir). Uygulamayı arka plana al, geri gel → süre doğru olmalı. Bittiğinde bildirim + kutlama. |
| **AI Koç** | Profil'den anahtar gir. Bir soru yaz → cevabın akarak geldiğini gör. Hızlı aksiyonları (Özetle/Quiz/Çöz) dene. |
| **İlerleme** | Birkaç pomodoro tamamla, haftalık grafiğin ve "en çok çalışılan konular"ın dolduğunu gör. |
| **Profil** | Ad/anahtar kaydet, sağlayıcı değiştir, bildirim/ses aç-kapa, başarımların açıldığını kontrol et. |

---

## ⚠️ Notlar
- **Bildirimler:** Expo Go'da yerel (local) bildirimler çalışır; tam push desteği için
  development build önerilir. İlk seansta izin istenir.
- **Web:** `npx expo start --web` ile çalışır ama uygulama mobil için tasarlanmıştır.
- Anahtarlar cihazda `AsyncStorage`'da tutulur — paylaşılan cihazlarda dikkat.
