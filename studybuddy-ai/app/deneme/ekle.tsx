import { useMemo, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Haptics from 'expo-haptics';
import { Txt } from '@/components/Txt';
import { Card } from '@/components/Card';
import { Button } from '@/components/Button';
import { Chip } from '@/components/Chip';
import { Header } from '@/components/Header';
import { useStore, type SubjectResult } from '@/store/useStore';
import { tr } from '@/locale/tr';
import { palette, radius, spacing } from '@/theme/theme';
import {
  AYT_FIELDS,
  calcNet,
  formatNet,
  getSections,
  type ExamKind,
} from '@/constants/yks';

type Draft = Record<string, { correct: string; wrong: string }>;

const clampInt = (v: string) => v.replace(/[^0-9]/g, '');

export default function DenemeEkle() {
  const addMockExam = useStore((s) => s.addMockExam);

  const [kind, setKind] = useState<ExamKind>('TYT');
  const [fieldId, setFieldId] = useState(AYT_FIELDS[0].id);
  const [name, setName] = useState('');
  const [draft, setDraft] = useState<Draft>({});

  const sections = useMemo(() => getSections(kind, fieldId), [kind, fieldId]);

  const get = (key: string) => draft[key] ?? { correct: '', wrong: '' };

  const setField = (key: string, field: 'correct' | 'wrong', value: string) =>
    setDraft((d) => ({ ...d, [key]: { ...get(key), [field]: clampInt(value) } }));

  // Anlık net hesapları
  const perNet = (key: string) => {
    const r = get(key);
    return calcNet(Number(r.correct) || 0, Number(r.wrong) || 0);
  };
  const totalNet = useMemo(
    () => sections.reduce((sum, s) => sum + perNet(s.key), 0),
    [sections, draft]
  );

  const overflowSection = sections.find((s) => {
    const r = get(s.key);
    return (Number(r.correct) || 0) + (Number(r.wrong) || 0) > s.max;
  });
  const hasAny = sections.some((s) => {
    const r = get(s.key);
    return (Number(r.correct) || 0) + (Number(r.wrong) || 0) > 0;
  });

  const save = () => {
    if (overflowSection || !hasAny) return;
    const results: Record<string, SubjectResult> = {};
    for (const s of sections) {
      const r = get(s.key);
      const correct = Number(r.correct) || 0;
      const wrong = Number(r.wrong) || 0;
      if (correct + wrong === 0) continue;
      results[s.key] = { correct, wrong };
    }
    addMockExam({
      kind,
      fieldId: kind === 'AYT' ? fieldId : undefined,
      name: name.trim(),
      results,
      totalNet: Math.round(totalNet * 100) / 100,
    });
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    router.back();
  };

  const switchKind = (k: ExamKind) => {
    setKind(k);
    setDraft({}); // bölümler değişti, girişleri temizle
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.padded}>
        <Header title={tr.deneme.formTitle} />
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Sınav türü */}
          <Txt variant="small" weight="semibold" tone="muted" style={styles.label}>
            {tr.deneme.kindLabel}
          </Txt>
          <View style={styles.chipRow}>
            <Chip label="TYT" selected={kind === 'TYT'} onPress={() => switchKind('TYT')} />
            <Chip label="AYT" selected={kind === 'AYT'} onPress={() => switchKind('AYT')} />
          </View>

          {/* AYT alanı */}
          {kind === 'AYT' && (
            <>
              <Txt variant="small" weight="semibold" tone="muted" style={styles.label}>
                {tr.deneme.fieldLabel}
              </Txt>
              <View style={styles.chipRow}>
                {AYT_FIELDS.map((f) => (
                  <Chip
                    key={f.id}
                    label={f.label}
                    selected={fieldId === f.id}
                    onPress={() => {
                      setFieldId(f.id);
                      setDraft({});
                    }}
                  />
                ))}
              </View>
            </>
          )}

          {/* Ad */}
          <Txt variant="small" weight="semibold" tone="muted" style={styles.label}>
            {tr.deneme.nameLabel}
          </Txt>
          <TextInput
            value={name}
            onChangeText={setName}
            placeholder={tr.deneme.namePlaceholder}
            placeholderTextColor={palette.textFaint}
            style={styles.nameInput}
          />

          {/* Ders satırları */}
          <Card style={styles.tableCard}>
            <View style={styles.theadRow}>
              <Txt variant="tiny" tone="faint" weight="bold" style={{ flex: 1 }}>
                DERS
              </Txt>
              <Txt variant="tiny" tone="faint" weight="bold" style={styles.colHead}>
                {tr.deneme.correct.toUpperCase()}
              </Txt>
              <Txt variant="tiny" tone="faint" weight="bold" style={styles.colHead}>
                {tr.deneme.wrong.toUpperCase()}
              </Txt>
              <Txt variant="tiny" tone="faint" weight="bold" style={styles.netHead}>
                NET
              </Txt>
            </View>

            {sections.map((s, i) => {
              const r = get(s.key);
              const over = (Number(r.correct) || 0) + (Number(r.wrong) || 0) > s.max;
              return (
                <View key={s.key} style={[styles.row, i > 0 && styles.divider]}>
                  <View style={{ flex: 1 }}>
                    <Txt variant="small" weight="semibold" numberOfLines={1}>
                      {s.label}
                    </Txt>
                    <Txt variant="tiny" tone="faint">
                      {s.max} soru
                    </Txt>
                  </View>
                  <TextInput
                    value={r.correct}
                    onChangeText={(v) => setField(s.key, 'correct', v)}
                    keyboardType="number-pad"
                    placeholder="0"
                    placeholderTextColor={palette.textFaint}
                    style={[styles.cell, over && styles.cellError]}
                    maxLength={2}
                  />
                  <TextInput
                    value={r.wrong}
                    onChangeText={(v) => setField(s.key, 'wrong', v)}
                    keyboardType="number-pad"
                    placeholder="0"
                    placeholderTextColor={palette.textFaint}
                    style={[styles.cell, over && styles.cellError]}
                    maxLength={2}
                  />
                  <Txt variant="small" weight="bold" tone="primary" style={styles.netCell}>
                    {formatNet(perNet(s.key))}
                  </Txt>
                </View>
              );
            })}
          </Card>

          {/* Toplam net */}
          <View style={styles.totalRow}>
            <Txt variant="h3" weight="semibold" tone="muted">
              {tr.deneme.totalNet}
            </Txt>
            <Txt variant="display" weight="black" tone="primary">
              {formatNet(Math.round(totalNet * 100) / 100)}
            </Txt>
          </View>

          {overflowSection && (
            <Txt variant="small" tone="streak" center style={{ marginBottom: spacing.md }}>
              ⚠️ {tr.deneme.invalid}
            </Txt>
          )}

          <Button
            label={tr.deneme.save}
            icon="save"
            onPress={save}
            disabled={!!overflowSection || !hasAny}
          />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: palette.bg },
  flex: { flex: 1 },
  padded: { paddingHorizontal: spacing.lg },
  content: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxxl },
  label: { marginTop: spacing.lg, marginBottom: spacing.sm, textTransform: 'uppercase', letterSpacing: 0.5 },
  chipRow: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  nameInput: {
    backgroundColor: palette.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.md,
    color: palette.text,
    fontSize: 16,
    borderWidth: 1,
    borderColor: palette.border,
  },
  tableCard: { marginTop: spacing.lg, paddingVertical: spacing.sm },
  theadRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingBottom: spacing.sm,
    paddingHorizontal: spacing.xs,
  },
  colHead: { width: 54, textAlign: 'center' },
  netHead: { width: 44, textAlign: 'right' },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, paddingHorizontal: spacing.xs, gap: spacing.xs },
  divider: { borderTopWidth: 1, borderTopColor: palette.border },
  cell: {
    width: 54,
    height: 42,
    textAlign: 'center',
    backgroundColor: palette.surfaceAlt,
    borderRadius: radius.sm,
    color: palette.text,
    fontSize: 16,
    fontWeight: '600',
    borderWidth: 1,
    borderColor: palette.border,
  },
  cellError: { borderColor: palette.danger },
  netCell: { width: 44, textAlign: 'right' },
  totalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.xl,
    marginBottom: spacing.lg,
  },
});
