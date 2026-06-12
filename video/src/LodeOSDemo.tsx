import React from 'react';
import { AbsoluteFill } from 'remotion';
import { TransitionSeries, linearTiming } from '@remotion/transitions';
import { fade } from '@remotion/transitions/fade';
import { C } from './lib/theme';

import { S1Problem } from './scenes/S1Problem';
import { S2Solution } from './scenes/S2Solution';
import { S3Artist } from './scenes/S3Artist';
import { S4Label } from './scenes/S4Label';
import { S5Creator } from './scenes/S5Creator';
import { S6Close } from './scenes/S6Close';

// Scene durations (frames @ 30fps). No audio; pacing tuned for reading.
const D = {
  problem: 230, // ~7.7s
  solution: 220, // ~7.3s
  artist: 250, // ~8.3s
  label: 250, // ~8.3s
  creator: 270, // ~9.0s
  close: 200, // ~6.7s
};
const XFADE = 18; // crossfade frames between scenes

const scenes = [
  { c: <S1Problem />, d: D.problem },
  { c: <S2Solution />, d: D.solution },
  { c: <S3Artist />, d: D.artist },
  { c: <S4Label />, d: D.label },
  { c: <S5Creator />, d: D.creator },
  { c: <S6Close />, d: D.close },
];

// Total = sum of scene durations minus overlapped transitions.
export const DEMO_DURATION =
  scenes.reduce((a, s) => a + s.d, 0) - XFADE * (scenes.length - 1);

export const LodeOSDemo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.paper50 }}>
      <TransitionSeries>
        {scenes.map((s, i) => (
          <React.Fragment key={i}>
            <TransitionSeries.Sequence durationInFrames={s.d}>
              {s.c}
            </TransitionSeries.Sequence>
            {i < scenes.length - 1 && (
              <TransitionSeries.Transition
                presentation={fade()}
                timing={linearTiming({ durationInFrames: XFADE })}
              />
            )}
          </React.Fragment>
        ))}
      </TransitionSeries>
    </AbsoluteFill>
  );
};
