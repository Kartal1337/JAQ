import { createClient } from '@supabase/supabase-js';

/**
 * Service-role client — bypasses RLS. ONLY use server-side in trusted
 * contexts: Inngest background functions and verified webhooks, never in a
 * handler that returns data straight to a browser. Always filter by user_id
 * yourself here since RLS is off.
 */
export function getSupabaseAdmin() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false } },
  );
}
