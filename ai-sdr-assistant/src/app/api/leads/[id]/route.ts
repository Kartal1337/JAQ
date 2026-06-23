import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSupabaseServer } from '@/lib/supabase/server';
import { requireUser } from '@/lib/auth';

const Patch = z.object({
  status: z.enum(['new', 'approved', 'sending', 'sent', 'replied', 'booked', 'bounced', 'unsubscribed']).optional(),
  // edit the step-1 draft inline
  subject: z.string().max(200).optional(),
  body: z.string().max(4000).optional(),
});

// PATCH /api/leads/:id — change lead status and/or edit its draft message
export async function PATCH(req: NextRequest, { params }: { params: { id: string } }) {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const body = Patch.parse(await req.json());
  const supabase = getSupabaseServer();

  if (body.status) {
    const { error } = await supabase.from('leads').update({ status: body.status }).eq('id', params.id);
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if (body.subject || body.body) {
    const patch: Record<string, unknown> = { ai_generated: false };
    if (body.subject) patch.subject = body.subject;
    if (body.body) patch.body = body.body;
    const { error } = await supabase
      .from('messages')
      .update(patch)
      .eq('lead_id', params.id)
      .eq('direction', 'outbound')
      .eq('step', 1);
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const supabase = getSupabaseServer();
  const { error } = await supabase.from('leads').delete().eq('id', params.id);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
