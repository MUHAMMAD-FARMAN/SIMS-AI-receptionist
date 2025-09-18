// Professional color palette inspired by Next.js
export const colors = {
  // Main colors
  background: '#000000',        // Pure black
  surface: '#111111',          // Dark gray surface
  card: '#1a1a1a',            // Card background
  border: '#333333',          // Border color
  shadow: '#000000',          // Shadow color
  
  // Text colors
  text: {
    primary: '#ffffff',       // Primary text (white)
    secondary: '#a1a1aa',     // Secondary text (gray)
    muted: '#71717a',         // Muted text (darker gray)
  },
  
  // Accent colors
  accent: '#ffffff',          // Primary accent (white)
  accentMuted: '#f4f4f5',     // Muted accent
  
  // Status colors
  success: '#10b981',         // Green
  error: '#ef4444',           // Red
  warning: '#f59e0b',         // Orange
  
  // Interactive states
  hover: '#262626',           // Hover state
  pressed: '#404040',         // Pressed state
  
  // Gradients
  gradient: {
    dark: ['#000000', '#111111', '#1a1a1a'],
    subtle: ['#111111', '#1a1a1a'],
  }
};

// Typography
export const typography = {
  // Font sizes
  sizes: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 30,
  },
  
  // Font weights
  weights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  }
};

// Spacing
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  '2xl': 48,
  '3xl': 64,
};

// Border radius
export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};