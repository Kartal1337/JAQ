import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseAdmin } from '@/lib/supabase/admin';

/**
 * POST /api/webhooks/cal — Cal.com booking webhook.
 * On BOOKING_CREATED, matches the attendee email to a lead, records the
 * appointment, and flips the lead to "booked" (the metric that drives renewal).
 */
export async function POST(req: NextRequest) {
  const payload = await req.json().catch(() => null);
  if (!payload) return NextResponse.json({ error: 'bad payload' }, { status: 400 });

  if (payload.triggerEvent !== 'BOOKING_CREATED') {
    return NextResponse.json({ status: 'ignored' });
  }

  const p = payload.payload ?? {};
  const attendeeEmail: string | undefined = p.attendees?.[0]?.email;
  const startTime: string | undefined = p.startTime;
  const bookingId: string | undefined = String(p.uid ?? p.bookingId ?? '');
  if (!attendeeEmail) return NextResponse.json({ status: 'no attendee' });

  const db = getSupabaseAdmin();
  const { data: lead } = await db
    .from('leads')
    .select('id, user_id')
    .eq('email', attendeeEmail.toLowerCase())
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (!lead) return NextResponse.json({ status: 'no matching lead' });

  await db.from('appointments').insert({
    lead_id: lead.id,
    user_id: lead.user_id,
    scheduled_for: startTime ?? null,
    cal_booking_id: bookingId,
    status: 'booked',
  });
  await db.from('leads').update({ status: 'booked' }).eq('id', lead.id);

  return NextResponse.json({ status: 'booked' });
}
