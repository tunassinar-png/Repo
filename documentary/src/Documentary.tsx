import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import timeline from './timeline.json';
import {Background, Hud, Popup, clamp} from './common';
import {ImagineScene, IndustryScene, IntroScene, NewStdScene, OutroScene, TitleScene, ValueScene} from './scenes';

const SCENES: Record<string, React.FC<{dur: number}>> = {
  title: TitleScene, intro: IntroScene, imagine: ImagineScene, value: ValueScene,
  industry: IndustryScene, newstd: NewStdScene, outro: OutroScene,
};

/** Glowing light-sweep at every chapter change */
const Sweep: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <>
      {timeline.scenes.slice(1).map((s) => {
        const p = interpolate(f, [s.from - 10, s.from + 14], [0, 1], clamp);
        if (p <= 0 || p >= 1) return null;
        return <div key={s.id} style={{position: 'absolute', top: 0, bottom: 0, left: `${-20 + p * 140}%`, width: 160, background: 'linear-gradient(90deg, transparent, rgba(255,210,122,0.35), transparent)', transform: 'skewX(-18deg)'}} />;
      })}
    </>
  );
};

export const Documentary: React.FC = () => {
  const f = useCurrentFrame();
  const out = interpolate(f, [timeline.total - 20, timeline.total - 1], [1, 0], clamp);
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <AbsoluteFill style={{opacity: out}}>
        <Background />
        {timeline.scenes.map((s) => {
          const S = SCENES[s.id];
          return (
            <Sequence key={s.id} from={s.from} durationInFrames={s.dur}>
              <S dur={s.dur} />
            </Sequence>
          );
        })}
        <Sweep />
        {timeline.popups.map((p, i) => <Popup key={i} data={p} index={i} />)}
        <Hud />
      </AbsoluteFill>
      <Audio src={staticFile('soundtrack.wav')} />
    </AbsoluteFill>
  );
};
