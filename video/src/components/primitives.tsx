import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, FONT, SHADOW } from '../lib/theme';
import { riseIn, ramp } from '../lib/anim';

// ---------- Eyebrow (uppercase sage label) ----------
export const Eyebrow: React.FC<{ children: React.ReactNode; color?: string }> = ({
  children,
  color = C.sage600,
}) => (
  <div
    style={{
      fontFamily: FONT.sans,
      fontSize: 20,
      fontWeight: 700,
      letterSpacing: '0.16em',
      textTransform: 'uppercase',
      color,
    }}
  >
    {children}
  </div>
);

// ---------- Pill / chip ----------
export const Chip: React.FC<{
  children: React.ReactNode;
  tone?: 'paper' | 'sage' | 'slate';
  style?: React.CSSProperties;
}> = ({ children, tone = 'paper', style }) => {
  const tones = {
    paper: { bg: C.paper0, bd: C.paper200, fg: C.ink500 },
    sage: { bg: C.sage50, bd: C.sage100, fg: C.sage700 },
    slate: { bg: '#EEF2F6', bd: '#D8E2EC', fg: C.slate700 },
  }[tone];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10,
        fontFamily: FONT.sans,
        fontSize: 19,
        fontWeight: 600,
        color: tones.fg,
        background: tones.bg,
        border: `1px solid ${tones.bd}`,
        borderRadius: 999,
        padding: '9px 18px',
        ...style,
      }}
    >
      {children}
    </span>
  );
};

// ---------- A small dot ----------
export const Dot: React.FC<{ color?: string; size?: number }> = ({
  color = C.sage500,
  size = 9,
}) => (
  <span
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: color,
      display: 'inline-block',
      flex: 'none',
    }}
  />
);

// ---------- Trace chip (agent observability step) ----------
export const TraceChip: React.FC<{
  label: string;
  index: number;
  startFrame: number;
}> = ({ label, index, startFrame }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame + index * 7, 14, 10);
  return (
    <span
      style={{
        ...s,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 9,
        fontFamily: FONT.sans,
        fontSize: 18,
        fontWeight: 600,
        color: C.ink500,
        background: C.paper0,
        border: `1px solid ${C.paper200}`,
        borderRadius: 999,
        padding: '8px 16px',
      }}
    >
      <Dot color={C.sage400} size={7} />
      {label}
    </span>
  );
};

// ---------- Route card (chat -> deep view bridge) ----------
export const RouteCard: React.FC<{
  title: string;
  sub: string;
  startFrame: number;
}> = ({ title, sub, startFrame }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 18, 16);
  return (
    <div
      style={{
        ...s,
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        width: 560,
        background: C.sage50,
        border: `1px solid ${C.sage100}`,
        borderRadius: 18,
        padding: '18px 22px',
      }}
    >
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 12,
          background: C.sage100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flex: 'none',
        }}
      >
        <ArrowRight color={C.sage600} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontFamily: FONT.sans,
            fontSize: 21,
            fontWeight: 700,
            color: C.sage700,
          }}
        >
          {title}
        </div>
        <div
          style={{
            fontFamily: FONT.sans,
            fontSize: 17,
            color: C.ink500,
            marginTop: 3,
          }}
        >
          {sub}
        </div>
      </div>
    </div>
  );
};

// ---------- Count-up monospace figure ----------
export const CountUp: React.FC<{
  to: number;
  startFrame: number;
  dur?: number;
  prefix?: string;
  size?: number;
  color?: string;
}> = ({ to, startFrame, dur = 36, prefix = '$', size = 96, color = C.sage600 }) => {
  const frame = useCurrentFrame();
  const t = ramp(frame, startFrame, dur);
  const val = Math.round(to * t);
  return (
    <span
      style={{
        fontFamily: FONT.mono,
        fontVariantNumeric: 'tabular-nums',
        fontWeight: 500,
        fontSize: size,
        letterSpacing: '-0.02em',
        color,
        lineHeight: 1,
      }}
    >
      {prefix}
      {val.toLocaleString('en-US')}
    </span>
  );
};

// ---------- Inline icons (stroke, on-brand) ----------
export const ArrowRight: React.FC<{ color?: string; size?: number }> = ({
  color = C.ink700,
  size = 22,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M5 12h14M13 6l6 6-6 6"
      stroke={color}
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const Check: React.FC<{ color?: string; size?: number }> = ({
  color = C.sage600,
  size = 22,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M5 13l4 4L19 7"
      stroke={color}
      strokeWidth={2.4}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const Spark: React.FC<{ color?: string; size?: number }> = ({
  color = C.sage500,
  size = 22,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <path
      d="M12 3v18M3 12h18M6 6l12 12M18 6L6 18"
      stroke={color}
      strokeWidth={1.6}
      strokeLinecap="round"
      opacity={0.9}
    />
  </svg>
);
