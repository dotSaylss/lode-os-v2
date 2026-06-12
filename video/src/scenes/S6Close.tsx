import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { LodeMark } from '../components/chat';
import { riseIn, ramp } from '../lib/anim';

// SCENE 6 - CLOSE
// One product, three businesses. The thesis line, the stack, the name.
export const S6Close: React.FC = () => {
  const frame = useCurrentFrame();

  const lines = [
    'Recover what you’re owed.',
    'Operate at scale.',
    'Make new money — on your terms.',
  ];

  const stack = ['Google ADK', 'MCP', 'A2A', 'Gemini on Vertex AI', 'Cloud Run'];

  return (
    <Stage align="center" justify="center">
      <div style={{ ...riseIn(frame, 6, 20, 0), marginBottom: 34 }}>
        <LodeMark size={92} />
      </div>

      <div style={{ textAlign: 'center', maxWidth: 1300 }}>
        {lines.map((l, i) => (
          <div
            key={i}
            style={{
              ...riseIn(frame, 24 + i * 16, 22, 16),
              fontFamily: FONT.serif,
              fontSize: 58,
              fontWeight: 400,
              letterSpacing: '-0.02em',
              lineHeight: 1.22,
              color: i === 2 ? C.sage600 : C.ink900,
            }}
          >
            {l}
          </div>
        ))}
      </div>

      <div
        style={{
          ...riseIn(frame, 90, 22, 16),
          marginTop: 50,
          fontFamily: FONT.sans,
          fontSize: 30,
          fontWeight: 600,
          color: C.ink700,
          textAlign: 'center',
        }}
      >
        LodeOS — the agentic control plane for the music business.
      </div>

      {/* stack strip */}
      <div
        style={{
          ...riseIn(frame, 120, 20, 14),
          marginTop: 40,
          display: 'flex',
          gap: 14,
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        {stack.map((s, i) => (
          <span
            key={s}
            style={{
              opacity: ramp(frame, 124 + i * 6, 12),
              fontFamily: FONT.sans,
              fontSize: 20,
              fontWeight: 600,
              color: C.sage700,
              background: C.sage50,
              border: `1px solid ${C.sage100}`,
              borderRadius: 999,
              padding: '9px 20px',
            }}
          >
            {s}
          </span>
        ))}
      </div>
    </Stage>
  );
};
