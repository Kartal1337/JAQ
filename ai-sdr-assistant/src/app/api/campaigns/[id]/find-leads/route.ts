import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { getSupabaseServer } from '@/lib/supabase/server';
import { requireUser } from '@/lib/auth';
import { inngest, EVENTS } from '@/lib/inngest/client';

const Body = z.object({ count: z.number().int().min(1).max(100).default(25) });

// POST /api/campaigns/:id/find-leads  -> kicks off the scrape+generate pipeline
export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const user = await requireUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const { count } = Body.parse(await req.json().catch(() => ({})));

  // Ownership check via RLS-backed read
  const supabase = getSupabaseServer();
  const { data: campaign, error } = await supabase
    .from('campaigns').select('id').eq('id', params.id).single();
  if (error || !campaign) return NextResponse.json({ error: 'not found' }, { status: 404 });

  await inngest.send({
    name: EVENTS.leadsFind,
    data: { campaignId: params.id, userId: user.id, count },
  });

  return NextResponse.json({ status: 'finding', count });
}
