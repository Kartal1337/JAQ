import { useState } from 'react';
import { StyleSheet, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import Animated, { FadeIn, FadeOut, SlideInRight } from 'react-native-reanimated';
import { Ionicons } from '@expo/vector-icons';
import { Screen } from '@/components/Screen';
import { Txt } from '@/components/Txt';
import { Button } from '@/components/Button';
import { Chip } from '@/components/Chip';
import { useStore } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';

export default function Onboarding() {
  const completeOnboarding = useStore((s) => s.completeOnboarding);

  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [levelId, setLevelId] = useState('lise12');
  const [interests, setInterests] = useState<string[]>([]);

  const toggleInterest = (id: string) =>
    setInterests((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  const canNext =
    step === 0 ? name.trim().length > 0 : step === 1 ? !!levelId : interests.length > 0;

  const finish = () => {
    completeOnboarding({ name: name.trim(), levelId, interests });
    router.replace('/(tabs)');
  };

  return (
    <Screen scroll>
      {/* Adım göstergesi */}
      <View style={styles.dots}>
        {[0, 1, 2].map((i) => (
          <View
            key={i}
            style={[styles.dot, i <= step && styles.dotActive]}
          />
        ))}
      </View>

      {step === 0 && (
        <Animated.View entering={FadeIn} exiting={FadeOut} style={styles.stepWrap}>
          <Txt variant="display" style={styles.bigEmoji}>👋</Txt>
          <Txt variant="h1" weight="black">{tr.onboarding.welcomeTitle}</Txt>
          <Txt variant="body" tone="muted" style={styles.subtitle}>
            {tr.onboarding.welcomeSubtitle}
          </Txt>

          <Txt variant="small" weight="semibold" tone="muted" style={styles.label}>
            {tr.onboarding.nameLabel}
          </Txt>
          <TextInput
            value={name}
            onChangeText={setName}
            placeholder={tr.onboarding.namePlaceholder}
            placeholderTextColor={palette.textFaint}
            style={styles.input}
            autoFocus
            returnKeyType="done"
            onSubmitEditing={() => canNext && setStep(1)}
          />
        </Animated.View>
      )}

      {step === 1 && (
        <Animated.View entering={SlideInRight} style={styles.stepWrap}>
          <Txt variant="h1" weight="black">{tr.onboarding.levelLabel}</Txt>
          <Txt variant="body" tone="muted" style={styles.subtitle}>
            Sana uygun içerikleri ayarlayalım.
          </Txt>
          <View style={styles.chips}>
            {tr.levels.map((lv) => (
              <Chip
                key={lv.id}
                label={lv.label}
                selected={levelId === lv.id}
                onPress={() => setLevelId(lv.id)}
              />
            ))}
          </View>
        </Animated.View>
      )}

      {step === 2 && (
        <Animated.View entering={SlideInRight} style={styles.stepWrap}>
          <Txt variant="h1" weight="black">{tr.onboarding.interestsLabel}</Txt>
          <Txt variant="body" tone="muted" style={styles.subtitle}>
            {tr.onboarding.interestsHint}
          </Txt>
          <View style={styles.chips}>
            {tr.subjects.map((sub) => (
              <Chip
                key={sub.id}
                label={sub.label}
                emoji={sub.emoji}
                selected={interests.includes(sub.id)}
                onPress={() => toggleInterest(sub.id)}
              />
            ))}
          </View>
        </Animated.View>
      )}

      <View style={styles.footer}>
        {step > 0 && (
          <Button
            label=""
            icon="chevron-back"
            variant="solid"
            onPress={() => setStep((s) => s - 1)}
            style={styles.backBtn}
          />
        )}
        <Button
          label={step === 2 ? tr.onboarding.start : tr.onboarding.next}
          icon={step === 2 ? 'rocket' : 'arrow-forward'}
          disabled={!canNext}
          onPress={() => (step === 2 ? finish() : setStep((s) => s + 1))}
          style={{ flex: 1 }}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  dots: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.lg, marginBottom: spacing.xl },
  dot: { width: 28, height: 6, borderRadius: 3, backgroundColor: palette.surfaceAlt },
  dotActive: { backgroundColor: palette.primary },
  stepWrap: { gap: spacing.sm, minHeight: 360 },
  bigEmoji: { fontSize: 64, marginBottom: spacing.sm },
  subtitle: { marginBottom: spacing.lg },
  label: { marginTop: spacing.md, marginBottom: spacing.sm, textTransform: 'uppercase', letterSpacing: 1 },
  input: {
    backgroundColor: palette.surface,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    color: palette.text,
    fontSize: 18,
  },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm, marginTop: spacing.md },
  footer: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xxl, alignItems: 'center' },
  backBtn: { width: 56, paddingHorizontal: 0 },
});
