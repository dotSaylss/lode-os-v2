import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { Eyebrow, Chip, ArrowRight } from '../components/primitives';
import { LodeMark } from '../components/chat';
import { PlatformNode, Link } from '../components/graph';
import { riseIn, ramp } from '../lib/anim';

// SCENE 2 - THE SOLUTION
// LodeOS puts a team of agents ACROSS the platforms. Now the same six
// platforms are wired into a central Lode hub; links draw themselves in
// sage (connected, not leaking). We name the two compute tiers.
export const S2Solution: React.FC = () => {
  const frame = useCurrentFrame();

  const cx = 960;
  const cy = 470;
  const nodes = [
    { label: 'DistroKid', x: 360, y: 330 },
    { label: 'Spotify', x: 360, y: 610 },
    { label: 'ASCAP', x: 1560, y: 330 },
    { label: 'SoundExchange', x: 1560, y: 610 },
    { label: 'Mogul', x: 700, y: 760 },
    { label: 'Disco', x: 1220, y: 760 },
  ];

  const headIn = riseIn(frame, 6, 22, 20);
  const hubPop = riseIn(frame, 30, 18, 0);
  const hubScale = ramp(frame, 30, 18);

  return (
    <Stage pad={0} justify="flex-start">
      <div style={{ padding: '84px 120px 0' }}>
        <div style={headIn}>
          <Eyebrow>The control plane</Eyebrow>
        </div>
        <h1
          style={{
            ...riseIn(frame, 18, 22, 18),
            margin: '16px 0 0',
            fontFamily: FONT.serif,
            fontSize: 64,
            fontWeight: 400,
            letterSpacing: '-0.02em',
            lineHeight: 1.1,
            color: C.ink900,
            maxWidth: 1500,
          }}
        >
          LodeOS puts a team of agents <span style={{ color: C.sage600 }}>across</span> them.
        </h1>
      </div>

      {/* connected graph */}
      <AbsoluteFill>
        <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0 }}>
          {nodes.map((n, i) => (
            <Link
              key={n.label}
              x1={cx}
              y1={cy}
              x2={n.x}
              y2={n.y}
              startFrame={70 + i * 6}
              dur={22}
              active
            />
          ))}
        </svg>

        {nodes.map((n, i) => (
          <PlatformNode
            key={n.label}
            label={n.label}
            x={n.x}
            y={n.y}
            startFrame={50 + i * 6}
          />
        ))}

        {/* central Lode hub */}
        <div
          style={{
            position: 'absolute',
            left: cx,
            top: cy,
            transform: `translate(-50%,-50%) scale(${0.7 + hubScale * 0.3})`,
            opacity: hubPop.opacity,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 14,
          }}
        >
          <div
            style={{
              width: 168,
              height: 168,
              borderRadius: '50%',
              background: C.paper0,
              border: `1px solid ${C.sage200}`,
              boxShadow: '0 16px 40px rgba(60,52,38,0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <LodeMark size={84} />
          </div>
          <div
            style={{
              fontFamily: FONT.sans,
              fontSize: 24,
              fontWeight: 700,
              color: C.ink900,
            }}
          >
            Lode
          </div>
        </div>
      </AbsoluteFill>

      {/* two-tier caption */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 92,
          display: 'flex',
          justifyContent: 'center',
          gap: 16,
          ...riseIn(frame, 130, 20, 16),
        }}
      >
        <Chip tone="paper" style={{ fontSize: 21 }}>
          <span style={{ width: 9, height: 9, borderRadius: '50%', background: C.amber500 }} />
          Gemini 2.5 Flash · quick lookups
        </Chip>
        <div style={{ display: 'flex', alignItems: 'center', color: C.inkMuted }}>
          <ArrowRight color={C.inkMuted} size={22} />
        </div>
        <Chip tone="sage" style={{ fontSize: 21 }}>
          <span style={{ width: 9, height: 9, borderRadius: '50%', background: C.sage500 }} />
          Gemini 2.5 Pro specialists · reasoning + action
        </Chip>
      </div>
    </Stage>
  );
};
