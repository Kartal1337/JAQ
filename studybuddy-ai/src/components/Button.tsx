import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { gradients, palette, radius, spacing } from '@/theme/theme';
import { Txt } from './Txt';

type Variant = 'primary' | 'solid' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface Props {
  label: string;
  onPress: () => void;
  variant?: Variant;
  size?: Size;
  icon?: keyof typeof Ionicons.glyphMap;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  haptic?: boolean;
}

const heights: Record<Size, number> = { sm: 40, md: 50, lg: 60 };

export function Button({
  label,
  onPress,
  variant = 'primary',
  size = 'md',
  icon,
  loading,
  disabled,
  style,
  haptic = true,
}: Props) {
  const isDisabled = disabled || loading;
  const height = heights[size];

  const handlePress = () => {
    if (isDisabled) return;
    if (haptic) Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    onPress();
  };

  const content = (
    <View style={styles.row}>
      {loading ? (
        <ActivityIndicator color={variant === 'ghost' ? palette.primary : palette.white} />
      ) : (
        <>
          {icon && (
            <Ionicons
              name={icon}
              size={size === 'lg' ? 22 : 18}
              color={variant === 'ghost' ? palette.primary : palette.white}
              style={{ marginRight: spacing.sm }}
            />
          )}
          <Txt
            variant={size === 'lg' ? 'h3' : 'body'}
            weight="bold"
            tone={variant === 'ghost' ? 'primary' : 'default'}
          >
            {label}
          </Txt>
        </>
      )}
    </View>
  );

  if (variant === 'primary') {
    return (
      <Pressable onPress={handlePress} disabled={isDisabled} style={[isDisabled && styles.dim, style]}>
        <LinearGradient
          colors={gradients.brand}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.base, { height }]}
        >
          {content}
        </LinearGradient>
      </Pressable>
    );
  }

  const bg =
    variant === 'solid'
      ? palette.surfaceAlt
      : variant === 'danger'
      ? palette.danger
      : 'transparent';

  return (
    <Pressable
      onPress={handlePress}
      disabled={isDisabled}
      style={[
        styles.base,
        { height, backgroundColor: bg },
        variant === 'ghost' && styles.ghostBorder,
        isDisabled && styles.dim,
        style,
      ]}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radius.full,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xl,
  },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  ghostBorder: { borderWidth: 1.5, borderColor: palette.primary },
  dim: { opacity: 0.5 },
});
