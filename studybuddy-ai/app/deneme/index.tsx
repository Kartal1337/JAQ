import { useMemo, useState } from 'react';
import { Alert, Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { ScrollView } from 'react-native';
import { Txt } from '@/components/Txt';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { Chip } from '@/components/Chip';
import { Header } from '@/components/Header';
import { StatTile } from '@/components/StatTile';
import { BarChart } from '@/components/BarChart';
import { useStore, type MockExam } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import { formatNet } from '@/constants/yks';
import {
  averageNet,
  bestNet,
  examTotalNet,
  lastDelta,
  netTrend,
  subjectAverages,
} from '@/lib/denemeStats';

type Filter = 'all' | 'TYT' | 'AYT';

export default function DenemeList() {
  const exams = useStore((s) => s.mockExams);
  const deleteMockExam = useStore((s) => s.deleteMockExam);

  const [filter, setFilter] = useState<Filter>('all');
  const kind = filter === 'all' ? undefined : filter;

  const filtered = useMemo(
    () => exams.filter((e) => !kind || e.kind === kind),
    [exams, kind]
  );
  const trend = useMemo(() => netTrend(exams, kind).slice(-8), [exams, kind]);
  const weak = useMemo(() => subjectAverages(filtered), [filtered]);
  const last = filtered[0] ? examTotalNet(filtered[0]) : 0;
  const delta = lastDelta(exams, kind);

  const confirmDelete = (e: MockExam) => {
    Alert.alert(tr.deneme.delete, tr.deneme.deleteConfirm, [
      { text: tr.profile.cancel, style: 'cancel' },
      { text: tr.deneme.delete, style: 'destructive', onPress: () => deleteMockExam(e.id) },
    ]);
  };

  const askAI = () => {
    const lines = filtered.slice(0, 5).map((e) => {
      const subs = Object.entries(e.results)
        .map(([k, r]) => `${k}: D${r.correct} Y${r.wrong}`)
        .join(', ');
      return `- ${e.kind}${e.fieldId ? ` (${e.fieldId})` : ''} "${e.name || 'Deneme'}" — toplam ${formatNet(
        examTotalNet(e)
      )} net | ${subs}`;
    });
    const weakText = weak
      .slice(0, 3)
      .map((w) => `${w.label} (ort. ${formatNet(w.avgNet)} net)`)
      .join(', ');
    const draft = `Deneme sonuçlarımı analiz et ve error_analysis_skill ile zayıf konularımı çıkar, sonra study_plan_skill ile bu hafta neye odaklanmam gerektiğini söyle.\n\nSon denemelerim:\n${lines.join(
      '\n'
    )}\n\nEn zayıf görünen dersler: ${weakText}`;
    router.push({ pathname: '/(tabs)/chat', params: { draft } });
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.padded}>
        <Header
          title={tr.deneme.title}
          subtitle={tr.deneme.subtitle}
          right={
            <Pressable onPress={() => router.push('/deneme/ekle')} hitSlop={8}>
              <Ionicons name="add-circle" size={32} color={palette.primary} />
            </Pressable>
          }
        />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Filtre */}
        <View style={styles.filterRow}>
          <Chip label="Tümü" selected={filter === 'all'} onPress={() => setFilter('all')} />
          <Chip label="TYT" selected={filter === 'TYT'} onPress={() => setFilter('TYT')} />
          <Chip label="AYT" selected={filter === 'AYT'} onPress={() => setFilter('AYT')} />
        </View>

        {filtered.length === 0 ? (
          <Card style={styles.emptyCard}>
            <Txt style={styles.emptyEmoji}>📝</Txt>
            <Txt variant="body" tone="muted" center>
              {tr.deneme.empty}
            </Txt>
            <Button
              label={tr.deneme.add}
              icon="add"
              onPress={() => router.push('/deneme/ekle')}
              style={{ marginTop: spacing.lg, alignSelf: 'stretch' }}
            />
          </Card>
        ) : (
          <>
            {/* Özet */}
            <View style={styles.statRow}>
              <StatTile
                icon="trending-up"
                value={formatNet(last)}
                label={tr.deneme.lastNet}
                tint={palette.primary}
              />
              <StatTile
                icon="stats-chart"
                value={formatNet(averageNet(exams, kind))}
                label={tr.deneme.avgNet}
                tint={palette.accent}
              />
              <StatTile
                icon="trophy"
                value={formatNet(bestNet(exams, kind))}
                label={tr.deneme.bestNet}
                tint={palette.streak}
              />
            </View>

            {delta !== null && (
              <View style={styles.deltaRow}>
                <Ionicons
                  name={delta >= 0 ? 'arrow-up-circle' : 'arrow-down-circle'}
                  size={18}
                  color={delta >= 0 ? palette.success : palette.danger}
                />
                <Txt variant="small" tone={delta >= 0 ? 'success' : 'streak'} weight="semibold">
                  {delta >= 0 ? '+' : ''}
                  {formatNet(delta)} net (son denemeye göre)
                </Txt>
              </View>
            )}

            {/* Net trendi */}
            {trend.length > 1 && (
              <Animated.View entering={FadeInDown.duration(400)} style={styles.block}>
                <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
                  {tr.deneme.netTrend}
                </Txt>
                <Card style={{ paddingVertical: spacing.xl }}>
                  <BarChart data={trend} formatValue={(v) => formatNet(v)} />
                </Card>
              </Animated.View>
            )}

            {/* Zayıf konular */}
            {weak.length > 0 && (
              <Animated.View entering={FadeInDown.delay(80).duration(400)} style={styles.block}>
                <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
                  {tr.deneme.weakSubjects}
                </Txt>
                <Card>
                  {weak.map((w, i) => (
                    <View key={w.key} style={[styles.weakRow, i > 0 && styles.divider]}>
                      <View style={styles.weakLabel}>
                        <Txt variant="body" weight="semibold">
                          {w.label}
                        </Txt>
                        <Txt variant="small" tone="muted">
                          ort. {formatNet(w.avgNet)} / {w.maxNet} {tr.deneme.net}
                        </Txt>
                      </View>
                      <View style={styles.barBg}>
                        <View
                          style={[
                            styles.barFill,
                            {
                              width: `${Math.round(w.ratio * 100)}%`,
                              backgroundColor:
                                w.ratio < 0.4
                                  ? palette.danger
                                  : w.ratio < 0.7
                                  ? palette.warning
                                  : palette.success,
                            },
                          ]}
                        />
                      </View>
                    </View>
                  ))}
                </Card>
                <Button
                  label={tr.deneme.askAI}
                  icon="sparkles"
                  variant="solid"
                  onPress={askAI}
                  style={{ marginTop: spacing.md }}
                />
              </Animated.View>
            )}

            {/* Deneme listesi */}
            <View style={styles.block}>
              <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
                {tr.deneme.title}
              </Txt>
              {filtered.map((e) => (
                <Card key={e.id} style={styles.examCard}>
                  <View style={{ flex: 1 }}>
                    <View style={styles.examTop}>
                      <View style={[styles.kindBadge, e.kind === 'AYT' && styles.aytBadge]}>
                        <Txt variant="tiny" weight="bold" tone="inverse">
                          {e.kind}
                        </Txt>
                      </View>
                      <Txt variant="body" weight="semibold" numberOfLines={1} style={{ flex: 1 }}>
                        {e.name || 'Deneme'}
                      </Txt>
                    </View>
                    <Txt variant="tiny" tone="faint" style={{ marginTop: 2 }}>
                      {new Date(e.date).toLocaleDateString('tr-TR')}
                    </Txt>
                  </View>
                  <View style={styles.examRight}>
                    <Txt variant="h2" weight="black" tone="primary">
                      {formatNet(examTotalNet(e))}
                    </Txt>
                    <Txt variant="tiny" tone="faint">
                      {tr.deneme.net}
                    </Txt>
                  </View>
                  <Pressable onPress={() => confirmDelete(e)} hitSlop={8} style={styles.trash}>
                    <Ionicons name="trash-outline" size={18} color={palette.textFaint} />
                  </Pressable>
                </Card>
              ))}
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  padded: { paddingHorizontal: spacing.lg },
  content: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxxl },
  filterRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  emptyCard: { alignItems: 'center', marginTop: spacing.xl },
  emptyEmoji: { fontSize: 48, marginBottom: spacing.md },
  statRow: { flexDirection: 'row', gap: spacing.sm },
  deltaRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginTop: spacing.md },
  block: { marginTop: spacing.xl },
  sectionTitle: { marginBottom: spacing.md },
  weakRow: { paddingVertical: spacing.md },
  weakLabel: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 6 },
  divider: { borderTopWidth: 1, borderTopColor: palette.border },
  barBg: { height: 8, borderRadius: radius.full, backgroundColor: palette.surfaceAlt, overflow: 'hidden' },
  barFill: { height: 8, borderRadius: radius.full },
  examCard: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.sm },
  examTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  kindBadge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.sm,
    backgroundColor: palette.primary,
  },
  aytBadge: { backgroundColor: palette.accent },
  examRight: { alignItems: 'center', minWidth: 56 },
  trash: { padding: spacing.xs },
});
