import { interpolate, spring, Easing } from 'remotion';

// Eased 0->1 over [start, start+dur] frames. Clamped both ends.
export const ramp = (
  frame: number,
  start: number,
  dur: number,
  easing = Easing.out(Easing.cubic)
) =>
  interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing,
  });

// Fade + rise-in transform string for entrances.
export const riseIn = (
  frame: number,
  start: number,
  dur = 18,
  px = 18
) => {
  const t = ramp(frame, start, dur);
  return {
    opacity: t,
    transform: `translateY(${(1 - t) * px}px)`,
  };
};

// Springy pop for emphasis (badges, checkmarks).
export const pop = (frame: number, fps: number, start: number) =>
  spring({
    frame: frame - start,
    fps,
    config: { damping: 14, stiffness: 180, mass: 0.7 },
  });

// Fade a block in then out within a window.
export const fadeWindow = (
  frame: number,
  inAt: number,
  outAt: number,
  inDur = 14,
  outDur = 14
) => {
  const a = ramp(frame, inAt, inDur);
  const b = 1 - ramp(frame, outAt, outDur);
  return Math.min(a, b);
};

export { Easing, interpolate };
