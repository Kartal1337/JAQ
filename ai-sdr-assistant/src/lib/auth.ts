import { getSupabaseServer } from '@/lib/supabase/server';

/** Returns the authenticated user or null. Use at the top of every handler. */
export async function requireUser() {
  const supabase = getSupabaseServer();
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}
