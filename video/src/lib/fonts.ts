import { loadFont as loadHanken } from '@remotion/google-fonts/HankenGrotesk';
import { loadFont as loadNewsreader } from '@remotion/google-fonts/Newsreader';
import { loadFont as loadSpline } from '@remotion/google-fonts/SplineSansMono';

// Load only the weights/styles actually used, latin subset, to avoid the
// "too many network requests" slowdown during render.
export const hanken = loadHanken('normal', {
  weights: ['400', '500', '600', '700'],
  subsets: ['latin'],
});

export const newsreader = loadNewsreader('normal', {
  weights: ['400'],
  subsets: ['latin'],
});
export const newsreaderItalic = loadNewsreader('italic', {
  weights: ['400'],
  subsets: ['latin'],
});

export const spline = loadSpline('normal', {
  weights: ['500'],
  subsets: ['latin'],
});
