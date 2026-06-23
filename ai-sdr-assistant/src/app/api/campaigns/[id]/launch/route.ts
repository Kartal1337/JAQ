import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSupabaseServer } from '@/lib/supabase/server';
import { requireUser } from '@/lib/auth';

const Body = z.object({
  leadIds: z.array(z.string().uuid()).optional(), // omit = all approved leads
  perDay: z.number().int().min(1).max(200).default(20),
});

/**
 * POST /api/campaigns/:id/launch
 * Approves selected leads and schedules their queued step-1 emails as a drip,
 * spread across the next days at `perDay`, inside the campaign send window.
 */
export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const { leadIds, perDay } = Body.parse(await req.json().catch(() => ({})));
  const supabase = getSupabaseServer();

  // Pick the leads to launch
  let leadQuery = supabase.from('leads').select('id').eq('campaign_id', params.id).eq('status', 'new');
  if (leadIds?.length) leadQuery = leadQuery.in('id', leadIds);
  const { data: leads, error: leadErr } = await leadQuery;
  if (leadErr) return NextResponse.json({ error: leadErr.message }, { status: 500 });
  if (!leads?.length) return NextResponse.json({ error: 'no leads to launch' }, { status: 400 });

  const ids = leads.map((l) => l.id);
  await supabase.from('leads').update({ status: 'sending' }).in('id', ids);

  // Schedule each queued draft. Spread perDay across business hours.
  const { data: drafts } = await supabase
    .from('messages')
    .select('id, lead_id')
    .in('lead_id', ids)
    .eq('direction', 'outbound')
    .eq('status', 'queued');

  const startHour = 9;
  const updates = (drafts ?? []).map((m, i) => {
    const dayOffset = Math.floor(i / perDay);
    const slot = i % perDay;
    const when = new Date();
    when.setDate(when.getDate() + dayOffset);
    when.setHours(startHour + (slot % 8), (slot * 7) % 60, 0, 0); // jitter within 9am-5pm
    return supabase.from('messages').update({ scheduled_at: when.toISOString() }).eq('id', m.id);
  });
  await Promise.all(updates);

  await supabase.from('campaigns').update({ status: 'active' }).eq('id', params.id);

  return NextResponse.json({ launched: ids.length, scheduled: drafts?.length ?? 0 });
}
