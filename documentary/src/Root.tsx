import React from 'react';
import {Composition} from 'remotion';
import {Documentary} from './Documentary';
import timeline from './timeline.json';

export const Root: React.FC = () => (
  <Composition id="Documentary" component={Documentary} durationInFrames={timeline.total} fps={timeline.fps} width={1920} height={1080} />
);
