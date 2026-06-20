import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { dayKey, daysBetween } from '@/lib/date';
import { qualifiedAchievements } from '@/lib/achievements';

export type AIProvider = 'openai' | 'grok' | 'claude';

export type PomodoroMode = '25_5' | '50_10';

export interface StudySession {
  id: string;
  date: string; // ISO timestamp
  dayKey: string; // YYYY-MM-DD (yerel)
  durationMin: number;
  topic: string;
  subjectId?: string;
  mode: PomodoroMode;
}

export interface Profile {
  name: string;
  levelId: string;
  interests: string[]; // subject id'leri
}

export interface Settings {
  apiKey: string;
  provider: AIProvider;
  notificationsEnabled: boolean;
  soundEnabled: boolean;
  defaultMode: PomodoroMode;
}

interface Streak {
  current: number;
  longest: number;
  lastStudyDay: string | null; // YYYY-MM-DD
}

interface StoreState {
  hydrated: boolean;
  onboarded: boolean;
  profile: Profile;
  settings: Settings;
  sessions: StudySession[];
  streak: Streak;
  achievements: string[]; // açılmış başarım id'leri

  // actions
  setHydrated: () => void;
  completeOnboarding: (profile: Profile) => void;
  updateProfile: (patch: Partial<Profile>) => void;
  updateSettings: (patch: Partial<Settings>) => void;
  addSession: (s: Omit<StudySession, 'id' | 'date' | 'dayKey'>) => StudySession;
  /** Seansı kaydeder ve hak edilen yeni başarımları açar; açılanları döndürür. */
  completeFocusSession: (
    s: Omit<StudySession, 'id' | 'date' | 'dayKey'>
  ) => { session: StudySession; newAchievements: string[] };
  unlockAchievement: (id: string) => boolean;
  resetAll: () => void;
}

const defaultProfile: Profile = { name: '', levelId: 'lise12', interests: [] };

const defaultSettings: Settings = {
  apiKey: '',
  provider: 'openai',
  notificationsEnabled: true,
  soundEnabled: true,
  defaultMode: '25_5',
};

const defaultStreak: Streak = { current: 0, longest: 0, lastStudyDay: null };

/** Yeni seans sonrası seriyi günceller (saf fonksiyon). */
function nextStreak(prev: Streak, today: string): Streak {
  if (prev.lastStudyDay === today) return prev; // bugün zaten sayıldı
  let current = 1;
  if (prev.lastStudyDay) {
    const diff = daysBetween(prev.lastStudyDay, today);
    if (diff === 1) current = prev.current + 1; // dün de çalışmış
    else if (diff <= 0) current = prev.current; // güvenlik
  }
  return {
    current,
    longest: Math.max(prev.longest, current),
    lastStudyDay: today,
  };
}

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      hydrated: false,
      onboarded: false,
      profile: defaultProfile,
      settings: defaultSettings,
      sessions: [],
      streak: defaultStreak,
      achievements: [],

      setHydrated: () => set({ hydrated: true }),

      completeOnboarding: (profile) => set({ onboarded: true, profile }),

      updateProfile: (patch) =>
        set((s) => ({ profile: { ...s.profile, ...patch } })),

      updateSettings: (patch) =>
        set((s) => ({ settings: { ...s.settings, ...patch } })),

      addSession: (input) => {
        const now = new Date();
        const session: StudySession = {
          ...input,
          id: `${now.getTime()}-${Math.random().toString(36).slice(2, 7)}`,
          date: now.toISOString(),
          dayKey: dayKey(now),
        };
        set((s) => ({
          sessions: [session, ...s.sessions],
          streak: nextStreak(s.streak, session.dayKey),
        }));
        return session;
      },

      completeFocusSession: (input) => {
        const session = get().addSession(input);
        const after = get();
        const qualified = qualifiedAchievements({
          sessions: after.sessions,
          streakCurrent: after.streak.current,
        });
        const newAchievements = qualified.filter(
          (id) => !after.achievements.includes(id)
        );
        if (newAchievements.length) {
          set((s) => ({ achievements: [...s.achievements, ...newAchievements] }));
        }
        return { session, newAchievements };
      },

      unlockAchievement: (id) => {
        if (get().achievements.includes(id)) return false;
        set((s) => ({ achievements: [...s.achievements, id] }));
        return true;
      },

      resetAll: () =>
        set({
          onboarded: false,
          profile: defaultProfile,
          settings: defaultSettings,
          sessions: [],
          streak: defaultStreak,
          achievements: [],
        }),
    }),
    {
      name: 'studybuddy-store-v1',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({
        onboarded: s.onboarded,
        profile: s.profile,
        settings: s.settings,
        sessions: s.sessions,
        streak: s.streak,
        achievements: s.achievements,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHydrated();
      },
    }
  )
);
