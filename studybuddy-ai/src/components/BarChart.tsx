import { StyleSheet, View } from 'react-native';
import Animated, { FadeInUp } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { gradients, palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';
import type { DayBar } from '@/lib/stats';

interface Props {
  data: DayBar[];
  height?: number;
}

/** Basit, animasyonlu dikey çubuk grafik (ek bağımlılık gerektirmez). */
export function BarChart({ data, height = 160 }: Props) {
  const max = Math.max(1, ...data.map((d) => d.minutes));

  return (
    <View style={[styles.wrap, { height: height + 28 }]}>
      {data.map((bar, i) => {
        const ratio = bar.minutes / max;
        const barHeight = Math.max(4, ratio * height);
        return (
          <View key={bar.key} style={styles.col}>
            <Txt variant="tiny" tone="faint" style={styles.value}>
              {bar.minutes > 0 ? bar.minutes : ''}
            </Txt>
            <View style={[styles.track, { height }]}>
              <Animated.View
                entering={FadeInUp.delay(i * 60).springify()}
                style={{ height: barHeight }}
              >
                <LinearGradient
                  colors={bar.minutes > 0 ? gradients.brandVertical : [palette.surfaceAlt, palette.surfaceAlt]}
                  style={styles.bar}
                />
              </Animated.View>
            </View>
            <Txt variant="tiny" tone="muted" weight="medium">
              {bar.label}
            </Txt>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between' },
  col: { flex: 1, alignItems: 'center', gap: 4 },
  track: { justifyContent: 'flex-end', width: '60%' },
  bar: { flex: 1, borderRadius: radius.sm, minHeight: 4 },
  value: { height: 14 },
});
