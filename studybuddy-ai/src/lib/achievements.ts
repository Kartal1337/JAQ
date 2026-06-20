import { tr } from '@/locale/tr';
import type { StudySession } from '@/store/useStore';
import { totalMinutes } from './stats';

export interface AchievementMeta {
  id: keyof typeof tr.achievements;
  title: string;
  desc: string;
  emoji: string;
}

export const ACHIEVEMENTS: AchievementMeta[] = (
  Object.keys(tr.achievements) as (keyof typeof tr.achievements)[]
).map((id) => ({ id, ...tr.achievements[id] }));

interface CheckInput {
  sessions: StudySession[];
  streakCurrent: number;
  now?: Date;
}

/**
 * Verilen duruma göre açılmış OLMASI gereken tüm başarım id'lerini döndürür.
 * Çağıran taraf zaten açık olanları filtreler.
 */
export function qualifiedAchievements({
  sessions,
  streakCurrent,
  now = new Date(),
}: CheckInput): string[] {
  const ids: string[] = [];
  const count = sessions.length;
  const total = totalMinutes(sessions);
  const hour = now.getHours();

  if (count >= 1) ids.push('firstPomodoro');
  if (count >= 50) ids.push('pomodoro50');
  if (streakCurrent >= 3) ids.push('streak3');
  if (streakCurrent >= 7) ids.push('streak7');
  if (streakCurrent >= 30) ids.push('streak30');
  if (total >= 600) ids.push('focus10h');
  if (hour >= 0 && hour < 5) ids.push('nightOwl');
  if (hour >= 4 && hour < 6) ids.push('earlyBird');

  return ids;
}
