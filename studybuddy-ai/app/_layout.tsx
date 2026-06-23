import { useEffect } from 'react';
import { View } from 'react-native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { configureNotifications } from '@/lib/notifications';
import { palette } from '@/theme/theme';

// Bildirim davranışını uygulama açılışında bir kez ayarla
configureNotifications();

export default function RootLayout() {
  useEffect(() => {
    // Reanimated/Gesture handler erken yüklensin
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: palette.bg }}>
      <SafeAreaProvider>
        <View style={{ flex: 1, backgroundColor: palette.bg }}>
          <StatusBar style="light" />
          <Stack
            screenOptions={{
              headerShown: false,
              contentStyle: { backgroundColor: palette.bg },
              animation: 'fade',
            }}
          >
            <Stack.Screen name="index" />
            <Stack.Screen name="onboarding" />
            <Stack.Screen name="(tabs)" />
            <Stack.Screen name="deneme/index" options={{ animation: 'slide_from_right' }} />
            <Stack.Screen
              name="deneme/ekle"
              options={{ animation: 'slide_from_bottom', presentation: 'modal' }}
            />
          </Stack>
        </View>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
