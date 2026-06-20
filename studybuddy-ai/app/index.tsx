import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { router } from 'expo-router';
import { useStore } from '@/store/useStore';
import { palette } from '@/theme/theme';

/**
 * Açılış yönlendiricisi: kalıcı veri yüklendikten sonra
 * onboarding tamamlandıysa sekmelere, değilse onboarding'e gider.
 */
export default function Index() {
  const hydrated = useStore((s) => s.hydrated);
  const onboarded = useStore((s) => s.onboarded);

  useEffect(() => {
    if (!hydrated) return;
    router.replace(onboarded ? '/(tabs)' : '/onboarding');
  }, [hydrated, onboarded]);

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.bg }}>
      <ActivityIndicator size="large" color={palette.primary} />
    </View>
  );
}
