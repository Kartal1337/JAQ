/**
 * leadSource.ts — pulls public business leads from Google Maps via Apify's
 * "Google Maps Scraper" actor. Pay-per-use, no infra to run.
 *
 * Swap this single module for SerpAPI or another provider without touching
 * the rest of the app — the Inngest function only depends on findLeads().
 *
 * Set APIFY_TOKEN. If unset, returns deterministic mock data so the whole
 * pipeline (and the onboarding "magic moment") runs end-to-end with zero
 * external setup while you develop.
 */

export interface ScrapedLead {
  businessName: string;
  contactName?: string;
  email?: string;
  phone?: string;
  website?: string;
  instagramHandle?: string;
  category?: string;
  city?: string;
  raw: unknown;
}

const APIFY_ACTOR = 'compass~crawler-google-places';

export async function findLeads(query: string, location: string | null, limit: number): Promise<ScrapedLead[]> {
  const token = process.env.APIFY_TOKEN;
  if (!token) {
    return mockLeads(query, location, limit);
  }

  const searchString = location ? `${query} in ${location}` : query;
  const res = await fetch(
    `https://api.apify.com/v2/acts/${APIFY_ACTOR}/run-sync-get-dataset-items?token=${token}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        searchStringsArray: [searchString],
        maxCrawledPlacesPerSearch: limit,
        language: 'en',
        scrapeContacts: true,
      }),
    },
  );

  if (!res.ok) {
    throw new Error(`Apify error ${res.status}: ${await res.text()}`);
  }

  const items = (await res.json()) as any[];
  return items.slice(0, limit).map((it) => ({
    businessName: it.title ?? it.name ?? 'Unknown business',
    email: firstEmail(it),
    phone: it.phone ?? it.phoneUnformatted,
    website: it.website,
    instagramHandle: extractInstagram(it),
    category: it.categoryName ?? it.category,
    city: it.city ?? location ?? undefined,
    raw: it,
  }));
}

function firstEmail(it: any): string | undefined {
  if (Array.isArray(it.emails) && it.emails.length) return it.emails[0];
  if (it.email) return it.email;
  return undefined;
}

function extractInstagram(it: any): string | undefined {
  const list: string[] = it.instagrams ?? it.socialMedia?.instagram ?? [];
  const url = Array.isArray(list) ? list[0] : list;
  if (!url) return undefined;
  const m = String(url).match(/instagram\.com\/([A-Za-z0-9._]+)/);
  return m ? m[1] : undefined;
}

// ---- dev/offline mock so the pipeline runs without any API keys ----
function mockLeads(query: string, location: string | null, limit: number): ScrapedLead[] {
  const city = location ?? 'Austin';
  const niche = query.replace(/\b(in|near|around)\b.*/i, '').trim() || 'business';
  const out: ScrapedLead[] = [];
  for (let i = 1; i <= limit; i++) {
    const name = `${city} ${capitalize(niche)} ${i}`;
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '');
    out.push({
      businessName: name,
      email: `hello@${slug}.com`,
      phone: `+1-512-555-01${String(i).padStart(2, '0')}`,
      website: `https://${slug}.com`,
      instagramHandle: slug,
      category: capitalize(niche),
      city,
      raw: { mock: true },
    });
  }
  return out;
}

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
