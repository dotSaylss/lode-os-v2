import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { Eyebrow, CountUp, ArrowRight, Check } from '../components/primitives';
import { riseIn, ramp, pop } from '../lib/anim';
import { VIDEO } from '../lib/theme';

// SCENE 4 - USE CASE 2: THE LABEL
// "Operate the whole roster." Lode Records: $446,716 uncollected across 50
// artists. The signature beat: a visible LabelAgent -> ActionAgent A2A
// handoff, with a packet traveling the wire, then a batch of drafts.
export const S4Label: React.FC = () => {
  const frame = useCurrentFrame();
  const fps = VIDEO.fps;

  // packet travels from strategist to executor between f=150 and f=178
  const travel = ramp(frame, 150, 28);
  const ax = 560;
  const bx = 1360;
  const py = 560;
  const packetX = ax + (bx - ax) * travel;
  const handed = travel >= 1;

  return (
    <Stage pad={0} justify="flex-start">
      <div style={{ padding: '70px 140px 0' }}>
        <div style={riseIn(frame, 4, 18, 16)}>
          <Eyebrow>Use case 02 · Label / catalog team</Eyebrow>
        </div>
        <h2
          style={{
            ...riseIn(frame, 12, 20, 14),
            margin: '14px 0 0',
            fontFamily: FONT.serif,
            fontStyle: 'italic',
            fontSize: 44,
            fontWeight: 400,
            color: C.ink700,
          }}
        >
          Lode Records — “operate the whole roster.”
        </h2>
      </div>

      {/* big number */}
      <div
        style={{
          marginTop: 40,
          padding: '0 140px',
          display: 'flex',
          alignItems: 'baseline',
          gap: 28,
          ...riseIn(frame, 36, 20, 16),
        }}
      >
        <CountUp to={446716} startFrame={44} dur={44} size={120} />
        <div
          style={{
            fontFamily: FONT.sans,
            fontSize: 26,
            color: C.ink500,
            fontWeight: 500,
          }}
        >
          uncollected across <b style={{ color: C.ink900 }}>50 artists</b>
        </div>
      </div>

      {/* A2A handoff stage */}
      <AbsoluteFill>
        {/* the wire */}
        <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0 }}>
          <line
            x1={ax + 150}
            y1={py}
            x2={bx - 150}
            y2={py}
            stroke={handed ? C.sage400 : C.paper300}
            strokeWidth={3}
            strokeDasharray="4 10"
            opacity={ramp(frame, 130, 16)}
          />
        </svg>

        <AgentBox
          title="LabelAgent"
          sub="Strategist · Gemini 2.5 Pro"
          line="Found the bulk opportunity:&#10;neighboring rights, 31 artists."
          x={ax}
          y={py}
          startFrame={100}
          active={!handed}
        />
        <AgentBox
          title="ActionAgent"
          sub="Executor · Gemini 2.5 Flash"
          line={handed ? 'Drafting 31 registrations…' : 'Standing by'}
          x={bx}
          y={py}
          startFrame={118}
          active={handed}
        />

        {/* the traveling A2A packet */}
        {travel > 0 && travel < 1 && (
          <div
            style={{
              position: 'absolute',
              left: packetX,
              top: py,
              transform: 'translate(-50%,-50%)',
              background: C.sage500,
              color: '#fff',
              fontFamily: FONT.mono,
              fontSize: 16,
              fontWeight: 600,
              padding: '8px 14px',
              borderRadius: 10,
              boxShadow: '0 8px 20px rgba(60,52,38,0.18)',
              whiteSpace: 'nowrap',
            }}
          >
            transfer · draft_registrations
          </div>
        )}

        {/* A2A label badge in the middle */}
        <div
          style={{
            position: 'absolute',
            left: (ax + bx) / 2,
            top: py - 78,
            transform: 'translate(-50%,-50%)',
            ...riseIn(frame, 140, 16, 10),
            fontFamily: FONT.sans,
            fontSize: 19,
            fontWeight: 700,
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            color: C.sage600,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          Agent-to-agent handoff <ArrowRight color={C.sage600} size={20} />
        </div>
      </AbsoluteFill>

      {/* batch result */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 96,
          display: 'flex',
          justifyContent: 'center',
          ...riseIn(frame, 200, 20, 16),
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 12,
            background: C.sage50,
            border: `1px solid ${C.sage100}`,
            borderRadius: 999,
            padding: '14px 26px',
            fontFamily: FONT.sans,
            fontSize: 23,
            fontWeight: 600,
            color: C.sage700,
          }}
        >
          <Check color={C.sage600} size={22} />
          31 registrations drafted in one batch — a quarter's work, one turn
        </div>
      </div>
    </Stage>
  );
};

const AgentBox: React.FC<{
  title: string;
  sub: string;
  line: string;
  x: number;
  y: number;
  startFrame: number;
  active: boolean;
}> = ({ title, sub, line, x, y, startFrame, active }) => {
  const frame = useCurrentFrame();
  const s = riseIn(frame, startFrame, 18, 14);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%,-50%) translateY(${(1 - (s.opacity as number)) * 14}px)`,
        opacity: s.opacity,
        width: 320,
        background: C.paper0,
        border: `2px solid ${active ? C.sage400 : C.paper200}`,
        borderRadius: 20,
        boxShadow: active
          ? '0 16px 40px rgba(87,125,99,0.20)'
          : '0 6px 18px rgba(60,52,38,0.07)',
        padding: '22px 24px',
        transition: 'border-color .2s, box-shadow .2s',
      }}
    >
      <div
        style={{
          fontFamily: FONT.sans,
          fontSize: 24,
          fontWeight: 700,
          color: C.ink900,
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: 15,
          color: active ? C.sage600 : C.inkMuted,
          marginTop: 4,
          marginBottom: 14,
        }}
      >
        {sub}
      </div>
      <div
        style={{
          fontFamily: FONT.sans,
          fontSize: 18,
          lineHeight: 1.4,
          color: C.ink700,
          whiteSpace: 'pre-line',
        }}
      >
        {line}
      </div>
    </div>
  );
};
