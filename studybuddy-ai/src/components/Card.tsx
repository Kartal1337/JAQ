import { ReactNode } from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { palette, radius, shadow, spacing } from '@/theme/theme';

interface Props {
  children: ReactNode;
  style?: ViewStyle;
  padded?: boolean;
}

/** Yumuşak köşeli, hafif gölgeli yüzey kartı. */
export function Card({ children, style, padded = true }: Props) {
  return (
    <View style={[styles.card, padded && styles.padded, style]}>{children}</View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: palette.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: palette.border,
    ...shadow.card,
  },
  padded: { padding: spacing.lg },
});
