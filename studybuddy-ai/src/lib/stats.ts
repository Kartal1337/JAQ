import { tr } from '@/locale/tr';
import type { StudySession } from '@/store/useStore';
import { dayKey, lastNDays } from './date';

/** Belirli bir günün toplam odak dakikası. */
export function minutesOnDay(sessions: StudySession[], key: string): number {
  return sessions
    .filter((s) => s.dayKey === key)
    .reduce((sum, s) => sum + s.durationMin, 0);
}

/** Bugünün toplam odak dakikası. */
export function todayMinutes(sessions: StudySession[]): number {
  return minutesOnDay(sessions, dayKey());
}

/** Bugün tamamlanan pomodoro sayısı. */
export function todayPomodoros(sessions: StudySession[]): number {
  return sessions.filter((s) => s.dayKey === dayKey()).length;
}

/** Toplam odak dakikası. */
export function totalMinutes(sessions: StudySession[]): number {
  return sessions.reduce((sum, s) => sum + s.durationMin, 0);
}

export interface DayBar {
  key: string;
  label: string;
  value: number; // o günün toplam odak dakikası
}

/** Son N gün için grafik verisi (gün etiketleriyle). */
export function dailyBars(sessions: StudySession[], days = 7): DayBar[] {
  const keys = lastNDays(days);
  return keys.map((key) => {
    const d = new Date(key + 'T00:00:00');
    // getDay: 0=Paz; bizim dizimiz Pzt=0
    const idx = (d.getDay() + 6) % 7;
    return { key, label: tr.history.days[idx], value: minutesOnDay(sessions, key) };
  });
}

export interface SubjectStat {
  subjectId: string;
  label: string;
  emoji: string;
  minutes: number;
}

/** En çok çalışılan konular (azalan). */
export function topSubjects(sessions: StudySession[], limit = 5): SubjectStat[] {
  const map = new Map<string, number>();
  for (const s of sessions) {
    if (!s.subjectId) continue;
    map.set(s.subjectId, (map.get(s.subjectId) ?? 0) + s.durationMin);
  }
  return [...map.entries()]
    .map(([subjectId, minutes]) => {
      const meta = tr.subjects.find((x) => x.id === subjectId);
      return {
        subjectId,
        label: meta?.label ?? subjectId,
        emoji: meta?.emoji ?? '📚',
        minutes,
      };
    })
    .sort((a, b) => b.minutes - a.minutes)
    .slice(0, limit);
}

/** En verimli günün dakikası. */
export function bestDayMinutes(sessions: StudySession[]): number {
  const map = new Map<string, number>();
  for (const s of sessions) {
    map.set(s.dayKey, (map.get(s.dayKey) ?? 0) + s.durationMin);
  }
  return Math.max(0, ...map.values());
}
