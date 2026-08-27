/**
 * outreach.ts — the core product magic.
 *
 * Turns a scraped lead + the user's offer into a short, personalized cold
 * email that actually gets replies. The constraints here ARE the product:
 * short, specific, human, one ask. Loosen them and reply rates collapse.
 */

export interface LeadContext {
  businessName: string;
  contactName?: string | null;
  website?: string | null;
  city?: string | null;
  category?: string | null;       // e.g. "Dentist", "Med spa"
  websiteSnippet?: string | null; // a few lines scraped from their site, if available
}

export interface OfferContext {
  senderName: string;
  senderCompany: string;
  offer: string;                  // what the user sells / the value prop
  bookingUrl?: string | null;     // Cal.com link, inserted as the CTA
  step: 1 | 2;                    // 1 = first touch, 2 = follow-up
}

export const OUTREACH_SYSTEM_PROMPT = `You are an expert B2B SDR who writes cold emails that get replies from small business owners.

Hard rules — breaking any of these makes the email worse:
- Under 80 words total. Shorter is better.
- First line must reference something SPECIFIC and TRUE about the recipient's business (their city, niche, or a detail from their website). Never generic.
- Plain, human language. A busy owner reads it on their phone in 5 seconds.
- Exactly ONE ask (the CTA). Soft, low-friction. No "let me know if you'd be interested in possibly exploring".
- BANNED openers: "I hope this email finds you well", "My name is", "I wanted to reach out", "I came across your".
- No buzzwords (synergy, leverage, solutions, cutting-edge, revolutionary, game-changer).
- No fake flattery. No exclamation marks. No emojis.
- Write like one real person emailing another, not a marketing department.

Output ONLY valid JSON, no markdown fences:
{"subject": "...", "body": "..."}

Subject: 2-5 words, lowercase-ish, looks like a real person sent it (not a campaign).
Body: the email. Sign off with just the sender's first name.`;

export function buildOutreachUserPrompt(lead: LeadContext, offer: OfferContext): string {
  const ctaLine = offer.bookingUrl
    ? `For the CTA, ask if they're open to a quick chat and include this booking link: ${offer.bookingUrl}`
    : `For the CTA, ask a simple yes/no question that's easy to reply to (no link).`;

  if (offer.step === 2) {
    return [
      `Write a SHORT follow-up email (the recipient did not reply to the first one).`,
      `Do not guilt-trip or say "just following up". Add one new small reason to reply or a different angle.`,
      ``,
      `Recipient business: ${lead.businessName}`,
      lead.contactName ? `Contact name: ${lead.contactName}` : ``,
      lead.category ? `Category: ${lead.category}` : ``,
      lead.city ? `City: ${lead.city}` : ``,
      lead.website ? `Website: ${lead.website}` : ``,
      lead.websiteSnippet ? `From their website: """${lead.websiteSnippet.slice(0, 600)}"""` : ``,
      ``,
      `Sender: ${offer.senderName} from ${offer.senderCompany}`,
      `What the sender offers: ${offer.offer}`,
      ctaLine,
    ].filter(Boolean).join('\n');
  }

  return [
    `Write the FIRST cold email.`,
    ``,
    `Recipient business: ${lead.businessName}`,
    lead.contactName ? `Contact name: ${lead.contactName}` : ``,
    lead.category ? `Category: ${lead.category}` : ``,
    lead.city ? `City: ${lead.city}` : ``,
    lead.website ? `Website: ${lead.website}` : ``,
    lead.websiteSnippet ? `From their website: """${lead.websiteSnippet.slice(0, 600)}"""` : ``,
    ``,
    `Sender: ${offer.senderName} from ${offer.senderCompany}`,
    `What the sender offers: ${offer.offer}`,
    ctaLine,
  ].filter(Boolean).join('\n');
}
