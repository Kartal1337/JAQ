import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseAdmin } from '@/lib/supabase/admin';
import { inngest, EVENTS } from '@/lib/inngest/client';

/**
 * POST /api/webhooks/email-inbound
 * Receives inbound replies (Resend inbound, or a Gmail push relay). Matches
 * the reply to a lead by sender email, stores it, and fires reply/received
 * so Claude Haiku can tag it.
 *
 * Verify the provider signature in production (Resend signs with a secret).
 */
export async function POST(req: NextRequest) {
  // TODO: verify provider signature header before trusting the payload.
  const payload = await req.json().catch(() => null);
  if (!payload) return NextResponse.json({ error: 'bad payload' }, { status: 400 });

  // Normalize across providers
  const fromEmail: string | undefined = payload.from?.email ?? payload.from ?? payload.sender;
  const text: string = payload.text ?? payload.body ?? payload.stripped_text ?? '';
  if (!fromEmail) return NextResponse.json({ error: 'no sender' }, { status: 400 });

  const db = getSupabaseAdmin();

  // Find the most recent lead with this email (across the workspace)
  const { data: lead } = await db
    .from('leads')
    .select('id, user_id')
    .eq('email', fromEmail.toLowerCase())
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (!lead) {
    // Unknown sender — ack so the provider doesn't retry forever.
    return NextResponse.json({ status: 'ignored' });
  }

  const { data: message, error } = await db
    .from('messages')
    .insert({
      lead_id: lead.id,
      user_id: lead.user_id,
      channel: 'email',
      direction: 'inbound',
      body: text,
      ai_generated: false,
      status: 'delivered',
    })
    .select('id')
    .single();
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  await inngest.send({ name: EVENTS.replyReceived, data: { messageId: message.id } });

  return NextResponse.json({ status: 'received' });
}
