import { NextResponse } from 'next/server';
import { getSupabaseServer } from '@/lib/supabase/server';
import { requireUser } from '@/lib/auth';

// GET /api/inbox — all inbound replies with AI tag + which lead they're from
export async function GET() {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const supabase = getSupabaseServer();
  const { data, error } = await supabase
    .from('messages')
    .select('id, body, ai_reply_tag, created_at, lead:lead_id(id, business_name, email, status)')
    .eq('direction', 'inbound')
    .order('created_at', { ascending: false })
    .limit(100);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ replies: data });
}
