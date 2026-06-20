import { Pressable, StyleSheet } from 'react-native';
import * as Haptics from 'expo-haptics';
import { palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';

interface Props {
  label: string;
  emoji?: string;
  selected?: boolean;
  onPress?: () => void;
}

/** Seçilebilir etiket (onboarding, mod seçimi vb.). */
export function Chip({ label, emoji, selected, onPress }: Props) {
  return (
    <Pressable
      onPress={() => {
        Haptics.selectionAsync().catch(() => {});
        onPress?.();
      }}
      style={[styles.chip, selected && styles.selected]}
    >
      <Txt
        variant="small"
        weight={selected ? 'bold' : 'medium'}
        tone={selected ? 'inverse' : 'muted'}
      >
        {emoji ? `${emoji}  ` : ''}
        {label}
      </Txt>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm + 2,
    borderRadius: radius.full,
    backgroundColor: palette.surfaceAlt,
    borderWidth: 1,
    borderColor: palette.border,
  },
  selected: {
    backgroundColor: palette.primary,
    borderColor: palette.primarySoft,
  },
});
