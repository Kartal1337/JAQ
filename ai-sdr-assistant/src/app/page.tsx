import Link from 'next/link';

export default function Home() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-24">
      <h1 className="text-4xl font-bold tracking-tight">AI SDR Assistant</h1>
      <p className="mt-4 text-lg text-slate-300">
        Tell it who you want as customers. It finds real leads, writes a
        personalized email for each one, sends on a drip, and surfaces the
        replies worth answering.
      </p>
      <div className="mt-8 flex gap-3">
        <Link
          href="/onboarding"
          className="rounded-lg bg-indigo-500 px-5 py-3 font-medium text-white hover:bg-indigo-400"
        >
          Get 25 free leads →
        </Link>
        <Link
          href="/dashboard"
          className="rounded-lg border border-slate-700 px-5 py-3 font-medium hover:bg-slate-900"
        >
          Dashboard
        </Link>
      </div>
      <p className="mt-6 text-sm text-slate-500">
        Email outreach is fully automated. Instagram/LinkedIn are assisted
        (we write it, you hit send) to keep your accounts safe.
      </p>
    </main>
  );
}
