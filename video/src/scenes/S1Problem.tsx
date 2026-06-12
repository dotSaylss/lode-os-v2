import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { Eyebrow } from '../components/primitives';
import { PlatformNode, FallingCoin } from '../components/graph';
import { riseIn, ramp, fadeWindow } from '../lib/anim';

// SCENE 1 - THE PROBLEM
// An artist's catalog lives across disconnected platforms; money falls
// through the gaps between them. We show six platforms with no links, and
// money literally leaking through the gaps.
export const S1Problem: React.FC = () => {
  const frame = useCurrentFrame();

  const platforms = [
    { label: 'DistroKid', x: 360, y: 470 },
    { label: 'Spotify', x: 720, y: 360 },
    { label: 'ASCAP', x: 1120, y: 360 },
    { label: 'SoundExchange', x: 1500, y: 470 },
    { label: 'Suno', x: 560, y: 700 },
    { label: 'Disco', x: 1320, y: 700 },
  ];

  const headIn = riseIn(frame, 6, 22, 20);
  const subIn = riseIn(frame, 22, 22, 18);

  // The damning line fades in late.
  const lineOpacity = fadeWindow(frame, 150, 9999, 18, 1);

  return (
    <Stage justify="flex-start" pad={0}>
      {/* heading band */}
      <div style={{ padding: '90px 120px 0' }}>
        <div style={{ ...headIn }}>
          <Eyebrow color={C.terra600}>The problem</Eyebrow>
        </div>
        <h1
          style={{
            ...subIn,
            margin: '18px 0 0',
            fontFamily: FONT.serif,
            fontSize: 72,
            fontWeight: 400,
            letterSpacing: '-0.02em',
            lineHeight: 1.08,
            color: C.ink900,
            maxWidth: 1400,
          }}
        >
          An artist's money lives on six platforms.
          <br />
          <span style={{ color: C.terra600 }}>Nobody watches the gaps between them.</span>
        </h1>
      </div>

      {/* scattered, unconnected platforms */}
      <AbsoluteFill>
        {platforms.map((p, i) => (
          <PlatformNode
            key={p.label}
            label={p.label}
            x={p.x}
            y={p.y}
            startFrame={40 + i * 8}
          />
        ))}

        {/* money leaking through the gaps */}
        {[
          { x: 540, fromY: 540, delay: 0 },
          { x: 920, fromY: 470, delay: 16 },
          { x: 1300, fromY: 470, delay: 8 },
          { x: 700, fromY: 780, delay: 26 },
          { x: 1180, fromY: 800, delay: 20 },
          { x: 1480, fromY: 560, delay: 34 },
        ].map((c, i) => (
          <FallingCoin
            key={i}
            x={c.x}
            fromY={c.fromY}
            startFrame={95}
            delay={c.delay}
          />
        ))}
      </AbsoluteFill>

      {/* the leak callout */}
      <div
        style={{
          position: 'absolute',
          left: 120,
          bottom: 96,
          opacity: lineOpacity,
          display: 'flex',
          alignItems: 'baseline',
          gap: 20,
        }}
      >
        <span
          style={{
            fontFamily: FONT.mono,
            fontSize: 30,
            fontWeight: 500,
            color: C.terra600,
          }}
        >
          unregistered rights · unclaimed mechanicals · black-box royalties · unpitched sync
        </span>
      </div>
    </Stage>
  );
};
