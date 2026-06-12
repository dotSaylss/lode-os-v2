// LodeOS brand tokens, lifted from frontend/src/app.css so the video
// matches the real product. Warm paper canvas, sage accent, warm ink.

export const C = {
  // canvas / paper
  paper0: '#FFFFFF',
  paper50: '#FAF8F2', // main canvas
  paper100: '#F2EEE4',
  paper200: '#E8E2D4', // hairline
  paper300: '#D9D1BF',

  // ink (warm near-black text)
  ink900: '#23241F',
  ink700: '#45473E',
  ink500: '#6C6F62',
  inkMuted: '#8E9183',

  // sage accent
  sage50: '#EDF3EE',
  sage100: '#DCE7DF',
  sage200: '#BFD4C6',
  sage300: '#9ABBA4',
  sage400: '#739B80',
  sage500: '#577D63', // primary accent
  sage600: '#456450',
  sage700: '#374F40',

  // slate (user voice)
  slate300: '#A7BFD1',
  slate500: '#5C7E9A',
  slate700: '#374F63',
  slate900: '#1E2B36',

  // terracotta (warm secondary, used for "leaking money")
  terra300: '#D6B3A3',
  terra500: '#B07762',
  terra600: '#97604C',
  clay500: '#B5654F',

  amber500: '#BE8B4E',
  white: '#FFFFFF',
};

export const FONT = {
  sans: "'Hanken Grotesk', ui-sans-serif, system-ui, sans-serif",
  serif: "'Newsreader', ui-serif, Georgia, serif",
  mono: "'Spline Sans Mono', ui-monospace, Menlo, monospace",
};

export const SHADOW = {
  sm: '0 1px 3px rgba(60,52,38,0.06), 0 1px 2px rgba(60,52,38,0.04)',
  md: '0 6px 18px rgba(60,52,38,0.07), 0 2px 6px rgba(60,52,38,0.04)',
  lg: '0 16px 40px rgba(60,52,38,0.12), 0 4px 12px rgba(60,52,38,0.06)',
  xl: '0 28px 64px rgba(45,38,28,0.18), 0 8px 20px rgba(45,38,28,0.08)',
};

export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
};
