import React from 'react';
import {Composition} from 'remotion';
import {Animatic} from './Animatic';

export const Root: React.FC = () => (
  <Composition
    id="Animatic"
    component={Animatic}
    durationInFrames={1800}
    fps={30}
    width={1080}
    height={1920}
  />
);
