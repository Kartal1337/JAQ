import { useState } from 'react';
import { Alert, StyleSheet, Switch, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';
import { Screen } from '@/components/Screen';
import { Txt } from '@/components/Txt';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { Chip } from '@/components/Chip';
import { StatTile } from '@/components/StatTile';
import { useStore, type AIProvider } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import { formatMinutes } from '@/lib/date';
import { totalMinutes } from '@/lib/stats';
import { ACHIEVEMENTS } from '@/lib/achievements';
import { getCountdown, upcomingYksYears } from '@/lib/countdown';

const PROVIDERS: { id: AIProvider; label: string }[] = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'grok', label: 'Grok (xAI)' },
  { id: 'claude', label: 'Claude' },
];

export default function Profile() {
  const profile = useStore((s) => s.profile);
  const settings = useStore((s) => s.settings);
  const streak = useStore((s) => s.streak);
  const sessions = useStore((s) => s.sessions);
  const unlocked = useStore((s) => s.achievements);
  const updateProfile = useStore((s) => s.updateProfile);
  const updateSettings = useStore((s) => s.updateSettings);
  const resetAll = useStore((s) => s.resetAll);

  const [name, setName] = useState(profile.name);
  const [apiKey, setApiKey] = useState(settings.apiKey);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  const total = totalMinutes(sessions);
  const examOptions = upcomingYksYears(3);
  const examLeft = profile.examDate ? getCountdown(profile.examDate).days : null;

  const setExamYear = (year: number) => {
    const opt = examOptions.find((e) => e.year === year);
    if (!opt) return;
    Haptics.selectionAsync().catch(() => {});
    updateProfile({ examDate: opt.dateKey, examLabel: opt.label });
  };

  const save = () => {
    updateProfile({ name: name.trim() || profile.name });
    updateSettings({ apiKey: apiKey.trim() });
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const confirmReset = () => {
    Alert.alert(tr.profile.resetData, tr.profile.resetConfirm, [
      { text: tr.profile.cancel, style: 'cancel' },
      {
        text: tr.profile.delete,
        style: 'destructive',
        onPress: () => {
          resetAll();
          router.replace('/onboarding');
        },
      },
    ]);
  };

  return (
    <Screen scroll>
      {/* Profil başlığı */}
      <View style={styles.profileHeader}>
        <View style={styles.bigAvatar}>
          <Txt style={{ fontSize: 36 }}>🎓</Txt>
        </View>
        <Txt variant="h1" weight="black">
          {profile.name || 'Öğrenci'}
        </Txt>
        <Txt variant="small" tone="muted">
          {tr.levels.find((l) => l.id === profile.levelId)?.label ?? ''}
        </Txt>
      </View>

      {/* İstatistikler */}
      <View style={styles.statRow}>
        <StatTile icon="flame" value={`${streak.current}`} label={tr.profile.streak} tint={palette.streak} />
        <StatTile icon="time" value={formatMinutes(total)} label={tr.profile.totalHours} tint={palette.accent} />
        <StatTile icon="checkmark-done" value={`${sessions.length}`} label={tr.profile.totalSessions} tint={palette.success} />
      </View>

      {/* Başarımlar */}
      <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
        {tr.profile.achievements}
      </Txt>
      <View style={styles.achGrid}>
        {ACHIEVEMENTS.map((a) => {
          const isOpen = unlocked.includes(a.id);
          return (
            <View key={a.id} style={[styles.achCard, !isOpen && styles.achLocked]}>
              <Txt style={[styles.achEmoji, !isOpen && styles.achEmojiLocked]}>
                {isOpen ? a.emoji : '🔒'}
              </Txt>
              <Txt variant="tiny" weight="bold" center numberOfLines={1}>
                {a.title}
              </Txt>
              <Txt variant="tiny" tone="faint" center numberOfLines={2} style={{ marginTop: 2 }}>
                {a.desc}
              </Txt>
            </View>
          );
        })}
      </View>

      {/* Ayarlar */}
      <Txt variant="h3" weight="bold" style={styles.sectionTitle}>
        {tr.profile.settings}
      </Txt>

      <Card style={styles.settingsCard}>
        {/* Ad düzenle */}
        <Txt variant="small" weight="semibold" tone="muted" style={styles.fieldLabel}>
          {tr.profile.editName}
        </Txt>
        <TextInput
          value={name}
          onChangeText={setName}
          placeholder={tr.onboarding.namePlaceholder}
          placeholderTextColor={palette.textFaint}
          style={styles.input}
        />

        {/* Hedef YKS */}
        <Txt variant="small" weight="semibold" tone="muted" style={styles.fieldLabel}>
          {tr.profile.examTarget}
          {examLeft != null ? `  ·  ${examLeft} ${tr.countdown.days}` : ''}
        </Txt>
        <View style={styles.providerRow}>
          {examOptions.map((opt) => (
            <Chip
              key={opt.year}
              label={opt.label}
              selected={profile.examLabel === opt.label}
              onPress={() => setExamYear(opt.year)}
            />
          ))}
        </View>

        {/* AI sağlayıcı */}
        <Txt variant="small" weight="semibold" tone="muted" style={styles.fieldLabel}>
          {tr.profile.apiProvider}
        </Txt>
        <View style={styles.providerRow}>
          {PROVIDERS.map((p) => (
            <Chip
              key={p.id}
              label={p.label}
              selected={settings.provider === p.id}
              onPress={() => updateSettings({ provider: p.id })}
            />
          ))}
        </View>

        {/* API anahtarı */}
        <Txt variant="small" weight="semibold" tone="muted" style={styles.fieldLabel}>
          {tr.profile.apiKey}
        </Txt>
        <View style={styles.keyRow}>
          <TextInput
            value={apiKey}
            onChangeText={setApiKey}
            placeholder={tr.profile.apiKeyPlaceholder}
            placeholderTextColor={palette.textFaint}
            style={[styles.input, { flex: 1, marginBottom: 0 }]}
            secureTextEntry={!showKey}
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Ionicons
            name={showKey ? 'eye-off' : 'eye'}
            size={22}
            color={palette.textMuted}
            style={styles.eye}
            onPress={() => setShowKey((v) => !v)}
          />
        </View>
        <Txt variant="tiny" tone="faint" style={{ marginTop: spacing.sm }}>
          {tr.profile.apiKeyHelp}
        </Txt>

        {/* Bildirim & ses */}
        <View style={styles.toggleRow}>
          <View style={{ flex: 1 }}>
            <Txt variant="body" weight="semibold">
              {tr.profile.notifications}
            </Txt>
            <Txt variant="tiny" tone="faint">
              {tr.profile.notificationsSub}
            </Txt>
          </View>
          <Switch
            value={settings.notificationsEnabled}
            onValueChange={(v) => updateSettings({ notificationsEnabled: v })}
            trackColor={{ true: palette.primary, false: palette.surfaceAlt }}
            thumbColor={palette.white}
          />
        </View>

        <View style={styles.toggleRow}>
          <Txt variant="body" weight="semibold">
            {tr.profile.sound}
          </Txt>
          <Switch
            value={settings.soundEnabled}
            onValueChange={(v) => updateSettings({ soundEnabled: v })}
            trackColor={{ true: palette.primary, false: palette.surfaceAlt }}
            thumbColor={palette.white}
          />
        </View>

        <Button
          label={saved ? tr.profile.apiKeySaved : tr.profile.save}
          icon={saved ? 'checkmark-circle' : 'save'}
          onPress={save}
          style={{ marginTop: spacing.lg }}
        />
      </Card>

      {/* Tehlikeli bölge */}
      <Button
        label={tr.profile.resetData}
        icon="trash"
        variant="ghost"
        onPress={confirmReset}
        style={styles.resetBtn}
      />

      <Txt variant="tiny" tone="faint" center style={styles.footer}>
        {tr.appName} · {tr.profile.version} 1.0.0{'\n'}
        {tr.profile.madeWith}
      </Txt>
    </Screen>
  );
}

const styles = StyleSheet.create({
  profileHeader: { alignItems: 'center', marginTop: spacing.lg, marginBottom: spacing.xl, gap: 4 },
  bigAvatar: {
    width: 84,
    height: 84,
    borderRadius: radius.full,
    backgroundColor: palette.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: palette.primary,
    marginBottom: spacing.sm,
  },
  statRow: { flexDirection: 'row', gap: spacing.sm },
  sectionTitle: { marginTop: spacing.xl, marginBottom: spacing.md },
  achGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  achCard: {
    width: '31%',
    backgroundColor: palette.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: palette.border,
    padding: spacing.md,
    alignItems: 'center',
    minHeight: 110,
  },
  achLocked: { opacity: 0.55 },
  achEmoji: { fontSize: 30, marginBottom: spacing.sm },
  achEmojiLocked: { fontSize: 26 },
  settingsCard: { gap: 0 },
  fieldLabel: { marginBottom: spacing.sm, marginTop: spacing.md, textTransform: 'uppercase', letterSpacing: 0.5 },
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
  providerRow: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  keyRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  eye: { padding: spacing.sm },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
  },
  resetBtn: { marginTop: spacing.xl, borderColor: palette.danger },
  footer: { marginTop: spacing.xl, lineHeight: 18 },
});
