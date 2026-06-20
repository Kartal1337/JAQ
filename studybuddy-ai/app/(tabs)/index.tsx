import { useMemo, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import Animated, { FadeInDown } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { Screen } from '@/components/Screen';
import { Txt } from '@/components/Txt';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { StatTile } from '@/components/StatTile';
import { useStore } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { gradients, palette, radius, spacing } from '@/theme/theme';
import { formatMinutes } from '@/lib/date';
import { todayMinutes, todayPomodoros } from '@/lib/stats';
import { getQuoteOfTheDay } from '@/constants/quotes';
import { suggestStudyPlan } from '@/lib/ai';

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return tr.home.greetingMorning;
  if (h < 18) return tr.home.greetingAfternoon;
  return tr.home.greetingEvening;
}

export default function Home() {
  const profile = useStore((s) => s.profile);
  const settings = useStore((s) => s.settings);
  const streak = useStore((s) => s.streak);
  const sessions = useStore((s) => s.sessions);

  const tMin = useMemo(() => todayMinutes(sessions), [sessions]);
  const tPomo = useMemo(() => todayPomodoros(sessions), [sessions]);
  const quote = useMemo(() => getQuoteOfTheDay(), []);

  const [aiLoading, setAiLoading] = useState(false);
  const [aiPlan, setAiPlan] = useState<string | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  const getSuggestion = async () => {
    if (!settings.apiKey) {
      setAiError(tr.chat.noApiKey);
      return;
    }
    setAiLoading(true);
    setAiError(null);
    setAiPlan(null);
    try {
      const levelLabel =
        tr.levels.find((l) => l.id === profile.levelId)?.label ?? '';
      const interestLabels = profile.interests
        .map((id) => tr.subjects.find((s) => s.id === id)?.label ?? id)
        .filter(Boolean);
      const plan = await suggestStudyPlan({
        provider: settings.provider,
        apiKey: settings.apiKey,
        level: levelLabel,
        interests: interestLabels,
      });
      setAiPlan(plan);
    } catch (e) {
      setAiError(tr.chat.errorGeneric);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <Screen scroll>
      {/* Selamlama */}
      <Animated.View entering={FadeInDown.duration(400)} style={styles.header}>
        <View>
          <Txt variant="small" tone="muted" weight="medium">
            {greeting()},
          </Txt>
          <Txt variant="h1" weight="black">
            {profile.name || 'Öğrenci'} 👋
          </Txt>
        </View>
      </Animated.View>

      {/* Streak banner */}
      <Animated.View entering={FadeInDown.delay(80).duration(400)}>
        <LinearGradient
          colors={gradients.streak}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.streakCard}
        >
          <View style={styles.streakLeft}>
            <Txt variant="tiny" weight="bold" style={styles.streakLabel}>
              {tr.home.streakTitle.toUpperCase()}
            </Txt>
            <View style={styles.streakRow}>
              <Txt variant="display" weight="black" tone="default">
                {streak.current}
              </Txt>
              <Txt variant="h2" weight="bold" style={styles.streakUnit}>
                {tr.home.streakDays}
              </Txt>
            </View>
            <Txt variant="small" weight="medium" style={styles.streakSub}>
              {streak.current > 0
                ? `En uzun seri: ${streak.longest} gün`
                : tr.home.streakZero}
            </Txt>
          </View>
          <Txt style={styles.fire}>🔥</Txt>
        </LinearGradient>
      </Animated.View>

      {/* Bugünkü istatistikler */}
      <Animated.View entering={FadeInDown.delay(140).duration(400)} style={styles.statRow}>
        <StatTile
          icon="time"
          value={formatMinutes(tMin)}
          label={tr.home.todayFocus}
          tint={palette.accent}
        />
        <StatTile
          icon="checkmark-done-circle"
          value={String(tPomo)}
          label={tr.home.pomodorosToday}
          tint={palette.success}
        />
      </Animated.View>

      {/* Hızlı başlat */}
      <Animated.View entering={FadeInDown.delay(200).duration(400)} style={styles.block}>
        <Button
          label={tr.home.quickStart}
          icon="play"
          size="lg"
          onPress={() => router.push('/(tabs)/timer')}
        />
        <Txt variant="tiny" tone="faint" center style={{ marginTop: spacing.sm }}>
          {tr.home.quickStartSub}
        </Txt>
      </Animated.View>

      {/* AI önerisi */}
      <Animated.View entering={FadeInDown.delay(260).duration(400)} style={styles.block}>
        <Card>
          <View style={styles.aiHeader}>
            <View style={styles.aiIcon}>
              <Ionicons name="sparkles" size={20} color={palette.primary} />
            </View>
            <Txt variant="h3" weight="bold">
              {tr.home.aiSuggestTitle}
            </Txt>
          </View>

          {aiPlan ? (
            <Txt variant="body" tone="muted" style={styles.aiText}>
              {aiPlan}
            </Txt>
          ) : aiError ? (
            <Txt variant="small" tone="streak" style={styles.aiText}>
              {aiError}
            </Txt>
          ) : (
            <Txt variant="small" tone="faint" style={styles.aiText}>
              YKS planını AI koçun hazırlasın, sen sadece odaklan. 🎯
            </Txt>
          )}

          <Button
            label={aiLoading ? tr.home.aiSuggestLoading : tr.home.aiSuggestButton}
            icon="bulb"
            variant="solid"
            size="sm"
            loading={aiLoading}
            onPress={getSuggestion}
            style={{ marginTop: spacing.md }}
          />
          {aiError === tr.chat.noApiKey && (
            <Button
              label={tr.chat.goToSettings}
              variant="ghost"
              size="sm"
              onPress={() => router.push('/(tabs)/profile')}
              style={{ marginTop: spacing.sm }}
            />
          )}
        </Card>
      </Animated.View>

      {/* Günün sözü */}
      <Animated.View entering={FadeInDown.delay(320).duration(400)} style={styles.block}>
        <Card style={styles.quoteCard}>
          <Txt style={styles.quoteEmoji}>{quote.emoji}</Txt>
          <Txt variant="tiny" weight="bold" tone="primary" style={styles.quoteLabel}>
            {tr.home.quoteTitle.toUpperCase()}
          </Txt>
          <Txt variant="h3" weight="semibold" style={{ marginTop: 4 }}>
            "{quote.text}"
          </Txt>
        </Card>
      </Animated.View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { marginTop: spacing.sm, marginBottom: spacing.lg },
  streakCard: {
    borderRadius: radius.xl,
    padding: spacing.xl,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    overflow: 'hidden',
  },
  streakLeft: { flex: 1 },
  streakLabel: { color: '#FFFFFFCC', letterSpacing: 1.5 },
  streakRow: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.sm },
  streakUnit: { color: '#FFFFFF', marginBottom: 8 },
  streakSub: { color: '#FFFFFFDD', marginTop: 2 },
  fire: { fontSize: 72 },
  statRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.lg },
  block: { marginTop: spacing.xl },
  aiHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  aiIcon: {
    width: 38,
    height: 38,
    borderRadius: radius.full,
    backgroundColor: palette.primary + '22',
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiText: { lineHeight: 22 },
  quoteCard: { backgroundColor: palette.bgElevated },
  quoteEmoji: { fontSize: 34 },
  quoteLabel: { letterSpacing: 1.5, marginTop: spacing.sm },
});
