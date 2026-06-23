import type { MockExam } from '@/store/useStore';
import { calcNet, subjectLabel } from '@/constants/yks';

/** Bir denemenin toplam neti (kayıtlı totalNet yoksa hesaplar). */
export function examTotalNet(e: MockExam): number {
  if (typeof e.totalNet === 'number') return e.totalNet;
  return Object.values(e.results).reduce(
    (sum, r) => sum + calcNet(r.correct, r.wrong),
    0
  );
}

export interface TrendPoint {
  key: string;
  label: string; // kısa tarih, ör. "12.06"
  value: number; // toplam net
}

/** Denemeleri tarihe göre (eskiden yeniye) net trendine çevirir. */
export function netTrend(exams: MockExam[], kind?: 'TYT' | 'AYT'): TrendPoint[] {
  return exams
    .filter((e) => !kind || e.kind === kind)
    .slice()
    .reverse()
    .map((e) => {
      const d = new Date(e.date);
      const label = `${String(d.getDate()).padStart(2, '0')}.${String(
        d.getMonth() + 1
      ).padStart(2, '0')}`;
      return { key: e.id, label, value: Math.round(examTotalNet(e) * 100) / 100 };
    });
}

export interface SubjectAvg {
  key: string;
  label: string;
  avgNet: number;
  maxNet: number; // o derste mümkün en yüksek net (soru sayısı)
  ratio: number; // avgNet / maxNet (0..1)
}

/**
 * Ders bazında ortalama net ve başarı oranı.
 * Oran düşükten yükseğe sıralı → ilk sıradakiler zayıf konular.
 */
export function subjectAverages(exams: MockExam[]): SubjectAvg[] {
  const sum = new Map<string, { net: number; count: number; max: number }>();

  for (const e of exams) {
    for (const [key, r] of Object.entries(e.results)) {
      const entry = sum.get(key) ?? { net: 0, count: 0, max: 0 };
      entry.net += calcNet(r.correct, r.wrong);
      entry.count += 1;
      // o anki denemede dersin soru sayısını korelasyon için sakla
      entry.max = Math.max(entry.max, r.correct + r.wrong);
      sum.set(key, entry);
    }
  }

  return [...sum.entries()]
    .map(([key, v]) => {
      const avgNet = Math.round((v.net / v.count) * 100) / 100;
      const maxNet = v.max || 1;
      return {
        key,
        label: subjectLabel(key),
        avgNet,
        maxNet,
        ratio: Math.max(0, Math.min(1, avgNet / maxNet)),
      };
    })
    .sort((a, b) => a.ratio - b.ratio);
}

export function bestNet(exams: MockExam[], kind?: 'TYT' | 'AYT'): number {
  const list = exams.filter((e) => !kind || e.kind === kind);
  if (!list.length) return 0;
  return Math.max(...list.map(examTotalNet));
}

export function averageNet(exams: MockExam[], kind?: 'TYT' | 'AYT'): number {
  const list = exams.filter((e) => !kind || e.kind === kind);
  if (!list.length) return 0;
  const total = list.reduce((s, e) => s + examTotalNet(e), 0);
  return Math.round((total / list.length) * 100) / 100;
}

/** Son iki denemenin net farkı (trend yönü). */
export function lastDelta(exams: MockExam[], kind?: 'TYT' | 'AYT'): number | null {
  const list = exams.filter((e) => !kind || e.kind === kind);
  if (list.length < 2) return null;
  return Math.round((examTotalNet(list[0]) - examTotalNet(list[1])) * 100) / 100;
}
