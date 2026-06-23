import { NextRequest, NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase/server';
import { requireUser } from '@/lib/auth';

// GET /api/campaigns/:id/leads — lead table with each lead's draft message
export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const supabase = getSupabaseServer();
  const { data, error } = await supabase
    .from('leads')
    .select('*, messages(id, subject, body, step, status, direction, ai_reply_tag)')
    .eq('campaign_id', params.id)
    .order('created_at', { ascending: true });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ leads: data });
}
