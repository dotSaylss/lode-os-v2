import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { Eyebrow, TraceChip, Check, ArrowRight } from '../components/primitives';
import { UserBubble, LodeAnswer } from '../components/chat';
import { riseIn, ramp } from '../lib/anim';

// SCENE 5 - USE CASE 3: THE AI-NATIVE CREATOR
// "New revenue, on your terms." Kai Rivers: connectors talk to each other.
// One ask carries a track from his Untitled library into a Disco pitch, as a
// DRAFT awaiting approval - the human-set permission leash is the whole point.
export const S5Creator: React.FC = () => {
  const frame = useCurrentFrame();

  const connectors = ['Suno', 'Untitled', 'Mogul', 'Disco'];

  return (
    <Stage pad={0} justify="flex-start">
      <div style={{ padding: '64px 140px 0' }}>
        <div style={riseIn(frame, 4, 18, 16)}>
          <Eyebrow>Use case 03 · AI-native creator</Eyebrow>
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
          Kai Rivers — “new revenue, on your terms.”
        </h2>
      </div>

      {/* connector loop strip */}
      <div
        style={{
          marginTop: 30,
          padding: '0 140px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        {connectors.map((name, i) => (
          <React.Fragment key={name}>
            <div
              style={{
                ...riseIn(frame, 30 + i * 8, 16, 10),
                padding: '12px 22px',
                background: C.paper0,
                border: `1px solid ${C.paper200}`,
                borderRadius: 14,
                fontFamily: FONT.sans,
                fontSize: 21,
                fontWeight: 600,
                color: C.ink700,
                boxShadow: '0 4px 12px rgba(60,52,38,0.06)',
              }}
            >
              {name}
            </div>
            {i < connectors.length - 1 && (
              <div style={{ ...riseIn(frame, 34 + i * 8, 12, 0) }}>
                <ArrowRight color={C.inkMuted} size={22} />
              </div>
            )}
          </React.Fragment>
        ))}
        <div
          style={{
            ...riseIn(frame, 64, 16, 10),
            marginLeft: 8,
            fontFamily: FONT.sans,
            fontSize: 18,
            color: C.inkMuted,
          }}
        >
          create → organize → own → monetize
        </div>
      </div>

      {/* the cross-connector ask */}
      <div
        style={{
          marginTop: 44,
          padding: '0 140px',
          display: 'flex',
          flexDirection: 'column',
          gap: 26,
        }}
      >
        <UserBubble startFrame={78}>
          Use Afterburn from my Sync Ready playlist and submit it to the best Disco pitch.
        </UserBubble>

        {/* cross-connector trace - the connectors talking to each other */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginLeft: 56 }}>
          <TraceChip label="Read your Disco permissions" index={0} startFrame={108} />
          <TraceChip label="Loaded active briefs · Disco" index={1} startFrame={108} />
          <TraceChip label="Read your library · Untitled" index={2} startFrame={108} />
          <TraceChip label="Resolved “Afterburn” · Sync Ready" index={3} startFrame={108} />
        </div>

        <LodeAnswer startFrame={150}>
          Matched <em style={{ color: C.sage600, fontWeight: 500 }}>Afterburn</em> to the Nike
          brand brief on its actual sound profile. Pitch drafted —{' '}
          <em style={{ color: C.sage600, fontWeight: 500 }}>waiting for your approval</em> before
          anything is submitted.
        </LodeAnswer>
      </div>

      {/* the permission leash */}
      <div
        style={{
          position: 'absolute',
          right: 140,
          bottom: 88,
          ...riseIn(frame, 185, 22, 18),
        }}
      >
        <PermissionCard frame={frame} />
      </div>
    </Stage>
  );
};

const PermissionCard: React.FC<{ frame: number }> = ({ frame }) => {
  const rows = [
    { cap: 'Read library', perm: 'Allow', tone: 'sage' as const },
    { cap: 'Draft pitches', perm: 'Needs approval', tone: 'amber' as const },
    { cap: 'Auto-submit', perm: 'Deny', tone: 'clay' as const },
  ];
  const colors = {
    sage: { bg: C.sage50, bd: C.sage100, fg: C.sage700 },
    amber: { bg: '#FAF3E9', bd: '#EAD9BD', fg: C.amber500 },
    clay: { bg: '#FAEFEC', bd: '#E6CFC6', fg: C.clay500 },
  };
  return (
    <div
      style={{
        width: 420,
        background: C.paper0,
        border: `1px solid ${C.paper200}`,
        borderRadius: 20,
        boxShadow: '0 16px 40px rgba(60,52,38,0.12)',
        padding: '22px 24px',
      }}
    >
      <div
        style={{
          fontFamily: FONT.sans,
          fontSize: 16,
          fontWeight: 700,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: C.inkMuted,
          marginBottom: 16,
        }}
      >
        Disco · permissions you set
      </div>
      {rows.map((r, i) => {
        const c = colors[r.tone];
        const reveal = ramp(frame, 195 + i * 8, 12);
        return (
          <div
            key={r.cap}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '11px 0',
              opacity: reveal,
              borderBottom: i < 2 ? `1px solid ${C.paper100}` : 'none',
            }}
          >
            <span style={{ fontFamily: FONT.sans, fontSize: 20, color: C.ink700 }}>
              {r.cap}
            </span>
            <span
              style={{
                fontFamily: FONT.sans,
                fontSize: 16,
                fontWeight: 600,
                color: c.fg,
                background: c.bg,
                border: `1px solid ${c.bd}`,
                borderRadius: 999,
                padding: '5px 14px',
              }}
            >
              {r.perm}
            </span>
          </div>
        );
      })}
      <div
        style={{
          marginTop: 14,
          fontFamily: FONT.sans,
          fontSize: 16,
          fontStyle: 'italic',
          color: C.ink500,
          lineHeight: 1.4,
        }}
      >
        Agents read this first, every turn — and obey it.
      </div>
    </div>
  );
};
