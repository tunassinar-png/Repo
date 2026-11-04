import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

const FONT = 'Inter, "DejaVu Sans", sans-serif';

type Scene = {
  label: string;
  shots: [string, string];
  vo: string;
  day: string;
  bg: [string, string];
};

const SCENES: Scene[] = [
  {label: 'BABAK 1 · ORBIT', shots: ['1A satelit, siklon global', '1B menembusi awan ke lautan'],
    vo: 'Bayangkan hujan turun setiap hari, tanpa henti, di seluruh dunia. Dari angkasa, Bumi diselubungi sistem ribut yang tidak lagi reda.',
    day: 'HARI 1', bg: ['#050b18', '#27384f']},
  {label: 'BABAK 2 · BANDAR', shots: ['2A dron tinggi, bandar banjir', '2B penjejakan rendah, arus jalan'],
    vo: 'Dalam beberapa hari, sistem saliran bandar tidak lagi mampu menampung. Sungai melimpah, jalan raya menjadi terusan, dan jutaan penduduk terkepung.',
    day: 'HARI 7', bg: ['#1b1f24', '#4b4a42']},
  {label: 'BABAK 3 · LADANG', shots: ['3A sawah tenggelam', '3B tanaman reput'],
    vo: 'Tanah yang tepu tidak dapat menyerap lagi. Akar tanaman kekurangan oksigen, tuaian reput, dan bekalan makanan mula terancam.',
    day: 'HARI 30', bg: ['#1a2316', '#4e5a38']},
  {label: 'BABAK 4 · TANAH RUNTUH', shots: ['4A cerun tergelincir', '4B jambatan runtuh'],
    vo: 'Air meresap ke dalam cerun dan melemahkan tanah. Tanah runtuh menimbus jalan, memusnahkan jambatan, dan memutuskan bekalan.',
    day: 'HARI 60', bg: ['#231a14', '#5a4533']},
  {label: 'BABAK 5 · HIDUPAN LIAR', shots: ['5A hutan hujan banjir', '5B muara dan terumbu'],
    vo: 'Habitat ditenggelamkan atau terhakis. Haiwan kehilangan tempat berlindung, dan terumbu karang ditimbus lumpur serta air tawar.',
    day: 'HARI 90', bg: ['#0e1c1a', '#2f4a45']},
  {label: 'BABAK 6 · BUMI', shots: ['6A cahaya menembusi awan', '6B satelit tarik keluar'],
    vo: 'Ini hanyalah senario hipotesis. Namun ia mengingatkan kita: kehidupan bergantung pada keseimbangan kitaran air yang rapuh.',
    day: '', bg: ['#0a1220', '#c8a160']},
];

const fade = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, start + 12, end - 12, end], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

const Rain: React.FC<{intensity: number}> = ({intensity}) => {
  const frame = useCurrentFrame();
  const lines = Array.from({length: 70});
  return (
    <AbsoluteFill style={{opacity: intensity}}>
      {lines.map((_, i) => {
        const x = (i * 137) % 1080;
        const speed = 38 + (i % 7) * 6;
        const y = ((frame * speed + i * 211) % 2200) - 150;
        return (
          <div key={i} style={{
            position: 'absolute', left: x, top: y, width: 2, height: 90 + (i % 5) * 20,
            background: 'rgba(220,230,245,0.35)', transform: 'rotate(8deg)',
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

const SceneView: React.FC<{scene: Scene; index: number}> = ({scene, index}) => {
  const frame = useCurrentFrame(); // local, 0..299
  const drift = interpolate(frame, [0, 300], [0, 1]);
  const rainOpacity = index === 5 ? interpolate(frame, [0, 300], [0.7, 0.05]) : 0.8;
  const shot = frame < 150 ? 0 : 1;
  const textShadow = '0 2px 14px rgba(0,0,0,0.5)';
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{
        background: `linear-gradient(${180 + drift * 20}deg, ${scene.bg[0]}, ${scene.bg[1]})`,
      }} />
      <Rain intensity={rainOpacity} />
      {/* storyboard info (reference only) */}
      <div style={{position: 'absolute', top: 300, left: 60, right: 60, fontFamily: FONT, color: 'rgba(255,255,255,0.55)', fontSize: 30, letterSpacing: 3}}>
        {scene.label}
        <div style={{fontSize: 26, marginTop: 10, letterSpacing: 1}}>SYOT {scene.shots[shot]}</div>
      </div>
      {/* day overlay: 5s..9s */}
      {scene.day && (
        <div style={{position: 'absolute', bottom: 560, width: '100%', textAlign: 'center', fontFamily: FONT, fontWeight: 500,
          fontSize: 56, letterSpacing: 8, color: 'rgba(255,255,255,0.92)', textShadow, opacity: fade(frame, index === 0 ? 150 : 60, index === 0 ? 270 : 180)}}>
          {scene.day}
        </div>
      )}
      {/* final line */}
      {index === 5 && (
        <div style={{position: 'absolute', bottom: 560, left: 80, right: 80, textAlign: 'center', fontFamily: FONT, fontWeight: 500,
          fontSize: 48, lineHeight: 1.3, color: 'rgba(255,255,255,0.95)', textShadow, opacity: fade(frame, 90, 290)}}>
          Kitaran air: seimbang, bukan berlebihan.
        </div>
      )}
      {/* VO caption strip (reference only) */}
      <div style={{position: 'absolute', bottom: 150, left: 60, right: 60, fontFamily: FONT, fontSize: 30, lineHeight: 1.4,
        color: 'rgba(255,255,255,0.7)', background: 'rgba(0,0,0,0.35)', padding: '16px 22px', borderRadius: 8,
        opacity: fade(frame, 15, 285)}}>
        <span style={{letterSpacing: 3, fontSize: 22, opacity: 0.7}}>NARATIF</span><br />{scene.vo}
      </div>
    </AbsoluteFill>
  );
};

export const Animatic: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const sec = frame / fps;
  const mm = String(Math.floor(sec / 60)).padStart(2, '0');
  const ss = String(Math.floor(sec % 60)).padStart(2, '0');
  const ff = String(frame % fps).padStart(2, '0');
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {SCENES.map((s, i) => (
        <Sequence key={i} from={i * 300} durationInFrames={300}>
          <SceneView scene={s} index={i} />
        </Sequence>
      ))}
      {/* title: 0:00.5 - 0:04 */}
      <div style={{position: 'absolute', top: 620, left: 70, right: 70, textAlign: 'center', fontFamily: FONT, fontWeight: 600,
        fontSize: 74, lineHeight: 1.2, letterSpacing: 3, color: 'rgba(255,255,255,0.95)',
        textShadow: '0 2px 18px rgba(0,0,0,0.55)', opacity: fade(frame, 15, 120)}}>
        APA JADI JIKA SETIAP HARI HUJAN TURUN DI SELURUH DUNIA?
      </div>
      {/* persistent hypothetical label */}
      <div style={{position: 'absolute', top: 260, left: 60, fontFamily: FONT, fontSize: 24, letterSpacing: 6, color: 'rgba(255,255,255,0.55)'}}>
        SENARIO HIPOTESIS
      </div>
      {/* animatic-only timecode */}
      <div style={{position: 'absolute', top: 60, right: 60, fontFamily: FONT, fontSize: 24, color: 'rgba(255,255,255,0.4)'}}>
        ANIMATIC {mm}:{ss}:{ff}
      </div>
    </AbsoluteFill>
  );
};
