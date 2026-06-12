import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C, FONT } from '../lib/theme';

// Full-frame warm paper canvas with a soft sage vignette. Every scene sits
// inside one of these so the whole film reads as one product surface.
export const Stage: React.FC<{
  children: React.ReactNode;
  pad?: number;
  align?: 'center' | 'flex-start';
  justify?: 'center' | 'flex-start';
}> = ({ children, pad = 120, align = 'flex-start', justify = 'center' }) => (
  <AbsoluteFill style={{ background: C.paper50, fontFamily: FONT.sans }}>
    {/* soft radial warmth, top-left */}
    <AbsoluteFill
      style={{
        background: `radial-gradient(1200px 800px at 18% 12%, ${C.sage50} 0%, rgba(0,0,0,0) 60%)`,
      }}
    />
    {/* faint paper grain via layered gradient lines */}
    <AbsoluteFill
      style={{
        opacity: 0.5,
        background: `radial-gradient(900px 700px at 92% 96%, ${C.paper100} 0%, rgba(0,0,0,0) 55%)`,
      }}
    />
    <AbsoluteFill
      style={{
        padding: pad,
        display: 'flex',
        flexDirection: 'column',
        alignItems: align,
        justifyContent: justify,
      }}
    >
      {children}
    </AbsoluteFill>
  </AbsoluteFill>
);
