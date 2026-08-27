# AI SDR Assistant

Micro-SaaS that finds leads, writes a personalized cold email for each one with
Claude, drips them out, and surfaces the replies worth answering. Built to be
run and shipped by one developer.

> **Compliance note:** Email outreach is fully automated (compliant, deliverable).
> Instagram/LinkedIn are designed as *assisted* — the AI writes the message and
> you hit send — to avoid the account bans that come with automated social DMs.
> Don't ship auto-DM. It will get your customers banned.

## The "magic moment"

The whole product hinges on one flow: a user types *"dentists in Austin"* and
within ~30s sees 25 real businesses, each with a personalized email already
written. Three files make that work:

1. `supabase/migrations/0001_init.sql` — the data model + RLS.
2. `src/inngest/functions.ts` — `scrapeLeads` → `generateMessages` pipeline.
3. `src/prompts/outreach.ts` — the Claude prompt that writes emails that get replies.

## Stack

Next.js 14 (App Router) · Supabase (Postgres + Auth + RLS) · Inngest (background
jobs) · Claude (`claude-sonnet-4-6` to write, `claude-haiku-4-5` to tag replies)
· Resend (email) · Apify Google Maps (leads) · Cal.com (booking) · Stripe (billing).

## Run it locally (works with zero external keys)

```bash
cd ai-sdr-assistant
cp .env.example .env.local      # add Supabase URL + keys + ANTHROPIC_API_KEY
npm install

# 1) Create the schema in your Supabase project
#    Paste supabase/migrations/0001_init.sql into the Supabase SQL editor and run.

# 2) Start the app
npm run dev                     # http://localhost:3000

# 3) In a second terminal, start the Inngest dev server (runs background jobs)
npm run inngest                 # discovers functions at /api/inngest
```

Without `APIFY_TOKEN` the lead source returns realistic **mock leads**, and
without `RESEND_API_KEY` sends are **logged, not sent** — so the entire
pipeline (scrape → generate → queue → "send") runs end to end with only a
Supabase project and an Anthropic key.

## How the pieces connect

```
Onboarding UI  ──POST /api/campaigns──────────►  campaigns row
               ──POST /api/campaigns/:id/find-leads─► inngest: campaign/leads.find
                                                        │
                          scrapeLeads (Apify/mock) ─────┤ inserts leads
                          generateMessages (Claude) ────┘ writes 1 email/lead
               ◄──GET /api/campaigns/:id/leads── shows leads + drafts ("magic moment")
               ──POST /api/campaigns/:id/launch─► schedules a throttled drip
send-scheduled (cron 5m) ─► sends due emails (caps, window, suppression)
inbound reply ──/api/webhooks/email-inbound──► inngest: reply/received
                          tagInboundReply (Haiku) ─► tags + auto-suppress unsubs
Cal booking  ──/api/webhooks/cal──► appointments row, lead -> "booked"
Stripe       ──/api/webhooks/stripe──► profiles.plan
```

## API surface

| Method | Route | Purpose |
|---|---|---|
| POST/GET | `/api/campaigns` | create / list campaigns |
| POST | `/api/campaigns/:id/find-leads` | start scrape + generate pipeline |
| GET | `/api/campaigns/:id/leads` | lead table with drafts |
| POST | `/api/campaigns/:id/launch` | approve + schedule the drip |
| PATCH/DELETE | `/api/leads/:id` | edit draft / change status / delete |
| GET | `/api/inbox` | inbound replies with AI tags |
| POST | `/api/webhooks/email-inbound` | inbound reply → tag |
| POST | `/api/webhooks/cal` | booking → appointment |
| POST | `/api/webhooks/stripe` | subscription → plan |
| GET/POST/PUT | `/api/inngest` | background function host |

## Deploy

- App → **Vercel** (import the repo, set env vars, done).
- DB/Auth → **Supabase** (run the migration).
- Jobs → **Inngest Cloud** (connect your Vercel URL; set `INNGEST_SIGNING_KEY`).

## Pricing (wire to Stripe Prices via env)

Starter **$49/mo** · Growth **$129/mo** (hero) · Pro **$299/mo**. 7-day trial,
no card, capped at 25 leads/sends to match onboarding.

## What's intentionally NOT built (v2)

Auto IG/LinkedIn send, teams/roles, A/B testing, CRM pipeline stages, mobile app.
Ship the email loop first — it's the part that makes money.
