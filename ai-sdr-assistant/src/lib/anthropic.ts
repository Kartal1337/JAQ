import Anthropic from '@anthropic-ai/sdk';

export const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
});

// Generation needs strong instruction-following; tagging is cheap + high volume.
export const MODELS = {
  generate: 'claude-sonnet-4-6',
  classify: 'claude-haiku-4-5-20251001',
} as const;

/**
 * Calls Claude and parses a single JSON object out of the response.
 * Tolerates accidental ```json fences just in case.
 */
export async function completeJSON<T>(opts: {
  model: string;
  system: string;
  user: string;
  maxTokens?: number;
}): Promise<T> {
  const res = await anthropic.messages.create({
    model: opts.model,
    max_tokens: opts.maxTokens ?? 512,
    system: opts.system,
    messages: [{ role: 'user', content: opts.user }],
  });

  const text = res.content
    .filter((b): b is Anthropic.TextBlock => b.type === 'text')
    .map((b) => b.text)
    .join('')
    .trim();

  const cleaned = text.replace(/^```(?:json)?/i, '').replace(/```$/i, '').trim();
  const start = cleaned.indexOf('{');
  const end = cleaned.lastIndexOf('}');
  if (start === -1 || end === -1) {
    throw new Error(`No JSON object in model response: ${text.slice(0, 200)}`);
  }
  return JSON.parse(cleaned.slice(start, end + 1)) as T;
}
