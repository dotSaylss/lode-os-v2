import React from 'react';
import { Composition } from 'remotion';
import { LodeOSDemo, DEMO_DURATION } from './LodeOSDemo';
import { VIDEO } from './lib/theme';
import './lib/fonts';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LodeOSDemo"
      component={LodeOSDemo}
      durationInFrames={DEMO_DURATION}
      fps={VIDEO.fps}
      width={VIDEO.width}
      height={VIDEO.height}
    />
  );
};
