import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, FONT } from '../lib/theme';
import { ramp, riseIn } from '../lib/anim';

// A labeled platform node.
export const PlatformNode: React.FC<{
  label: string;
  x: number;
  y: number;
  startFrame: number;
  tone?: string;
}> = ({ label, x, y, startFrame, tone = C.paper0 }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 16, 12);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, -50%) translateY(${(1 - (s.opacity as number)) * 12}px)`,
        opacity: s.opacity,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 10,
      }}
    >
      <div
        style={{
          width: 116,
          height: 116,
          borderRadius: 26,
          background: tone,
          border: `1px solid ${C.paper200}`,
          boxShadow: '0 6px 18px rgba(60,52,38,0.07)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: FONT.sans,
          fontSize: 22,
          fontWeight: 700,
          color: C.ink700,
        }}
      >
        {label.slice(0, 2)}
      </div>
      <div
        style={{
          fontFamily: FONT.sans,
          fontSize: 19,
          fontWeight: 600,
          color: C.ink700,
        }}
      >
        {label}
      </div>
    </div>
  );
};

// An SVG line connecting two points that "draws" itself over time.
// When `leak` is true it renders a dashed terracotta line (broken link).
export const Link: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  startFrame: number;
  dur?: number;
  leak?: boolean;
  active?: boolean;
}> = ({ x1, y1, x2, y2, startFrame, dur = 20, leak = false, active = false }) => {
  const frame = useCurrentFrame();
  const len = Math.hypot(x2 - x1, y2 - y1);
  const t = ramp(frame, startFrame, dur);
  const color = leak ? C.terra500 : active ? C.sage500 : C.paper300;
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke={color}
      strokeWidth={leak || active ? 3 : 2}
      strokeDasharray={leak ? '2 10' : len}
      strokeDashoffset={leak ? 0 : len * (1 - t)}
      strokeLinecap="round"
      opacity={leak ? t * 0.9 : t}
    />
  );
};

// A coin/money glyph that falls through a gap (the "leaking money" motif).
export const FallingCoin: React.FC<{
  x: number;
  fromY: number;
  startFrame: number;
  delay: number;
}> = ({ x, fromY, startFrame, delay }) => {
  const frame = useCurrentFrame();
  const local = frame - startFrame - delay;
  if (local < 0) return null;
  const fall = ramp(frame, startFrame + delay, 34);
  const y = fromY + fall * 240;
  const opacity = local < 6 ? local / 6 : 1 - ramp(frame, startFrame + delay + 24, 14);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: 'translate(-50%,-50%)',
        opacity,
        width: 34,
        height: 34,
        borderRadius: '50%',
        background: C.terra300,
        border: `2px solid ${C.terra500}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: FONT.mono,
        fontSize: 18,
        fontWeight: 700,
        color: C.terra600,
      }}
    >
      $
    </div>
  );
};
