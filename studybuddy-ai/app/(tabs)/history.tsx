import { useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { Screen } from '@/components/Screen';
import { Txt } from '@/components/Txt';
import { Card } from '@/components/Card';
import { Chip } from '@/components/Chip';
import { StatTile } from '@/components/StatTile';
import { BarChart } from '@/components/BarChart';
import { useStore } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import { formatMinutes } from '@/lib/date';
import {
  bestDayMinutes,
  dailyBars,
  topSubjects,
  totalMinutes,
} from '@/lib/stats';

type Range = 'weekly' | 'monthly';

export default function History() {
  const sessions = useStore((s) => s.sessions);
  const [range, setRange] = useState<Range>('weekly');

  const bars = useMemo(
    () => dailyBars(sessions, range === 'weekly' ? 7 : 30),
    [sessions, range]
  );
  const total = useMemo(() => totalMinutes(sessions), [sessions]);
  const best = useMemo(() => bestDayMinutes(sessions), [sessions]);
  const subjects = useMemo(() => topSubjects(sessions), [sessions]);

  const hasData = sessions.length > 0;
  const maxSubjectMin = Math.max(1, ...subjects.map((s) => s.minutes));

  return (
    <Screen scroll>
      <Txt variant="h1" weight="black" style={styles.title}>
        {tr.history.title}
      </Txt>

      {/* Aralık seçimi */}
      <View style={styles.rangeRow}>
        <Chip
          label={tr.history.weekly}
          selected={range === 'weekly'}
          onPress={() => setRange('weekly')}
        />
        <Chip
          label={tr.history.monthly}
          selected={range === 'monthly'}
          onPress={() => setRange('monthly')}
        />
      </View>

      {/* Grafik */}
      <Animated.View entering={FadeInDown.duration(400)}>
        <Card style={styles.chartCard}>
          {hasData ? (
            <BarChart data={range === 'weekly' ? bars : bars.slice(-7)} />
          ) : (
            <Txt variant="body" tone="muted" center style={{ paddingVertical: spacing.xxl }}>
              {tr.history.noData}
            </Txt>
          )}
        </Card>
      </Animated.View>

      {/* Özet istatistikler */}
      <Animated.View entering={FadeInDown.delay(100).duration(400)} style={styles.statRow}>
        <StatTile
          icon="hourglass"
          value={formatMinutes(total)}
          label={tr.history.totalFocus}
          tint={palette.primary}
        />
        <StatTile
          icon="flame"
          value={formatMinutes(best)}
          label={tr.history.bestDay}
          tint={palette.streak}
        />
        <StatTile
          icon="checkmark-done"
          value={String(sessions.length)}
          label={tr.history.totalPomodoros}
          tint={palette.success}
        />
      </Animated.View>

      {/* En çok çalışılan konular */}
      <Animated.View entering={FadeInDown.delay(180).duration(400)} style={styles.block}>
        <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
          {tr.history.topSubjects}
        </Txt>
        <Card>
          {subjects.length === 0 ? (
            <Txt variant="small" tone="muted" center style={{ paddingVertical: spacing.lg }}>
              {tr.history.noData}
            </Txt>
          ) : (
            subjects.map((s, i) => (
              <View key={s.subjectId} style={[styles.subjectRow, i > 0 && styles.divider]}>
                <Txt style={styles.subjectEmoji}>{s.emoji}</Txt>
                <View style={{ flex: 1 }}>
                  <View style={styles.subjectLabelRow}>
                    <Txt variant="body" weight="semibold">
                      {s.label}
                    </Txt>
                    <Txt variant="small" tone="muted" weight="medium">
                      {formatMinutes(s.minutes)}
                    </Txt>
                  </View>
                  <View style={styles.barBg}>
                    <View
                      style={[
                        styles.barFill,
                        { width: `${(s.minutes / maxSubjectMin) * 100}%` },
                      ]}
                    />
                  </View>
                </View>
              </View>
            ))
          )}
        </Card>
      </Animated.View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginTop: spacing.sm, marginBottom: spacing.lg },
  rangeRow: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.lg },
  chartCard: { paddingVertical: spacing.xl },
  statRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg },
  block: { marginTop: spacing.xl },
  sectionTitle: { marginBottom: spacing.md },
  subjectRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.md },
  divider: { borderTopWidth: 1, borderTopColor: palette.border },
  subjectEmoji: { fontSize: 26 },
  subjectLabelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  barBg: {
    height: 8,
    borderRadius: radius.full,
    backgroundColor: palette.surfaceAlt,
    overflow: 'hidden',
  },
  barFill: { height: 8, borderRadius: radius.full, backgroundColor: palette.primary },
});
