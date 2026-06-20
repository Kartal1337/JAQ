/**
 * StudyBuddy AI tasarım sistemi (design tokens).
 * Tek kaynak: renkler, boşluklar, köşe yarıçapları, tipografi.
 * Varsayılan tema koyu (dark) moddur.
 */

export const palette = {
  // Mor-mavi marka tonları
  primary: '#7C5CFF',
  primaryDark: '#5B3FE0',
  primarySoft: '#9C84FF',
  accent: '#3DD6F5',
  accentSoft: '#6FE3FA',

  // Durum renkleri
  success: '#34D399',
  warning: '#FBBF24',
  danger: '#FB7185',
  streak: '#FF8A3D', // ateş turuncusu

  // Koyu yüzeyler
  bg: '#0B0B1A',
  bgElevated: '#13132B',
  surface: '#1A1A33',
  surfaceAlt: '#222244',
  border: '#2A2A4A',

  // Metin
  text: '#F5F5FF',
  textMuted: '#A9A9C9',
  textFaint: '#6E6E92',

  white: '#FFFFFF',
  black: '#000000',
} as const;

export const gradients = {
  brand: ['#7C5CFF', '#3DD6F5'] as const,
  brandVertical: ['#5B3FE0', '#7C5CFF'] as const,
  streak: ['#FF8A3D', '#FF5C7C'] as const,
  success: ['#34D399', '#3DD6F5'] as const,
  card: ['#1A1A33', '#13132B'] as const,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

export const radius = {
  sm: 10,
  md: 16,
  lg: 22,
  xl: 28,
  full: 999,
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  md: 16,
  lg: 18,
  xl: 22,
  xxl: 28,
  xxxl: 38,
  display: 54,
} as const;

export const shadow = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 14,
    elevation: 6,
  },
  glow: {
    shadowColor: palette.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 18,
    elevation: 10,
  },
};

export const theme = {
  palette,
  gradients,
  spacing,
  radius,
  fontSize,
  shadow,
};

export type Theme = typeof theme;
