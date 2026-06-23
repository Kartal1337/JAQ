import { StyleSheet, View } from 'react-native';
import Animated, { FadeInUp } from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { gradients, palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';

export interface BarDatum {
  key: string;
  label: string;
  value: number;
}

interface Props {
  data: BarDatum[];
  height?: number;
  /** Çubuk üstündeki değeri biçimlendir (varsayılan: tam sayı). */
  formatValue?: (v: number) => string;
}

/** Basit, animasyonlu dikey çubuk grafik (ek bağımlılık gerektirmez). */
export function BarChart({ data, height = 160, formatValue }: Props) {
  const max = Math.max(1, ...data.map((d) => d.value));
  const fmt = formatValue ?? ((v: number) => String(Math.round(v)));

  return (
    <View style={[styles.wrap, { height: height + 28 }]}>
      {data.map((bar, i) => {
        const ratio = bar.value / max;
        const barHeight = Math.max(4, ratio * height);
        return (
          <View key={bar.key} style={styles.col}>
            <Txt variant="tiny" tone="faint" style={styles.value} numberOfLines={1}>
              {bar.value > 0 ? fmt(bar.value) : ''}
            </Txt>
            <View style={[styles.track, { height }]}>
              <Animated.View
                entering={FadeInUp.delay(i * 60).springify()}
                style={{ height: barHeight }}
              >
                <LinearGradient
                  colors={
                    bar.value > 0
                      ? gradients.brandVertical
                      : [palette.surfaceAlt, palette.surfaceAlt]
                  }
                  style={styles.bar}
                />
              </Animated.View>
            </View>
            <Txt variant="tiny" tone="muted" weight="medium" numberOfLines={1}>
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
