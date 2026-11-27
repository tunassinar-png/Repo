import React from 'react';
import {Composition} from 'remotion';
import {Rezeki} from './Rezeki';
import timeline from './timeline.json';

export const Root: React.FC = () => (
  <Composition id="Rezeki" component={Rezeki} durationInFrames={timeline.total} fps={timeline.fps} width={1080} height={1920} />
);
