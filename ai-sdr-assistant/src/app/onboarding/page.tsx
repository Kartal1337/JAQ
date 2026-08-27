'use client';

import { useState } from 'react';

// Minimal onboarding that drives the "magic moment":
// describe target -> create campaign -> find leads -> see personalized emails.
export default function Onboarding() {
  const [step, setStep] = useState<'describe' | 'finding' | 'review'>('describe');
  const [niche, setNiche] = useState('dentists');
  const [location, setLocation] = useState('Austin TX');
  const [offer, setOffer] = useState('I build websites that book more appointments for local clinics.');
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setError(null);
    setStep('finding');
    try {
      const c = await fetch('/api/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${niche} – ${location}`,
          target_query: niche,
          location,
          offer,
        }),
      }).then((r) => r.json());
      if (!c.campaign) throw new Error('Could not create campaign (are you signed in?)');
      setCampaignId(c.campaign.id);

      await fetch(`/api/campaigns/${c.campaign.id}/find-leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 25 }),
      });

      // Poll until drafts are generated
      await poll(c.campaign.id);
    } catch (e: any) {
      setError(e.message);
      setStep('describe');
    }
  }

  async function poll(id: string, tries = 0) {
    const res = await fetch(`/api/campaigns/${id}/leads`).then((r) => r.json());
    const withDraft = (res.leads ?? []).filter((l: any) => l.messages?.length);
    if (withDraft.length >= 1 || tries > 30) {
      setLeads(res.leads ?? []);
      setStep('review');
      return;
    }
    setTimeout(() => poll(id, tries + 1), 2000);
  }

  async function launch() {
    if (!campaignId) return;
    await fetch(`/api/campaigns/${campaignId}/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ perDay: 20 }),
    });
    window.location.href = '/dashboard';
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-bold">Let’s get you 25 leads in 3 minutes</h1>

      {error && <p className="mt-4 rounded bg-red-950 px-4 py-2 text-red-300">{error}</p>}

      {step === 'describe' && (
        <div className="mt-8 space-y-5">
          <Field label="Who do you want as customers?">
            <input className="input" value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="dentists" />
          </Field>
          <Field label="Where?">
            <input className="input" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="Austin TX" />
          </Field>
          <Field label="What do you offer them? (this powers the AI)">
            <textarea className="input min-h-24" value={offer} onChange={(e) => setOffer(e.target.value)} />
          </Field>
          <button onClick={start} className="rounded-lg bg-indigo-500 px-5 py-3 font-medium hover:bg-indigo-400">
            Find 25 leads →
          </button>
          <style>{`.input{width:100%;border-radius:.5rem;background:#0f172a;border:1px solid #1e293b;padding:.7rem .9rem;color:#e2e8f0}`}</style>
        </div>
      )}

      {step === 'finding' && (
        <div className="mt-16 text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
          <p className="mt-4 text-slate-300">Finding businesses and writing a personalized email for each…</p>
        </div>
      )}

      {step === 'review' && (
        <div className="mt-8">
          <p className="text-slate-300">
            Found <b>{leads.length}</b> leads. Each already has a personalized email. Review, then launch.
          </p>
          <div className="mt-6 space-y-4">
            {leads.map((l) => {
              const draft = l.messages?.find((m: any) => m.direction === 'outbound');
              return (
                <div key={l.id} className="rounded-lg border border-slate-800 bg-slate-900/50 p-4">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold">{l.business_name}</span>
                    <span className="text-slate-400">{l.email}</span>
                  </div>
                  {draft && (
                    <div className="mt-3 rounded bg-slate-950 p-3 text-sm text-slate-300">
                      <div className="font-medium text-slate-200">Subject: {draft.subject}</div>
                      <pre className="mt-2 whitespace-pre-wrap font-sans">{draft.body}</pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <button onClick={launch} className="mt-8 rounded-lg bg-green-500 px-6 py-3 font-semibold text-slate-950 hover:bg-green-400">
            Launch — send these over the next 3 days →
          </button>
        </div>
      )}
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm text-slate-400">{label}</span>
      {children}
    </label>
  );
}
