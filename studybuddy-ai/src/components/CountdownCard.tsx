import { StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { gradients, palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';
import { countdownMood, getCountdown } from '@/lib/countdown';
import { tr } from '@/locale/tr';

interface Props {
  dateKey: string;
  label: string; // "YKS 2027"
}

/** Hedef sınava kalan günü gösteren geri sayım kartı. */
export function CountdownCard({ dateKey, label }: Props) {
  const cd = getCountdown(dateKey);

  return (
    <LinearGradient
      colors={gradients.brandVertical}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.card}
    >
      <View style={styles.headerRow}>
        <Txt variant="tiny" weight="bold" style={styles.label}>
          {label.toUpperCase()}
        </Txt>
        <Txt style={styles.icon}>🎯</Txt>
      </View>

      {cd.isToday ? (
        <Txt variant="h1" weight="black" style={styles.today}>
          {tr.countdown.today}
        </Txt>
      ) : (
        <View style={styles.numberRow}>
          <Txt variant="display" weight="black">
            {cd.days}
          </Txt>
          <View style={styles.unitWrap}>
            <Txt variant="h3" weight="bold">
              {tr.countdown.daysLeft}
            </Txt>
            {cd.weeks > 0 && (
              <Txt variant="tiny" style={styles.weeks}>
                ≈ {cd.weeks} {tr.countdown.weeksShort}
              </Txt>
            )}
          </View>
        </View>
      )}

      {!cd.isToday && (
        <Txt variant="small" weight="medium" style={styles.mood}>
          {countdownMood(cd.days)}
        </Txt>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.xl, padding: spacing.xl, overflow: 'hidden' },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { color: '#FFFFFFCC', letterSpacing: 1.5 },
  icon: { fontSize: 26 },
  numberRow: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.md, marginTop: spacing.sm },
  unitWrap: { marginBottom: spacing.sm },
  weeks: { color: '#FFFFFFCC', marginTop: 2 },
  today: { marginTop: spacing.sm },
  mood: { color: '#FFFFFFEE', marginTop: spacing.md },
});
