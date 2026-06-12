import React from 'react';
import { useCurrentFrame } from 'remotion';
import { C, FONT } from '../lib/theme';
import { riseIn } from '../lib/anim';

// Lode mark (small sage orb with ring)
export const LodeMark: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: '50%',
      background: `radial-gradient(circle at 35% 30%, ${C.sage300}, ${C.sage500})`,
      boxShadow: `0 0 0 4px ${C.sage50}`,
      flex: 'none',
    }}
  />
);

// User message bubble (slate)
export const UserBubble: React.FC<{
  children: React.ReactNode;
  startFrame: number;
}> = ({ children, startFrame }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 16, 14);
  return (
    <div style={{ ...s, alignSelf: 'flex-end', maxWidth: 720 }}>
      <div
        style={{
          background: C.slate500,
          borderRadius: '18px 18px 6px 18px',
          padding: '16px 22px',
          fontFamily: FONT.sans,
          fontSize: 25,
          lineHeight: 1.45,
          color: '#fff',
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Lode answer (serif italic voice). `em` words can be sage-highlighted by
// passing <em>...</em> in children.
export const LodeAnswer: React.FC<{
  children: React.ReactNode;
  startFrame: number;
}> = ({ children, startFrame }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 18, 16);
  return (
    <div style={{ ...s, display: 'flex', gap: 18, alignItems: 'flex-start', maxWidth: 980 }}>
      <div style={{ marginTop: 6 }}>
        <LodeMark size={38} />
      </div>
      <p
        style={{
          margin: 0,
          fontFamily: FONT.serif,
          fontSize: 30,
          fontStyle: 'italic',
          lineHeight: 1.5,
          color: C.ink900,
        }}
      >
        {children}
      </p>
    </div>
  );
};

// Tier caption under an answer (which compute tier served it)
export const TierTag: React.FC<{
  tier: 'fast' | 'reasoning';
  startFrame: number;
}> = ({ tier, startFrame }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 14, 8);
  const label =
    tier === 'fast'
      ? 'Quick lookup · Gemini 2.5 Flash'
      : 'Deep reasoning · Gemini 2.5 Pro';
  return (
    <div
      style={{
        ...s,
        display: 'inline-flex',
        alignItems: 'center',
        gap: 9,
        fontFamily: FONT.mono,
        fontSize: 17,
        color: C.inkMuted,
        marginLeft: 56,
      }}
    >
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: tier === 'fast' ? C.amber500 : C.sage500,
        }}
      />
      {label}
    </div>
  );
};
