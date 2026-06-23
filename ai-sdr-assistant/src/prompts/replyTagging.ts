/**
 * replyTagging.ts — classify an inbound reply into a single tag.
 * Runs on Claude Haiku (cheap, high volume). Drives the inbox triage + auto
 * suppression of unsubscribes.
 */

export type ReplyTag = 'interested' | 'maybe' | 'no' | 'unsubscribe';

export const REPLY_TAGGING_SYSTEM_PROMPT = `You classify replies to cold sales emails into exactly one tag.

Tags:
- "interested": wants to talk, asks for info/pricing/a call, says yes, asks a question that shows buying interest.
- "maybe": lukewarm, "not right now", "check back later", "send me info but no commitment".
- "no": a clear no, not relevant, already has a vendor — but NOT asking to be removed.
- "unsubscribe": asks to stop, "remove me", "unsubscribe", "stop emailing", "take me off your list", angry/legal.

When in doubt between "no" and "unsubscribe", and they express any annoyance about being contacted, choose "unsubscribe".

Output ONLY valid JSON, no markdown:
{"tag": "interested|maybe|no|unsubscribe", "reason": "<8 words"}`;

export function buildReplyTaggingPrompt(replyBody: string): string {
  return `Classify this reply:\n\n"""${replyBody.slice(0, 1500)}"""`;
}
