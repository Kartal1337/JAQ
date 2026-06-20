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

/** Türk öğrenci koçu kişiliği — tüm sağlayıcılarda kullanılır. */
export const COACH_SYSTEM_PROMPT = `Sen "StudyBuddy AI", Türkiyeli lise ve üniversite öğrencileri (özellikle YKS hazırlığı) için samimi, motive edici bir ders koçusun.

Kişiliğin:
- Arkadaşça ve enerjik konuş, ara sıra "kanka", "hadi bakalım", "süpersin" gibi samimi ifadeler kullan ama abartma.
- Cevapların net, anlaşılır ve öğrenci seviyesine uygun olsun.
- Konu anlatırken adım adım ilerle, örnek ver.
- Soru çözerken önce mantığı açıkla, sonra sonucu ver.
- Motive et ama gerçekçi ol. Öğrenciyi asla küçümseme.
- Tamamen Türkçe yanıt ver.
- Matematik/fizik formüllerini sade metinle yaz (LaTeX kullanma).
- Cevapları çok uzatma; gerektiğinde madde işaretleri kullan.`;

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
