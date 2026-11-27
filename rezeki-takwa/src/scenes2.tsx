import React from 'react';
import {useCurrentFrame, random} from 'remotion';
import {AR_FONT, C, Chip, Cloud, Coin, FONT, Headline, Heart, Layer, Lantern, Person, SceneFade, clamp, localStarts, ramp, useSp, win, SceneT, W, useArabicFont} from './common';

type P = {s: SceneT};

/* ───────── 4. PRAYER: dalam kesempitan, tetap solat ───────── */
export const PrayerScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  // gap half-width between the two walls
  const close = ramp(f, 4, L[0] + 36);
  const open1 = ramp(f, L[1] + 8, L[1] + 70), open2 = ramp(f, L[2], L[2] + 60);
  const g = 480 - 300 * close + 130 * open1 + 90 * open2;
  const prayer = ramp(f, L[1], L[1] + 20);
  const glow = ramp(f, L[1] + 4, L[1] + 40);
  const lantern = ramp(f, L[2] - 2, L[2] + 24);
  return (
    <SceneFade dur={s.dur}>
      <div style={{opacity: 1 - prayer}}><Headline lines={[{text: 'DALAM'}, {text: 'KESEMPITAN', color: C.coral}]} start={4} size={100} top={230} /></div>
      <div style={{opacity: prayer}}><Headline lines={[{text: 'TETAP'}, {text: 'MENJAGA SOLAT', color: C.gold}]} start={L[1]} size={92} top={230} /></div>
      <Layer>
        <defs>
          <pattern id="hatch" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="14" fill="#1b2b2a" /><line x1="0" y1="0" x2="0" y2="14" stroke="#3b504d" strokeWidth="5" /></pattern>
          <radialGradient id="halo"><stop offset="0" stopColor={C.gold} stopOpacity="0.7" /><stop offset="1" stopColor={C.gold} stopOpacity="0" /></radialGradient>
        </defs>
        <circle cx="540" cy="930" r="420" fill="url(#halo)" opacity={glow * 0.9} />
        {/* walls */}
        <rect x={540 - g - 700} y="520" width="700" height="640" fill="url(#hatch)" /><rect x={540 - g - 6} y="520" width="6" height="640" fill="#0a1514" />
        <rect x={540 + g} y="520" width="700" height="640" fill="url(#hatch)" /><rect x={540 + g} y="520" width="6" height="640" fill="#0a1514" />
        {/* lanterns */}
        <g transform="translate(180 540)" opacity={lantern}><Lantern size={110} glow={lantern} /></g>
        <g transform="translate(790 540)" opacity={lantern}><Lantern size={110} glow={lantern} /></g>
        {/* prayer mat */}
        <g transform={`translate(540 1148) scale(${prayer} 1)`}>
          <rect x="-190" y="-10" width="380" height="40" rx="10" fill="#0f6b55" stroke={C.gold} strokeWidth="4" />
          <path d="M-60 -2h120v26h-120z" fill="none" stroke={C.gold} strokeWidth="3" opacity="0.7" />
        </g>
        <Person x={540} y={1146} scale={0.84 * sp(2)} pose={prayer > 0.5 ? 'qiyam' : 'stand'} mood={prayer > 0.5 ? 'calm' : 'worried'} t={f} />
      </Layer>
      <Chip text="SOLAT" x={540} y={760} at={L[1] + 14} />
      <Chip text="JANJI ALLAH" x={540} y={1240} at={L[2] + 18} color={C.mint} />
    </SceneFade>
  );
};

/* ───────── 5. VERSE: Surah At-Talaq 65:2–3 ───────── */
const AR1 = 'وَمَن يَتَّقِ ٱللَّهَ يَجْعَل لَّهُۥ مَخْرَجًا';
const AR2 = 'وَيَرْزُقْهُ مِنْ حَيْثُ لَا يَحْتَسِبُ';
const Envelope: React.FC = () => (
  <svg width="100" height="100" viewBox="0 0 100 100"><rect x="8" y="22" width="84" height="58" rx="8" fill={C.cream} /><path d="M10 26 50 56 90 26" fill="none" stroke={C.goldDeep} strokeWidth="5" strokeLinejoin="round" /><circle cx="50" cy="56" r="8" fill={C.coral} /></svg>
);
const Apple: React.FC = () => (
  <svg width="100" height="100" viewBox="0 0 100 100"><path d="M50 30C30 14 8 34 14 58c5 20 22 32 36 24 14 8 31-4 36-24 6-24-16-44-36-28z" fill={C.coral} /><path d="M50 30c0-10 4-18 12-22" stroke="#6b3b1d" strokeWidth="5" fill="none" strokeLinecap="round" /><path d="M56 16q14-4 20 6-14 6-20-6z" fill={C.mint} /></svg>
);
export const VerseScene: React.FC<P> = ({s}) => {
  useArabicFont();
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const arLine = (at: number) => ({opacity: ramp(f, at, at + 28), transform: `translateY(${(1 - ramp(f, at, at + 28)) * 24}px)`, filter: `blur(${(1 - ramp(f, at, at + 28)) * 10}px)`});
  const door = ramp(f, L[1] + 40, L[1] + 100);
  const cards = [
    {label: 'WANG', x: 640, y: 880, from: [-700, -300], icon: <Coin size={90} />},
    {label: 'MAKANAN', x: 880, y: 880, from: [600, -500], icon: <Apple />},
    {label: 'PELUANG', x: 640, y: 1070, from: [-600, 300], icon: <Envelope />},
    {label: 'BANTUAN', x: 880, y: 1070, from: [700, 260], icon: <Heart size={90} color={C.coral} />},
  ];
  return (
    <SceneFade dur={s.dur}>
      {/* banner */}
      <div style={{position: 'absolute', top: 205, left: 0, right: 0, display: 'flex', justifyContent: 'center', opacity: ramp(f, 4, 20), transform: `scale(${0.9 + 0.1 * ramp(f, 4, 20)})`}}>
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 34, letterSpacing: 5, color: C.ink, background: `linear-gradient(90deg, ${C.goldDeep}, ${C.gold}, ${C.goldDeep})`, padding: '14px 44px', borderRadius: 14, boxShadow: '0 10px 30px rgba(0,0,0,0.4)'}}>SURAH AT-TALAQ · 65 : 2 – 3</div>
      </div>
      {/* arabic */}
      <div dir="rtl" style={{position: 'absolute', top: 320, left: 40, right: 40, textAlign: 'center', fontFamily: AR_FONT, fontSize: 80, lineHeight: 1.85, color: C.cream, textShadow: '0 0 40px rgba(244,201,93,0.45)'}}>
        <div style={arLine(L[1] - 4)}>{AR1}</div>
        <div style={arLine(L[2] - 4)}>{AR2}</div>
      </div>
      <Layer>
        <defs><radialGradient id="dl"><stop offset="0" stopColor={C.cream} /><stop offset="1" stopColor={C.gold} stopOpacity="0.2" /></radialGradient></defs>
        {/* book stand (before arabic) */}
        <g transform={`translate(540 520) scale(${sp(8)})`} opacity={1 - ramp(f, L[1] - 6, L[1] + 14)}>
          <path d="M-150-70 0-50v110L-150 40z" fill={C.cream} stroke={C.teal} strokeWidth="8" strokeLinejoin="round" /><path d="M150-70 0-50v110L150 40z" fill={C.cream} stroke={C.teal} strokeWidth="8" strokeLinejoin="round" />
          {[-30, -5, 20].map((y, i) => <g key={i}><line x1="-120" y1={-45 + y + 10} x2="-30" y2={-35 + y + 10} stroke={C.teal} strokeWidth="4" opacity="0.6" /><line x1="120" y1={-45 + y + 10} x2="30" y2={-35 + y + 10} stroke={C.teal} strokeWidth="4" opacity="0.6" /></g>)}
          <path d="M-90 70 90 190M90 70-90 190" stroke="#a46a35" strokeWidth="14" strokeLinecap="round" />
        </g>
        {/* door = jalan keluar */}
        <g opacity={ramp(f, L[1] + 30, L[1] + 50)}>
          <rect x="110" y="860" width="250" height="330" rx="10" fill="#0a1a17" stroke={C.gold} strokeWidth="6" />
          <rect x="122" y="872" width="226" height="318" fill="url(#dl)" opacity={door} />
          <polygon points={`122,872 ${122 + 226 * (1 - door * 0.82)},${880 + 10 * door} ${122 + 226 * (1 - door * 0.82)},${1180 - 10 * door} 122,1190`} fill="#8a5a2b" />
          <circle cx={122 + 226 * (1 - door * 0.82) - 20} cy="1030" r="8" fill={C.gold} />
        </g>
        {/* rezeki cards flying in */}
        {cards.map((c, i) => {
          const p = ramp(f, L[2] + 6 + i * 8, L[2] + 40 + i * 8, (x) => 1 - Math.pow(1 - x, 3));
          const x = c.x + c.from[0] * (1 - p), y = c.y + c.from[1] * (1 - p);
          return (
            <g key={i}>
              <line x1={c.x + c.from[0] * 0.5} y1={c.y + c.from[1] * 0.5} x2={c.x} y2={c.y} stroke={C.gold} strokeWidth="3" strokeDasharray="8 10" opacity={0.5 * (1 - p) * ramp(f, L[2], L[2] + 10)} />
              <g transform={`translate(${x} ${y})`} opacity={Math.min(1, p * 2)}>
                <rect x="-100" y="-78" width="200" height="156" rx="26" fill="rgba(0,0,0,0.35)" stroke="rgba(255,255,255,0.25)" strokeWidth="2" />
                <g transform="translate(-45 -62)">{c.icon}</g>
                <text x="0" y="62" textAnchor="middle" fontSize="27" fontWeight="900" letterSpacing="2" fill={C.gold} fontFamily={FONT}>{c.label}</text>
              </g>
            </g>
          );
        })}
      </Layer>
      <Chip text="JALAN KELUAR" x={235} y={820} at={L[1] + 70} color={C.mint} size={28} />
      <Chip text="DARI ARAH TAK DISANGKA!" x={760} y={760} at={L[2] + 44} color={C.gold} size={28} />
    </SceneFade>
  );
};

/* ───────── 6. MYTH vs FACT: takwa bukan bermakna tiada ujian ───────── */
export const MythScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const shield = sp(L[2] + 4, 9);
  const wallClose = ramp(f, L[1], L[1] + 40);
  const rainOn = ramp(f, 6, 24);
  const g = 480 - 190 * wallClose;
  const strike = ramp(f, L[0] + 40, L[0] + 62);
  const Card: React.FC<{y: number; tag: string; text: string; col: string; at: number; bad?: boolean}> = ({y, tag, text, col, at, bad}) => {
    const p = sp(at, 12);
    return (
      <div style={{position: 'absolute', left: 70, right: 70, top: y, height: 170, borderRadius: 34, background: 'rgba(0,0,0,0.34)', border: `4px solid ${col}`, transform: `translateX(${(1 - p) * (bad ? -900 : 900)}px)`, fontFamily: FONT, padding: '22px 36px', boxSizing: 'border-box', overflow: 'hidden'}}>
        <div style={{fontSize: 26, fontWeight: 900, letterSpacing: 6, color: col}}>{tag}</div>
        <div style={{position: 'relative', display: 'inline-block', marginTop: 8, fontSize: 44, fontWeight: 800, color: C.cream, opacity: bad ? 1 - 0.35 * strike : 1}}>
          {text}
          {bad && <div style={{position: 'absolute', left: -6, top: '54%', height: 7, width: `${strike * 104}%`, background: C.coral, borderRadius: 4}} />}
        </div>
        <div style={{position: 'absolute', right: 30, top: 38, width: 84, height: 84, borderRadius: '50%', background: col, color: C.ink, fontSize: 56, fontWeight: 900, display: 'grid', placeItems: 'center', transform: `scale(${sp(at + (bad ? 44 : 14), 8)})`}}>{bad ? '✕' : '✓'}</div>
      </div>
    );
  };
  return (
    <SceneFade dur={s.dur}>
      <Card y={230} tag="MITOS" text="Bertakwa = tiada ujian" col={C.coral} at={4} bad />
      <Card y={430} tag="HAKIKAT" text="Bertakwa = teguh walau diuji" col={C.mint} at={L[2] - 6} />
      <Layer>
        <defs><pattern id="hatch2" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="14" height="14" fill="#1b2b2a" /><line x1="0" y1="0" x2="0" y2="14" stroke="#3b504d" strokeWidth="5" /></pattern></defs>
        <rect x={540 - g - 700} y="700" width="700" height="460" fill="url(#hatch2)" opacity={wallClose} /><rect x={540 + g} y="700" width="700" height="460" fill="url(#hatch2)" opacity={wallClose} />
        <g transform="translate(370 640)" opacity={rainOn}><Cloud size={340} color="#6f7f90" /></g>
        {/* rain */}
        {Array.from({length: 26}).map((_, i) => {
          const x = 400 + random(`rx${i}`) * 280; const sp2 = 10 + random(`rs${i}`) * 6;
          const y0 = 830 + ((f * sp2 + random(`ry${i}`) * 300) % 330);
          const hitY = shield > 0.5 ? 900 : 1100;
          if (y0 > hitY) return null;
          return <line key={i} x1={x} y1={y0} x2={x - 6} y2={y0 + 26} stroke={C.sky} strokeWidth="4" strokeLinecap="round" opacity={0.75 * rainOn} />;
        })}
        {/* shield */}
        <g transform={`translate(540 880) scale(${shield})`} opacity={Math.min(1, shield)}>
          <circle r="150" fill={C.mint} opacity="0.18" />
          <path d="M0-95 80-62v52c0 52-34 86-80 105-46-19-80-53-80-105v-52z" fill={C.teal} stroke={C.mint} strokeWidth="8" strokeLinejoin="round" />
          <g transform="translate(-30 -40)"><Heart size={60} color={C.cream} /></g>
        </g>
        <Person x={540} y={1170} scale={0.66 * sp(2)} pose="stand" mood={f < L[2] ? 'tired' : 'calm'} t={f} />
      </Layer>
      <Chip text="TAKWA" x={540} y={1245} at={L[2] + 10} color={C.mint} size={32} />
      <Chip text="UJIAN" x={820} y={820} at={10} color={C.coral} fg={C.cream} size={30} rot={6} />
    </SceneFade>
  );
};
