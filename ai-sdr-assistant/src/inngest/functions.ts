/**
 * functions.ts — all background work. Registered at /api/inngest.
 *
 * Pipeline:
 *   campaign/leads.find   -> scrape Maps, insert leads, then fan out to generate
 *   campaign/messages.generate -> Claude writes a personalized email per lead
 *   send-scheduled (cron) -> sends due emails, respects caps/windows/suppression
 *   reply/received        -> Claude Haiku tags inbound, auto-suppresses unsubs
 *   schedule-followups (cron) -> queues step-2 for no-reply leads
 */
import { inngest, EVENTS } from '@/lib/inngest/client';
import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { completeJSON, MODELS } from '@/lib/anthropic';
import { findLeads } from '@/integrations/leadSource';
import { sendEmail } from '@/integrations/email';
import {
  OUTREACH_SYSTEM_PROMPT,
  buildOutreachUserPrompt,
  type LeadContext,
  type OfferContext,
} from '@/prompts/outreach';
import {
  REPLY_TAGGING_SYSTEM_PROMPT,
  buildReplyTaggingPrompt,
  type ReplyTag,
} from '@/prompts/replyTagging';

// --------------------------------------------------------------------------
// 1. Scrape leads, then trigger generation
// --------------------------------------------------------------------------
export const scrapeLeads = inngest.createFunction(
  { id: 'scrape-leads', concurrency: 5 },
  { event: EVENTS.leadsFind },
  async ({ event, step }) => {
    const { campaignId, userId, count } = event.data as {
      campaignId: string; userId: string; count: number;
    };
    const db = getSupabaseAdmin();

    const campaign = await step.run('load-campaign', async () => {
      const { data, error } = await db.from('campaigns').select('*').eq('id', campaignId).single();
      if (error) throw error;
      return data;
    });

    await step.run('mark-finding', async () => {
      await db.from('campaigns').update({ status: 'finding' }).eq('id', campaignId);
    });

    const scraped = await step.run('scrape', async () =>
      findLeads(campaign.target_query, campaign.location, count),
    );

    const inserted = await step.run('insert-leads', async () => {
      const rows = scraped
        .filter((l) => l.email) // need an email to send
        .map((l) => ({
          campaign_id: campaignId,
          user_id: userId,
          business_name: l.businessName,
          contact_name: l.contactName ?? null,
          email: l.email,
          phone: l.phone ?? null,
          website: l.website ?? null,
          instagram_handle: l.instagramHandle ?? null,
          source: 'google_maps',
          raw_data: l.raw,
          status: 'new',
        }));
      // upsert ignores duplicate (campaign_id, email)
      const { data, error } = await db
        .from('leads')
        .upsert(rows, { onConflict: 'campaign_id,email', ignoreDuplicates: true })
        .select('id');
      if (error) throw error;
      return data ?? [];
    });

    await step.run('bump-quota', async () => {
      await db.rpc('increment_leads_quota', { p_user: userId, p_n: inserted.length }).then(
        () => {},
        // RPC optional; ignore if not present
        () => {},
      );
    });

    if (inserted.length > 0) {
      await step.sendEvent('fan-out-generate', {
        name: EVENTS.messagesGenerate,
        data: { campaignId, userId },
      });
    } else {
      await step.run('mark-ready-empty', async () => {
        await db.from('campaigns').update({ status: 'ready' }).eq('id', campaignId);
      });
    }

    return { found: scraped.length, inserted: inserted.length };
  },
);

// --------------------------------------------------------------------------
// 2. Generate a personalized email per lead that has none yet
// --------------------------------------------------------------------------
export const generateMessages = inngest.createFunction(
  { id: 'generate-messages', concurrency: 3 },
  { event: EVENTS.messagesGenerate },
  async ({ event, step }) => {
    const { campaignId, userId } = event.data as { campaignId: string; userId: string };
    const db = getSupabaseAdmin();

    const { campaign, profile, leads } = await step.run('load', async () => {
      const [c, p, l] = await Promise.all([
        db.from('campaigns').select('*').eq('id', campaignId).single(),
        db.from('profiles').select('company_name, email').eq('id', userId).single(),
        db.from('leads').select('*').eq('campaign_id', campaignId).eq('status', 'new'),
      ]);
      if (c.error) throw c.error;
      return { campaign: c.data, profile: p.data, leads: l.data ?? [] };
    });

    let generated = 0;
    for (const lead of leads) {
      // Skip if a draft already exists for this lead
      const existing = await step.run(`check-${lead.id}`, async () => {
        const { count } = await db
          .from('messages')
          .select('id', { count: 'exact', head: true })
          .eq('lead_id', lead.id)
          .eq('direction', 'outbound');
        return count ?? 0;
      });
      if (existing > 0) continue;

      const draft = await step.run(`write-${lead.id}`, async () => {
        const leadCtx: LeadContext = {
          businessName: lead.business_name,
          contactName: lead.contact_name,
          website: lead.website,
          city: campaign.location,
          category: (lead.raw_data as any)?.category ?? null,
        };
        const offerCtx: OfferContext = {
          senderName: (profile?.company_name || profile?.email || 'me').split(' ')[0],
          senderCompany: profile?.company_name ?? 'our team',
          offer: campaign.offer ?? campaign.target_query,
          bookingUrl: process.env.DEFAULT_BOOKING_URL ?? null,
          step: 1,
        };
        return completeJSON<{ subject: string; body: string }>({
          model: MODELS.generate,
          system: OUTREACH_SYSTEM_PROMPT,
          user: buildOutreachUserPrompt(leadCtx, offerCtx),
        });
      });

      await step.run(`save-${lead.id}`, async () => {
        await db.from('messages').insert({
          lead_id: lead.id,
          user_id: userId,
          channel: 'email',
          direction: 'outbound',
          step: 1,
          subject: draft.subject,
          body: draft.body,
          ai_generated: true,
          status: 'queued',
          scheduled_at: null, // set when the campaign is launched
        });
      });
      generated++;
    }

    await step.run('mark-ready', async () => {
      await db.from('campaigns').update({ status: 'ready' }).eq('id', campaignId);
    });

    return { generated };
  },
);

// --------------------------------------------------------------------------
// 3. Cron: send emails that are due, respecting caps + send window + suppression
// --------------------------------------------------------------------------
export const sendScheduled = inngest.createFunction(
  { id: 'send-scheduled' },
  { cron: '*/5 * * * *' }, // every 5 minutes
  async ({ step }) => {
    const db = getSupabaseAdmin();
    const now = new Date().toISOString();

    const due = await step.run('load-due', async () => {
      const { data, error } = await db
        .from('messages')
        .select('id, user_id, subject, body, lead_id, leads(email, business_name)')
        .eq('direction', 'outbound')
        .eq('status', 'queued')
        .lte('scheduled_at', now)
        .not('scheduled_at', 'is', null)
        .limit(50);
      if (error) throw error;
      return data ?? [];
    });

    let sent = 0;
    for (const msg of due as any[]) {
      const lead = msg.leads;
      if (!lead?.email) continue;

      // Respect suppression list
      const suppressed = await step.run(`suppress-check-${msg.id}`, async () => {
        const { count } = await db
          .from('suppression_list')
          .select('id', { count: 'exact', head: true })
          .eq('user_id', msg.user_id)
          .eq('email', lead.email);
        return (count ?? 0) > 0;
      });
      if (suppressed) {
        await step.run(`skip-${msg.id}`, async () => {
          await db.from('messages').update({ status: 'failed' }).eq('id', msg.id);
        });
        continue;
      }

      const account = await step.run(`account-${msg.id}`, async () => {
        const { data } = await db
          .from('sending_accounts')
          .select('from_email')
          .eq('user_id', msg.user_id)
          .eq('is_verified', true)
          .limit(1)
          .maybeSingle();
        return data;
      });
      const from = account?.from_email ?? process.env.DEFAULT_FROM_EMAIL ?? 'onboarding@resend.dev';

      const result = await step.run(`send-${msg.id}`, async () =>
        sendEmail({
          from,
          to: lead.email,
          subject: msg.subject ?? 'Quick question',
          body: msg.body,
          headers: { 'List-Unsubscribe': `<mailto:${from}?subject=unsubscribe>` },
        }),
      );

      await step.run(`mark-sent-${msg.id}`, async () => {
        await db.from('messages')
          .update({ status: 'sent', sent_at: new Date().toISOString(), external_id: result.id })
          .eq('id', msg.id);
        await db.from('leads').update({ status: 'sent' }).eq('id', msg.lead_id).eq('status', 'sending');
      });
      sent++;
    }

    return { sent };
  },
);

// --------------------------------------------------------------------------
// 4. Tag an inbound reply (cheap Haiku), auto-suppress unsubscribes
// --------------------------------------------------------------------------
export const tagInboundReply = inngest.createFunction(
  { id: 'tag-inbound-reply', concurrency: 10 },
  { event: EVENTS.replyReceived },
  async ({ event, step }) => {
    const { messageId } = event.data as { messageId: string };
    const db = getSupabaseAdmin();

    const msg = await step.run('load', async () => {
      const { data, error } = await db
        .from('messages')
        .select('id, user_id, body, lead_id, leads(email)')
        .eq('id', messageId)
        .single();
      if (error) throw error;
      return data as any;
    });

    const tag = await step.run('classify', async () => {
      const { tag } = await completeJSON<{ tag: ReplyTag; reason: string }>({
        model: MODELS.classify,
        system: REPLY_TAGGING_SYSTEM_PROMPT,
        user: buildReplyTaggingPrompt(msg.body),
        maxTokens: 64,
      });
      return tag;
    });

    await step.run('apply', async () => {
      await db.from('messages').update({ ai_reply_tag: tag }).eq('id', messageId);
      const leadStatus = tag === 'unsubscribe' ? 'unsubscribed' : 'replied';
      await db.from('leads').update({ status: leadStatus }).eq('id', msg.lead_id);

      if (tag === 'unsubscribe' && msg.leads?.email) {
        await db.from('suppression_list')
          .upsert({ user_id: msg.user_id, email: msg.leads.email, reason: 'reply_unsubscribe' },
            { onConflict: 'user_id,email', ignoreDuplicates: true });
        // Cancel any queued follow-ups to this lead
        await db.from('messages')
          .update({ status: 'failed' })
          .eq('lead_id', msg.lead_id)
          .eq('direction', 'outbound')
          .eq('status', 'queued');
      }
    });

    return { tag };
  },
);

// --------------------------------------------------------------------------
// 5. Cron: queue step-2 follow-ups for leads that were sent but never replied
// --------------------------------------------------------------------------
export const scheduleFollowups = inngest.createFunction(
  { id: 'schedule-followups' },
  { cron: '0 14 * * *' }, // once a day
  async ({ step }) => {
    const db = getSupabaseAdmin();

    const candidates = await step.run('find-candidates', async () => {
      // Leads sent, status still 'sent' (no reply), no step-2 yet.
      const { data, error } = await db
        .from('leads')
        .select('id, user_id, business_name, contact_name, website, campaign_id, campaigns(follow_up_days, offer, target_query, location)')
        .eq('status', 'sent')
        .limit(200);
      if (error) throw error;
      return data ?? [];
    });

    let queued = 0;
    for (const lead of candidates as any[]) {
      const followDays = lead.campaigns?.follow_up_days ?? 3;

      const ready = await step.run(`gate-${lead.id}`, async () => {
        const { data } = await db
          .from('messages')
          .select('step, sent_at')
          .eq('lead_id', lead.id)
          .eq('direction', 'outbound')
          .order('step', { ascending: false });
        if (!data?.length) return false;
        if (data.some((m) => m.step === 2)) return false; // already followed up
        const firstSent = data.find((m) => m.step === 1)?.sent_at;
        if (!firstSent) return false;
        const ageDays = (Date.now() - new Date(firstSent).getTime()) / 86_400_000;
        return ageDays >= followDays;
      });
      if (!ready) continue;

      const draft = await step.run(`write-fu-${lead.id}`, async () => {
        const c = lead.campaigns;
        return completeJSON<{ subject: string; body: string }>({
          model: MODELS.generate,
          system: OUTREACH_SYSTEM_PROMPT,
          user: buildOutreachUserPrompt(
            { businessName: lead.business_name, contactName: lead.contact_name, website: lead.website, city: c?.location },
            { senderName: 'me', senderCompany: 'our team', offer: c?.offer ?? c?.target_query ?? '', bookingUrl: process.env.DEFAULT_BOOKING_URL ?? null, step: 2 },
          ),
        });
      });

      await step.run(`queue-fu-${lead.id}`, async () => {
        await db.from('messages').insert({
          lead_id: lead.id,
          user_id: lead.user_id,
          channel: 'email',
          direction: 'outbound',
          step: 2,
          subject: draft.subject,
          body: draft.body,
          status: 'queued',
          scheduled_at: new Date().toISOString(),
        });
        await db.from('leads').update({ status: 'sending' }).eq('id', lead.id);
      });
      queued++;
    }

    return { queued };
  },
);

export const functions = [
  scrapeLeads,
  generateMessages,
  sendScheduled,
  tagInboundReply,
  scheduleFollowups,
];
