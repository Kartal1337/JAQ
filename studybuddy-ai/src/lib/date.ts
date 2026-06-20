/** Tarih yardımcıları — hepsi cihazın yerel saatine göre çalışır. */

/** YYYY-MM-DD formatında yerel tarih anahtarı. */
export function dayKey(d: Date = new Date()): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** İki gün anahtarı arasındaki tam gün farkı. */
export function daysBetween(a: string, b: string): number {
  const da = new Date(a + 'T00:00:00');
  const db = new Date(b + 'T00:00:00');
  return Math.round((db.getTime() - da.getTime()) / (1000 * 60 * 60 * 24));
}

/** Son 7 günün gün anahtarları (bugün dahil, eskiden yeniye). */
export function lastNDays(n: number): string[] {
  const out: string[] = [];
  const now = new Date();
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    out.push(dayKey(d));
  }
  return out;
}

/** Dakikayı "1s 25dk" gibi okunur biçime çevirir. */
export function formatMinutes(min: number): string {
  if (min < 60) return `${min}dk`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m === 0 ? `${h}s` : `${h}s ${m}dk`;
}

/** Saniyeyi mm:ss biçimine çevirir. */
export function formatClock(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
