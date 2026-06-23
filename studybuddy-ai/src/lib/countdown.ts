/**
 * YKS geri sayımı yardımcıları.
 * Sınav tarihi ÖSYM tarafından her yıl değişebildiği için, Haziran'ın
 * 3. cumartesisini TAHMİN olarak kullanırız; kullanıcı Profil'den
 * tam tarihi değiştirebilir.
 */

import { dayKey, daysBetween } from './date';

/** Verilen yıl için tahmini YKS tarihi (Haziran'ın 3. cumartesisi). */
export function estimateYksDate(year: number): Date {
  const june1 = new Date(year, 5, 1);
  const offsetToSat = (6 - june1.getDay() + 7) % 7; // ilk cumartesiye kayma
  const thirdSat = 1 + offsetToSat + 14;
  return new Date(year, 5, thirdSat);
}

export interface YksYearOption {
  year: number;
  dateKey: string; // YYYY-MM-DD
  label: string; // "YKS 2027"
}

/**
 * Bugünden itibaren gelecekteki ilk `count` YKS yılını döndürür.
 * (Bu yılki sınav geçtiyse otomatik bir sonraki yıldan başlar.)
 */
export function upcomingYksYears(count = 3, from: Date = new Date()): YksYearOption[] {
  let startYear = from.getFullYear();
  if (estimateYksDate(startYear).getTime() < from.getTime()) startYear += 1;

  const out: YksYearOption[] = [];
  for (let i = 0; i < count; i++) {
    const year = startYear + i;
    out.push({
      year,
      dateKey: dayKey(estimateYksDate(year)),
      label: `YKS ${year}`,
    });
  }
  return out;
}

/** Hedef tarihe kalan tam gün (geçmişse negatif). */
export function daysUntil(targetDateKey: string, from: Date = new Date()): number {
  return daysBetween(dayKey(from), targetDateKey);
}

export interface Countdown {
  days: number; // kalan gün (>=0; geçtiyse 0)
  weeks: number; // kalan tam hafta
  passed: boolean; // sınav geçti mi
  isToday: boolean; // bugün mü
}

export function getCountdown(targetDateKey: string, from: Date = new Date()): Countdown {
  const raw = daysUntil(targetDateKey, from);
  return {
    days: Math.max(0, raw),
    weeks: Math.max(0, Math.floor(raw / 7)),
    passed: raw < 0,
    isToday: raw === 0,
  };
}

/** Geri sayıma göre kısa motivasyon alt metni. */
export function countdownMood(days: number): string {
  if (days <= 0) return 'Bugün senin günün! Sakin ol, hazırsın 💪';
  if (days <= 7) return 'Son düzlük! Tekrar ve deneme zamanı 🔥';
  if (days <= 30) return 'Son ay — eksiklere odaklan, panik yok 🎯';
  if (days <= 100) return 'Kritik dönem! Her gün net kazancı 📈';
  if (days <= 200) return 'İstikrar kazandıran dönemdesin, devam 🚀';
  return 'Erken başlayan kazanır. Temeli sağlam at 🌱';
}
