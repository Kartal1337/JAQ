import Link from 'next/link';
import { getSupabaseServer } from '@/lib/supabase/server';

// Server component: the renewal-driving numbers + the reply inbox.
export default async function Dashboard() {
  const supabase = getSupabaseServer();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-24">
        <p>Please sign in to view your dashboard.</p>
        <Link href="/onboarding" className="text-indigo-400 underline">Start onboarding</Link>
      </main>
    );
  }

  const [{ count: leadsCount }, { count: sentCount }, { count: repliedCount }, { count: bookedCount }, { data: replies }] =
    await Promise.all([
      supabase.from('leads').select('id', { count: 'exact', head: true }),
      supabase.from('messages').select('id', { count: 'exact', head: true }).eq('direction', 'outbound').eq('status', 'sent'),
      supabase.from('messages').select('id', { count: 'exact', head: true }).eq('direction', 'inbound'),
      supabase.from('appointments').select('id', { count: 'exact', head: true }),
      supabase.from('messages')
        .select('id, body, ai_reply_tag, created_at, lead:lead_id(business_name, email)')
        .eq('direction', 'inbound').order('created_at', { ascending: false }).limit(20),
    ]);

  const stats = [
    { label: 'Leads found', value: leadsCount ?? 0 },
    { label: 'Emails sent', value: sentCount ?? 0 },
    { label: 'Replies', value: repliedCount ?? 0 },
    { label: 'Meetings booked', value: bookedCount ?? 0, hero: true },
  ];

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link href="/onboarding" className="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium hover:bg-indigo-400">
          + New campaign
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        {stats.map((s) => (
          <div key={s.label} className={`rounded-xl border p-5 ${s.hero ? 'border-green-700 bg-green-950/30' : 'border-slate-800 bg-slate-900/50'}`}>
            <div className="text-3xl font-bold">{s.value}</div>
            <div className="mt-1 text-sm text-slate-400">{s.label}</div>
          </div>
        ))}
      </div>

      <h2 className="mt-12 text-lg font-semibold">Reply inbox</h2>
      <div className="mt-4 space-y-3">
        {(replies ?? []).length === 0 && <p className="text-slate-500">No replies yet. Once emails go out, replies show up here, tagged.</p>}
        {(replies ?? []).map((r: any) => (
          <div key={r.id} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">{r.lead?.business_name ?? r.lead?.email}</span>
              <Tag tag={r.ai_reply_tag} />
            </div>
            <p className="mt-2 line-clamp-3 text-sm text-slate-300">{r.body}</p>
          </div>
        ))}
      </div>
    </main>
  );
}

function Tag({ tag }: { tag: string | null }) {
  const map: Record<string, string> = {
    interested: 'bg-green-500/20 text-green-300',
    maybe: 'bg-yellow-500/20 text-yellow-300',
    no: 'bg-slate-500/20 text-slate-300',
    unsubscribe: 'bg-red-500/20 text-red-300',
  };
  const cls = tag ? map[tag] ?? 'bg-slate-700' : 'bg-slate-700';
  return <span className={`rounded-full px-3 py-1 text-xs ${cls}`}>{tag ?? 'untagged'}</span>;
}
