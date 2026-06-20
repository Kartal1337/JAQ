import { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, TextInput, View } from 'react-native';
import Animated, { FadeIn } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { Screen } from '@/components/Screen';
import { Txt } from '@/components/Txt';
import { Button } from '@/components/Button';
import { Chip } from '@/components/Chip';
import { Card } from '@/components/Card';
import { ProgressRing } from '@/components/ProgressRing';
import { useStore, type PomodoroMode } from '@/store/useStore';
import { usePomodoro } from '@/hooks/usePomodoro';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import { formatClock } from '@/lib/date';
import { postSessionCheers } from '@/constants/quotes';

export default function TimerScreen() {
  const settings = useStore((s) => s.settings);
  const completeFocusSession = useStore((s) => s.completeFocusSession);
  const updateSettings = useStore((s) => s.updateSettings);

  const [mode, setMode] = useState<PomodoroMode>(settings.defaultMode);
  const [topic, setTopic] = useState('');
  const [subjectId, setSubjectId] = useState<string | undefined>();
  const [cheer, setCheer] = useState<string | null>(null);

  const handleFocusComplete = useCallback(
    (minutes: number) => {
      const { newAchievements } = completeFocusSession({
        durationMin: minutes,
        topic: topic.trim() || 'Genel çalışma',
        subjectId,
        mode,
      });
      const base = postSessionCheers[Math.floor(Math.random() * postSessionCheers.length)];
      const achText = newAchievements.length
        ? `\n\n🏆 Yeni başarım açıldı!`
        : '';
      setCheer(base + achText);
    },
    [completeFocusSession, topic, subjectId, mode]
  );

  const { phase, running, secondsLeft, progress, start, pause, reset, finish } =
    usePomodoro({
      mode,
      notificationsEnabled: settings.notificationsEnabled,
      onFocusComplete: handleFocusComplete,
    });

  const phaseLabel =
    phase === 'focus' ? tr.timer.focus : mode === '50_10' ? tr.timer.longBreak : tr.timer.shortBreak;
  const ringColor = phase === 'focus' ? undefined : palette.success;

  const selectMode = (m: PomodoroMode) => {
    if (running) return;
    setMode(m);
    updateSettings({ defaultMode: m });
  };

  return (
    <Screen>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: spacing.xxl }}
      >
        <Txt variant="h1" weight="black" style={styles.title}>
          {tr.timer.title}
        </Txt>

        {/* Mod seçimi */}
        <View style={styles.modeRow}>
          <Chip
            label={tr.timer.mode2505}
            selected={mode === '25_5'}
            onPress={() => selectMode('25_5')}
          />
          <Chip
            label={tr.timer.mode5010}
            selected={mode === '50_10'}
            onPress={() => selectMode('50_10')}
          />
        </View>

        {/* Sayaç halkası */}
        <View style={styles.ringWrap}>
          <ProgressRing progress={progress} color={ringColor} size={290} strokeWidth={18}>
            <Txt variant="tiny" weight="bold" tone={phase === 'focus' ? 'primary' : 'success'} style={styles.phaseLabel}>
              {phaseLabel.toUpperCase()}
            </Txt>
            <Txt style={styles.clock}>{formatClock(secondsLeft)}</Txt>
            <Txt variant="small" tone="faint">
              {running ? tr.timer.keepFocus : tr.timer.remaining}
            </Txt>
          </ProgressRing>
        </View>

        {/* Kontroller */}
        <View style={styles.controls}>
          {!running ? (
            <Button
              label={secondsLeft > 0 && progress > 0 ? tr.timer.resume : tr.timer.start}
              icon="play"
              size="lg"
              onPress={start}
              style={{ flex: 1 }}
            />
          ) : (
            <Button
              label={tr.timer.pause}
              icon="pause"
              size="lg"
              variant="solid"
              onPress={pause}
              style={{ flex: 1 }}
            />
          )}
          <Button
            label=""
            icon="stop"
            size="lg"
            variant="danger"
            onPress={finish}
            style={styles.iconBtn}
          />
          <Button
            label=""
            icon="refresh"
            size="lg"
            variant="solid"
            onPress={reset}
            style={styles.iconBtn}
          />
        </View>

        {/* Konu notu */}
        <Card style={styles.topicCard}>
          <Txt variant="small" weight="semibold" tone="muted" style={styles.topicLabel}>
            {tr.timer.topicLabel}
          </Txt>
          <TextInput
            value={topic}
            onChangeText={setTopic}
            placeholder={tr.timer.topicPlaceholder}
            placeholderTextColor={palette.textFaint}
            style={styles.input}
            editable={!running}
          />
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.subjectChips}
          >
            {tr.subjects.map((s) => (
              <Chip
                key={s.id}
                label={s.label}
                emoji={s.emoji}
                selected={subjectId === s.id}
                onPress={() => !running && setSubjectId(subjectId === s.id ? undefined : s.id)}
              />
            ))}
          </ScrollView>
        </Card>
      </ScrollView>

      {/* Seans tamamlandı bildirimi */}
      {cheer && (
        <Animated.View entering={FadeIn} style={styles.cheerOverlay}>
          <Card style={styles.cheerCard}>
            <Txt style={styles.cheerEmoji}>🎉</Txt>
            <Txt variant="h2" weight="black" center>
              {tr.timer.sessionDone}
            </Txt>
            <Txt variant="body" tone="muted" center style={{ marginTop: spacing.sm }}>
              {cheer}
            </Txt>
            <Button
              label={tr.common.ok}
              icon="checkmark"
              onPress={() => setCheer(null)}
              style={{ marginTop: spacing.lg, alignSelf: 'stretch' }}
            />
          </Card>
        </Animated.View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginTop: spacing.sm, marginBottom: spacing.lg },
  modeRow: { flexDirection: 'row', gap: spacing.md, justifyContent: 'center' },
  ringWrap: { alignItems: 'center', marginVertical: spacing.xl },
  phaseLabel: { letterSpacing: 2, marginBottom: spacing.xs },
  clock: { fontSize: 64, fontWeight: '800', color: palette.text, fontVariant: ['tabular-nums'] },
  controls: { flexDirection: 'row', gap: spacing.md, alignItems: 'center' },
  iconBtn: { width: 60, paddingHorizontal: 0 },
  topicCard: { marginTop: spacing.xl },
  topicLabel: { marginBottom: spacing.sm },
  input: {
    backgroundColor: palette.surfaceAlt,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    color: palette.text,
    fontSize: 16,
    borderWidth: 1,
    borderColor: palette.border,
  },
  subjectChips: { gap: spacing.sm, paddingTop: spacing.md, paddingRight: spacing.lg },
  cheerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#000000CC',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xl,
  },
  cheerCard: { alignItems: 'center', width: '100%', maxWidth: 360 },
  cheerEmoji: { fontSize: 56, marginBottom: spacing.sm },
});
