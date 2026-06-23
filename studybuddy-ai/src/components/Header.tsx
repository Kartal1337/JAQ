import { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';

interface Props {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  right?: ReactNode;
}

/** Stack ekranları için geri tuşlu başlık. */
export function Header({ title, subtitle, onBack, right }: Props) {
  return (
    <View style={styles.row}>
      <Pressable
        style={styles.iconBtn}
        onPress={onBack ?? (() => router.back())}
        hitSlop={8}
      >
        <Ionicons name="chevron-back" size={24} color={palette.text} />
      </Pressable>
      <View style={styles.titleWrap}>
        <Txt variant="h3" weight="bold" numberOfLines={1}>
          {title}
        </Txt>
        {subtitle ? (
          <Txt variant="tiny" tone="muted" numberOfLines={1}>
            {subtitle}
          </Txt>
        ) : null}
      </View>
      <View style={styles.right}>{right}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    gap: spacing.sm,
  },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: radius.full,
    backgroundColor: palette.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: palette.border,
  },
  titleWrap: { flex: 1 },
  right: { minWidth: 40, alignItems: 'flex-end' },
});
