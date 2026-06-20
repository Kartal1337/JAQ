import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import * as Haptics from 'expo-haptics';
import { useKeepAwake } from 'expo-keep-awake';
import type { PomodoroMode } from '@/store/useStore';
import * as Notif from '@/lib/notifications';

export type Phase = 'focus' | 'break';

export interface PomodoroConfig {
  focusMin: number;
  breakMin: number;
}

export const MODE_CONFIG: Record<PomodoroMode, PomodoroConfig> = {
  '25_5': { focusMin: 25, breakMin: 5 },
  '50_10': { focusMin: 50, breakMin: 10 },
};

interface Args {
  mode: PomodoroMode;
  notificationsEnabled: boolean;
  /** Odak fazı bittiğinde (geçen dakikayla) çağrılır. */
  onFocusComplete: (focusMinutes: number) => void;
  /** Mola bittiğinde çağrılır. */
  onBreakComplete?: () => void;
}

/**
 * Zaman damgası tabanlı pomodoro motoru.
 * Uygulama arka plana alınıp geri gelince kalan süre tekrar hesaplanır,
 * böylece sayaç hep doğru kalır. Bitişte yerel bildirim planlanır.
 */
export function usePomodoro({
  mode,
  notificationsEnabled,
  onFocusComplete,
  onBreakComplete,
}: Args) {
  const cfg = MODE_CONFIG[mode];
  const fullSeconds = (phase: Phase) =>
    (phase === 'focus' ? cfg.focusMin : cfg.breakMin) * 60;

  const [phase, setPhase] = useState<Phase>('focus');
  const [running, setRunning] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(fullSeconds('focus'));

  const endAtRef = useRef<number | null>(null); // bitiş zaman damgası (ms)
  const notifIdRef = useRef<string | null>(null);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completeRef = useRef<() => void>(() => {});

  useKeepAwake(); // çalışırken ekran açık kalsın

  const total = fullSeconds(phase);

  // Mod değişince ve durmuşken sayacı sıfırla
  useEffect(() => {
    if (!running) {
      setSecondsLeft(fullSeconds(phase));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  const clearTick = () => {
    if (tickRef.current) {
      clearInterval(tickRef.current);
      tickRef.current = null;
    }
  };

  const handlePhaseComplete = useCallback(() => {
    clearTick();
    endAtRef.current = null;
    setRunning(false);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

    if (phase === 'focus') {
      onFocusComplete(cfg.focusMin);
      setPhase('break');
      setSecondsLeft(fullSeconds('break'));
    } else {
      onBreakComplete?.();
      setPhase('focus');
      setSecondsLeft(fullSeconds('focus'));
    }
  }, [phase, cfg.focusMin, onFocusComplete, onBreakComplete]);

  // En güncel complete handler'ı ref'te tut (interval kapanışı için)
  completeRef.current = handlePhaseComplete;

  const syncFromClock = useCallback(() => {
    if (endAtRef.current == null) return;
    const remaining = Math.round((endAtRef.current - Date.now()) / 1000);
    if (remaining <= 0) {
      setSecondsLeft(0);
      completeRef.current();
    } else {
      setSecondsLeft(remaining);
    }
  }, []);

  const start = useCallback(async () => {
    const dur = secondsLeft > 0 ? secondsLeft : total;
    endAtRef.current = Date.now() + dur * 1000;
    setRunning(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => {});

    if (notificationsEnabled) {
      notifIdRef.current = await Notif.scheduleSessionEnd(dur, phase);
    }

    clearTick();
    tickRef.current = setInterval(syncFromClock, 250);
  }, [secondsLeft, total, phase, notificationsEnabled, syncFromClock]);

  const pause = useCallback(async () => {
    clearTick();
    syncFromClock(); // kalan süreyi sabitle
    endAtRef.current = null;
    setRunning(false);
    await Notif.cancel(notifIdRef.current);
    notifIdRef.current = null;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
  }, [syncFromClock]);

  const reset = useCallback(async () => {
    clearTick();
    endAtRef.current = null;
    setRunning(false);
    await Notif.cancel(notifIdRef.current);
    notifIdRef.current = null;
    setSecondsLeft(fullSeconds(phase));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, mode]);

  /** "Bitir": odak fazındaysa o ana kadarki süreyi seans olarak kaydeder. */
  const finish = useCallback(async () => {
    clearTick();
    await Notif.cancel(notifIdRef.current);
    notifIdRef.current = null;
    const elapsedSec = total - secondsLeft;
    endAtRef.current = null;
    setRunning(false);

    if (phase === 'focus' && elapsedSec >= 60) {
      onFocusComplete(Math.round(elapsedSec / 60));
    }
    setPhase('focus');
    setSecondsLeft(fullSeconds('focus'));
  }, [phase, total, secondsLeft, onFocusComplete]);

  // Arka plandan dönünce saati senkronize et
  useEffect(() => {
    const sub = AppState.addEventListener('change', (s: AppStateStatus) => {
      if (s === 'active' && running) syncFromClock();
    });
    return () => sub.remove();
  }, [running, syncFromClock]);

  // Temizlik
  useEffect(() => () => clearTick(), []);

  const progress = total > 0 ? 1 - secondsLeft / total : 0;

  return {
    phase,
    running,
    secondsLeft,
    total,
    progress,
    start,
    pause,
    reset,
    finish,
  };
}
