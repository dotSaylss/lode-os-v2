import React from 'react';
import { useCurrentFrame } from 'remotion';
import { Stage } from '../components/Stage';
import { C, FONT } from '../lib/theme';
import { Eyebrow, TraceChip, CountUp, Check } from '../components/primitives';
import { UserBubble, LodeAnswer, TierTag } from '../components/chat';
import { riseIn, ramp } from '../lib/anim';

// SCENE 3 - USE CASE 1: THE INDEPENDENT ARTIST
// "Find the money you're owed." June Freedom asks where she's losing money;
// the orchestrator audits her rights over MCP, surfaces $2,400 in unclaimed
// neighboring rights, and drafts the SoundExchange registration.
export const S3Artist: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <Stage pad={0} justify="flex-start">
      <div style={{ padding: '70px 140px 0' }}>
        <div style={riseIn(frame, 4, 18, 16)}>
          <Eyebrow>Use case 01 · Independent artist</Eyebrow>
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
          June Freedom — “find the money you're owed.”
        </h2>
      </div>

      {/* chat exchange */}
      <div
        style={{
          marginTop: 56,
          padding: '0 140px',
          display: 'flex',
          flexDirection: 'column',
          gap: 30,
        }}
      >
        <UserBubble startFrame={40}>Where am I losing money?</UserBubble>

        {/* trace chips: context gathered */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 10,
            marginLeft: 56,
          }}
        >
          <TraceChip label="Read your royalty data · Mogul (MCP)" index={0} startFrame={70} />
          <TraceChip label="Checked ASCAP & SoundExchange" index={1} startFrame={70} />
          <TraceChip label="Royalty orchestrator · Gemini 2.5 Pro" index={2} startFrame={70} />
        </div>

        <LodeAnswer startFrame={110}>
          I found <em style={{ color: C.sage600, fontWeight: 500 }}>$2,400</em> in unclaimed
          neighboring rights on your catalog. I've drafted the SoundExchange registration —
          want me to file it?
        </LodeAnswer>
        <TierTag tier="reasoning" startFrame={140} />
      </div>

      {/* the recovered-money figure with a drafted-registration card */}
      <div
        style={{
          position: 'absolute',
          right: 140,
          bottom: 90,
          display: 'flex',
          alignItems: 'flex-end',
          gap: 40,
          ...riseIn(frame, 165, 22, 20),
        }}
      >
        <DraftCard frame={frame} />
        <div style={{ textAlign: 'right' }}>
          <div
            style={{
              fontFamily: FONT.sans,
              fontSize: 18,
              fontWeight: 700,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: C.inkMuted,
              marginBottom: 10,
            }}
          >
            Recoverable, found in one turn
          </div>
          <CountUp to={2400} startFrame={170} dur={32} size={104} />
        </div>
      </div>
    </Stage>
  );
};

const DraftCard: React.FC<{ frame: number }> = ({ frame }) => {
  const stamped = ramp(frame, 205, 12) > 0.5;
  return (
    <div
      style={{
        width: 360,
        background: C.paper0,
        border: `1px solid ${C.paper200}`,
        borderRadius: 18,
        boxShadow: '0 16px 40px rgba(60,52,38,0.12)',
        padding: '20px 22px',
      }}
    >
      <div
        style={{
          fontFamily: FONT.mono,
          fontSize: 15,
          color: C.inkMuted,
          marginBottom: 10,
        }}
      >
        DRAFT · SX-2026-0417
      </div>
      <div
        style={{
          fontFamily: FONT.sans,
          fontSize: 22,
          fontWeight: 600,
          color: C.ink900,
          marginBottom: 16,
        }}
      >
        SoundExchange registration
      </div>
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 9,
          fontFamily: FONT.sans,
          fontSize: 17,
          fontWeight: 600,
          color: stamped ? C.sage700 : C.inkMuted,
          background: stamped ? C.sage50 : C.paper100,
          border: `1px solid ${stamped ? C.sage100 : C.paper200}`,
          borderRadius: 999,
          padding: '7px 14px',
          transition: 'all .2s',
        }}
      >
        {stamped && <Check color={C.sage600} size={16} />}
        {stamped ? 'Ready for your approval' : 'Drafting…'}
      </div>
    </div>
  );
};
