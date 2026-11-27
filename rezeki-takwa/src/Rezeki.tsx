import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import {Background, Captions, Hud, SceneT, scenes} from './common';
import {HookScene, NightScene, StruggleScene} from './scenes1';
import {MythScene, PrayerScene, VerseScene} from './scenes2';
import {BalanceScene, EndScene, FormulaScene} from './scenes3';

const MAP: Record<string, React.FC<{s: SceneT}>> = {
  hook: HookScene, struggle: StruggleScene, night: NightScene, prayer: PrayerScene, verse: VerseScene, myth: MythScene,
  balance: BalanceScene, formula: FormulaScene, end: EndScene,
};
export const Rezeki: React.FC = () => (
  <AbsoluteFill style={{background: '#000'}}>
    <Background />
    {scenes.map((s) => {
      const C = MAP[s.id];
      return <Sequence key={s.id} from={s.from} durationInFrames={s.dur}><C s={s} /></Sequence>;
    })}
    <Hud />
    <Captions />
    <Audio src={staticFile('soundtrack.mp3')} />
  </AbsoluteFill>
);
