import { Text, TextProps, StyleSheet } from 'react-native';
import { palette, fontSize } from '@/theme/theme';

type Variant = 'display' | 'h1' | 'h2' | 'h3' | 'body' | 'small' | 'tiny';
type Tone = 'default' | 'muted' | 'faint' | 'primary' | 'accent' | 'success' | 'streak' | 'inverse';

interface Props extends TextProps {
  variant?: Variant;
  tone?: Tone;
  weight?: 'regular' | 'medium' | 'semibold' | 'bold' | 'black';
  center?: boolean;
}

const variantStyle: Record<Variant, { fontSize: number; lineHeight: number }> = {
  display: { fontSize: fontSize.display, lineHeight: fontSize.display + 4 },
  h1: { fontSize: fontSize.xxl, lineHeight: fontSize.xxl + 6 },
  h2: { fontSize: fontSize.xl, lineHeight: fontSize.xl + 6 },
  h3: { fontSize: fontSize.lg, lineHeight: fontSize.lg + 6 },
  body: { fontSize: fontSize.md, lineHeight: fontSize.md + 8 },
  small: { fontSize: fontSize.sm, lineHeight: fontSize.sm + 6 },
  tiny: { fontSize: fontSize.xs, lineHeight: fontSize.xs + 4 },
};

const toneColor: Record<Tone, string> = {
  default: palette.text,
  muted: palette.textMuted,
  faint: palette.textFaint,
  primary: palette.primary,
  accent: palette.accent,
  success: palette.success,
  streak: palette.streak,
  inverse: palette.bg,
};

const weightMap = {
  regular: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  black: '800',
} as const;

/** Tek tipte, temaya bağlı metin bileşeni. */
export function Txt({
  variant = 'body',
  tone = 'default',
  weight = 'regular',
  center,
  style,
  ...rest
}: Props) {
  return (
    <Text
      {...rest}
      style={[
        variantStyle[variant],
        { color: toneColor[tone], fontWeight: weightMap[weight] },
        center && styles.center,
        style,
      ]}
    />
  );
}

const styles = StyleSheet.create({
  center: { textAlign: 'center' },
});
