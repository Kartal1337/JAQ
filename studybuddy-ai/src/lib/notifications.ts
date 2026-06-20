/**
 * Pomodoro bildirimleri.
 * Expo Go ile yerel (local) bildirimler çalışır; push token gerekmez.
 */

import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { tr } from '@/locale/tr';

let configured = false;

export function configureNotifications() {
  if (configured) return;
  configured = true;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
}

export async function ensurePermission(): Promise<boolean> {
  const { status } = await Notifications.getPermissionsAsync();
  if (status === 'granted') return true;
  const req = await Notifications.requestPermissionsAsync();
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('pomodoro', {
      name: 'Pomodoro',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#7C5CFF',
    });
  }
  return req.status === 'granted';
}

/**
 * Seansın bitişine bildirim planlar. Uygulama arka plandayken bile çalışır.
 * Dönen id ile iptal edilebilir.
 */
export async function scheduleSessionEnd(
  seconds: number,
  phase: 'focus' | 'break'
): Promise<string | null> {
  const ok = await ensurePermission();
  if (!ok) return null;
  const isFocus = phase === 'focus';
  return Notifications.scheduleNotificationAsync({
    content: {
      title: isFocus
        ? tr.notification.focusDoneTitle
        : tr.notification.breakDoneTitle,
      body: isFocus
        ? tr.notification.focusDoneBody
        : tr.notification.breakDoneBody,
      sound: true,
    },
    trigger: {
      type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
      seconds: Math.max(1, Math.round(seconds)),
    },
  });
}

export async function cancel(id: string | null) {
  if (id) await Notifications.cancelScheduledNotificationAsync(id).catch(() => {});
}

export async function cancelAll() {
  await Notifications.cancelAllScheduledNotificationsAsync().catch(() => {});
}
