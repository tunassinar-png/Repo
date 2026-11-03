import React from 'react';
import {Composition} from 'remotion';
import {TestVideo} from './TestVideo';

export const Root: React.FC = () => (
  <Composition
    id="TestVideo"
    component={TestVideo}
    durationInFrames={150}
    fps={30}
    width={1920}
    height={1080}
  />
);
