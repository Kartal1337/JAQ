import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { getSupabaseAdmin } from '@/lib/supabase/admin';

/**
 * POST /api/webhooks/stripe — subscription lifecycle -> profiles.plan
 * Map your Stripe Price IDs to plans via STRIPE_PRICE_* env vars.
 */
const PLAN_BY_PRICE: Record<string, string> = {
  [process.env.STRIPE_PRICE_STARTER ?? '']: 'starter',
  [process.env.STRIPE_PRICE_GROWTH ?? '']: 'growth',
  [process.env.STRIPE_PRICE_PRO ?? '']: 'pro',
};

export async function POST(req: NextRequest) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY ?? '', { apiVersion: '2024-06-20' });

  const sig = req.headers.get('stripe-signature');
  const raw = await req.text();

  let event: Stripe.Event;
  try {
    event = secret && sig
      ? stripe.webhooks.constructEvent(raw, sig, secret)
      : (JSON.parse(raw) as Stripe.Event); // dev fallback only
  } catch (err) {
    return NextResponse.json({ error: `signature: ${(err as Error).message}` }, { status: 400 });
  }

  const db = getSupabaseAdmin();

  switch (event.type) {
    case 'customer.subscription.created':
    case 'customer.subscription.updated': {
      const sub = event.data.object as Stripe.Subscription;
      const priceId = sub.items.data[0]?.price.id ?? '';
      const plan = sub.status === 'active' || sub.status === 'trialing'
        ? (PLAN_BY_PRICE[priceId] ?? 'starter')
        : 'trial';
      await db.from('profiles').update({ plan }).eq('stripe_customer_id', String(sub.customer));
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as Stripe.Subscription;
      await db.from('profiles').update({ plan: 'trial' }).eq('stripe_customer_id', String(sub.customer));
      break;
    }
  }

  return NextResponse.json({ received: true });
}
