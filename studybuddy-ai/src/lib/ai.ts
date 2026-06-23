/**
 * Basit, sağlayıcı-bağımsız AI istemcisi.
 * Kullanıcı kendi API anahtarını girer (OpenAI / Grok / Claude).
 * Anahtar yalnızca cihazda saklanır; doğrudan sağlayıcıya istek atılır.
 *
 * Not: React Native fetch gövde streaming'i (ReadableStream reader) güvenilir
 * desteklemediği için varsayılan olarak tek seferlik (non-stream) yanıt alır.
 * `onToken` verilirse yanıt kelime kelime simüle edilerek akıtılır (UX için).
 */

import type { AIProvider } from '@/store/useStore';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface CompleteOpts {
  provider: AIProvider;
  apiKey: string;
  messages: ChatMessage[];
  signal?: AbortSignal;
  onToken?: (chunk: string) => void;
}

const ENDPOINTS: Record<AIProvider, string> = {
  openai: 'https://api.openai.com/v1/chat/completions',
  grok: 'https://api.x.ai/v1/chat/completions',
  claude: 'https://api.anthropic.com/v1/messages',
};

const MODELS: Record<AIProvider, string> = {
  openai: 'gpt-4o-mini',
  grok: 'grok-2-latest',
  claude: 'claude-sonnet-4-6',
};

/** YKS odaklı, skill-tabanlı AI koç kişiliği — tüm sağlayıcılarda kullanılır. */
export const COACH_SYSTEM_PROMPT = `Sen "StudyBuddy", Türkiye'deki YKS (TYT + AYT) öğrencileri için gelişmiş bir öğrenme sistemisin. Tek amacın: öğrencinin NET'ini artırmak. Kıdemli bir YKS mentoru + özel öğretmen (Matematik, Fizik, Kimya, Türkçe, Biyoloji) + sınav stratejisti + performans analisti karışımı gibi davran.

TEMEL HEDEF: TYT ve AYT netini maksimize et — zayıf konuları hızlı teşhis et, sınava yönelik derinlikte öğret, hedefli sorularla pekiştir, ilerlemeyi takip et, boşa giden çalışma süresini azalt.

SKILL SİSTEMİ (ZORUNLU):
Her isteği önce bir Skill'e sınıflandır:
- diagnostic_skill → seviye tespiti, zayıf nokta bulma
- concept_teaching_skill → sıfırdan konu anlatımı
- exam_question_skill → soru çözme / açıklama
- error_analysis_skill → hata analizi
- study_plan_skill → günlük/haftalık program
- revision_skill → aralıklı tekrar (spaced repetition) özetleri
- motivation_skill → zihinsel performans + disiplin
Uygun skill yoksa yenisini oluştur.

ÇIKTI FORMATI (her akademik yanıt bu yapıda olmalı):
SKILL: (seçilen skill)
HEDEF: (bu adımın amacı, tek cümle)
GİRDİ KONTROLÜ: (eksik bilgi veya yaptığın varsayımlar)
ÇÖZÜM/ANLATIM: (net açıklama; gerektiğinde adım adım; sınav odaklı kısa yollar ve kalıplar)
SINAV TAKTİĞİ: (YKS'ye özel kalıp, tuzak veya kısa yol — en az 1 tane)
SONRAKİ ADIM: (öğrencinin şimdi ne yapması gerektiği)

(Sadece selam/teşekkür gibi akademik olmayan kısa mesajlarda bu formatı atla, tek satır yanıt ver.)

TEŞHİS MODU: Öğrenci "çalışamıyorum", "konuları bilmiyorum", "nereden başlayayım" gibi şeyler derse FULL DIAGNOSTIC SKILL'i aç: 3-7 hedefli soru sor, mevcut net seviyesini tahmin et, öğrenciyi sınıflandır (Başlangıç 0-20 net / Orta 20-60 net / İleri 60+ net), sonra yol haritası çıkar.

ÖĞRETME KURALLARI:
- Teori derinliğinden çok YKS sınav ilgisini önceliklendir; "soru çözdürme mantığı" odaklı ol.
- En sık çıkan soru tipleri ve zayıf konu eliminasyonu önce gelir.
- Minimum efor → maksimum net kazancı. Günlük ölçülebilir çıktı hedefle.
- Kaçın: uzun akademik anlatım, gereksiz teori, sınavla ilgisiz içerik, boş motivasyon lafı, muğlak tavsiye.
- Üslup: yapılandırılmış, doğrudan, taktiksel, sade. Tamamen Türkçe yanıt ver.
- Matematik/fizik formüllerini sade metinle yaz (LaTeX kullanma).

HAFIZA DAVRANIŞI: Konuşma boyunca zayıf dersleri ve tekrar eden hataları takip et, zorluğu dinamik ayarla, uygun olduğunda tekrar döngüsü öner.`;


async function callOpenAICompatible(
  url: string,
  model: string,
  apiKey: string,
  messages: ChatMessage[],
  signal?: AbortSignal
): Promise<string> {
  const res = await fetch(url, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: 0.7,
      max_tokens: 1024,
    }),
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`AI hatası (${res.status}): ${errText.slice(0, 200)}`);
  }
  const data = await res.json();
  return data?.choices?.[0]?.message?.content?.trim() ?? '';
}

async function callClaude(
  apiKey: string,
  messages: ChatMessage[],
  signal?: AbortSignal
): Promise<string> {
  const system = messages.find((m) => m.role === 'system')?.content;
  const turns = messages
    .filter((m) => m.role !== 'system')
    .map((m) => ({ role: m.role, content: m.content }));

  const res = await fetch(ENDPOINTS.claude, {
    method: 'POST',
    signal,
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODELS.claude,
      system,
      messages: turns,
      max_tokens: 1024,
    }),
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    throw new Error(`AI hatası (${res.status}): ${errText.slice(0, 200)}`);
  }
  const data = await res.json();
  return data?.content?.[0]?.text?.trim() ?? '';
}

/** Yanıtı kelime kelime "akıtarak" UX'i canlandırır. */
async function simulateStream(text: string, onToken: (c: string) => void) {
  const words = text.split(/(\s+)/);
  for (const w of words) {
    onToken(w);
    // küçük gecikme — daktilo etkisi
    await new Promise((r) => setTimeout(r, 14));
  }
}

export async function complete({
  provider,
  apiKey,
  messages,
  signal,
  onToken,
}: CompleteOpts): Promise<string> {
  if (!apiKey) throw new Error('NO_API_KEY');

  let full: string;
  if (provider === 'claude') {
    full = await callClaude(apiKey, messages, signal);
  } else {
    full = await callOpenAICompatible(
      ENDPOINTS[provider],
      MODELS[provider],
      apiKey,
      messages,
      signal
    );
  }

  if (onToken && full) await simulateStream(full, onToken);
  return full;
}

/** "Bugün ne çalışayım?" için tek seferlik öneri üretir. */
export async function suggestStudyPlan(opts: {
  provider: AIProvider;
  apiKey: string;
  level: string;
  interests: string[];
}): Promise<string> {
  const interestsText = opts.interests.length
    ? opts.interests.join(', ')
    : 'genel dersler';
  return complete({
    provider: opts.provider,
    apiKey: opts.apiKey,
    messages: [
      { role: 'system', content: COACH_SYSTEM_PROMPT },
      {
        role: 'user',
        content: `Ben ${opts.level} seviyesindeyim ve şu derslere odaklanıyorum: ${interestsText}. Bugün için bana kısa, uygulanabilir bir çalışma planı öner. En fazla 4 madde, her madde için tahmini pomodoro sayısı yaz. Kısa ve motive edici ol.`,
      },
    ],
  });
}
