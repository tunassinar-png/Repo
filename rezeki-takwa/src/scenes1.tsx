import React from 'react';
import {AbsoluteFill, interpolate, random, useCurrentFrame} from 'remotion';
import {Briefcase, C, Chip, ClockIcon, Coin, FONT, Headline, Heart, Layer, Moon, Person, Sun, Wallet, SceneFade, clamp, localStarts, ramp, useSp, win, SceneT, W} from './common';

type P = {s: SceneT};

/* ───────── 1. HOOK: sibuk mencari rezeki → siapa yang memberi? ───────── */
export const HookScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const phase2 = ramp(f, L[2] - 6, L[2] + 24);
  const speed = 0.022 + 0.03 * ramp(f, L[1], L[1] + 50);
  const ang = f * speed;
  const items = ['coin', 'brief', 'clock', 'wallet', 'coin', 'brief', 'clock', 'coin'];
  return (
    <SceneFade dur={s.dur}>
      <div style={{opacity: 1 - phase2}}><Headline lines={[{text: 'SIBUK'}, {text: 'MENCARI'}, {text: 'REZEKI', color: C.gold}]} start={6} size={104} top={210} /></div>
      <div style={{opacity: phase2}}><Headline lines={[{text: 'SIAPA'}, {text: 'SEBENARNYA', color: C.gold}, {text: 'YANG MEMBERI?'}]} start={L[2]} size={92} top={210} /></div>
      <Layer>
        {/* orbit ring */}
        <ellipse cx={540} cy={860} rx={400} ry={230} fill="none" stroke={C.gold} strokeWidth="3" strokeDasharray="10 14" opacity={0.35 * (1 - phase2)} />
        {items.map((it, i) => {
          const a = ang + (i / items.length) * Math.PI * 2;
          const x = 540 + Math.cos(a) * 400, y = 860 + Math.sin(a) * 230;
          const scale = (0.75 + 0.35 * Math.sin(a)) * sp(10 + i * 3) * (1 - phase2);
          return (
            <g key={i} transform={`translate(${x} ${y}) scale(${scale}) translate(-50 -50)`}>
              {it === 'coin' && <Coin size={100} spin={f * 0.15 + i} />}
              {it === 'brief' && <Briefcase size={100} />}
              {it === 'clock' && <ClockIcon size={100} t={f * 3} />}
              {it === 'wallet' && <Wallet size={120} />}
            </g>
          );
        })}
        {/* light beam for phase 2 */}
        <defs><linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={C.gold} stopOpacity="0.55" /><stop offset="1" stopColor={C.gold} stopOpacity="0" /></linearGradient></defs>
        <polygon points="470,790 610,790 820,1180 260,1180" fill="url(#beam)" opacity={phase2} />
        <Person x={540} y={1160} scale={0.78} pose={phase2 > 0.5 ? 'stand' : 'run'} mood={phase2 > 0.5 ? 'calm' : 'tired'} t={f} tilt={-12 * phase2} />
        <g opacity={phase2} transform={`translate(540 ${760 + Math.sin(f / 10) * 10}) scale(${0.9 + 0.1 * Math.sin(f / 12)})`}>
          <text textAnchor="middle" fontSize="170" fontWeight="900" fontFamily={FONT} fill={C.gold} style={{filter: 'drop-shadow(0 0 30px rgba(244,201,93,0.7))'}}>?</text>
        </g>
      </Layer>
    </SceneFade>
  );
};

/* ───────── 2. STRUGGLE: ayah bekerja, duit tak cukup ───────── */
export const StruggleScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const walk = ramp(f, L[1], L[2] - 6, (x) => x);
  const px = 150 + walk * 780;
  const panel = ramp(f, L[2] - 4, L[2] + 16);
  const barIn = ramp(f, L[2] + 10, L[2] + 60);
  const sunA = Math.PI * (1 - walk);   // sun arc from left to right
  const sunX = 540 + Math.cos(sunA) * 380, sunY = 520 - Math.sin(sunA) * 250;
  const dayOpacity = 1 - panel;
  return (
    <SceneFade dur={s.dur}>
      <Layer>
        <g opacity={dayOpacity}>
          <path d="M160 520 A380 250 0 0 1 920 520" fill="none" stroke={C.gold} strokeWidth="3" strokeDasharray="8 12" opacity="0.4" />
          <g transform={`translate(${sunX} ${sunY}) translate(-60 -60)`} opacity={ramp(f, L[1] - 6, L[1] + 10)}><Sun size={120} rot={f * 1.5} /></g>
          <g transform="translate(110 260)" opacity={ramp(f, L[1], L[1] + 14)}><ClockIcon size={90} t={walk * 360 * 3} /></g>
          <rect x="0" y="1150" width={W} height="6" fill="rgba(255,255,255,0.14)" />
          {Array.from({length: 9}).map((_, i) => <rect key={i} x={((i * 150 - f * 6) % 1350 + 1350) % 1350 - 120} y="1170" width="70" height="6" rx="3" fill="rgba(255,255,255,0.12)" />)}
        </g>
        <g opacity={dayOpacity}>
          <Person x={f < L[1] ? 540 : px} y={1150} scale={0.86 * sp(2)} pose={f < L[1] ? 'stand' : 'walk'} mood={f < L[1] ? 'neutral' : 'tired'} t={f} briefcase={f >= L[1]} />
        </g>
        {/* infographic panel: income vs needs */}
        <g opacity={panel} transform={`translate(0 ${(1 - panel) * 40})`}>
          <rect x="70" y="250" width="940" height="640" rx="40" fill="rgba(0,0,0,0.32)" stroke="rgba(255,255,255,0.18)" strokeWidth="2" />
          <text x="120" y="330" fontSize="34" fontWeight="800" letterSpacing="4" fill={C.mint} fontFamily={FONT}>PENDAPATAN</text>
          <rect x="120" y="350" width="840" height="64" rx="32" fill="rgba(255,255,255,0.1)" />
          <rect x="120" y="350" width={840 * 0.42 * barIn} height="64" rx="32" fill={C.mint} />
          <text x="120" y="500" fontSize="34" fontWeight="800" letterSpacing="4" fill={C.coral} fontFamily={FONT}>KEPERLUAN</text>
          <rect x="120" y="520" width="840" height="64" rx="32" fill="rgba(255,255,255,0.1)" />
          <rect x="120" y="520" width={840 * 1.0 * barIn} height="64" rx="32" fill={C.coral} />
          <g opacity={ramp(f, L[2] + 55, L[2] + 70)} transform={`translate(${960 + Math.sin(f / 4) * 6} 552)`}><path d="M0-30l40 30-40 30v-18h-30v-24h30z" fill={C.coral} /></g>
        </g>
        <g opacity={panel}>
          <Person x={230} y={1150} scale={0.62} pose="stand" mood="tired" t={f} />
          <g transform="translate(560 1050)" opacity={ramp(f, L[2] + 30, L[2] + 44)}><Wallet size={170} /></g>
        </g>
      </Layer>
      {/* chips */}
      <div style={{opacity: 1 - panel}}><Chip text="SEORANG AYAH" x={540} y={760} at={4} /></div>
      <div style={{opacity: panel}}>
        {['BIL', 'SEWA', 'MAKAN', 'SEKOLAH'].map((t, i) => <Chip key={t} text={t} x={190 + i * 230} y={660 + (i % 2) * 70} at={L[2] + 24 + i * 7} color={C.cream} size={30} />)}
        <Chip text="TAK CUKUP!" x={700} y={800} at={L[2] + 70} color={C.coral} fg={C.cream} size={48} rot={-6} />
      </div>
    </SceneFade>
  );
};

/* ───────── 3. NIGHT: memandang anak-anak, berbisik tentang esok ───────── */
const Bed: React.FC<{x: number; y: number; blanket: string; f: number; at: number}> = ({x, y, blanket, f, at}) => {
  const z = (f - at) / 30;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect x="0" y="-8" width="200" height="40" rx="12" fill="#4a3322" />
      <rect x="6" y="-30" width="188" height="34" rx="14" fill="#efe6d2" />
      <circle cx="34" cy="-34" r="26" fill={C.skin} /><path d="M10 -40Q34 -70 58 -40Q34 -52 10 -40z" fill="#2a1d14" /><path d="M24 -32q6 5 12 0" stroke={C.ink} strokeWidth="3" fill="none" strokeLinecap="round" />
      <rect x="62" y="-48" width="132" height="58" rx="18" fill={blanket} />
      {[0, 1, 2].map((k) => {
        const p = ((z * 0.7 + k * 0.33) % 1 + 1) % 1;
        return <text key={k} x={60 + p * 40} y={-70 - p * 60} fontSize={22 + p * 18} fontWeight="900" fill={C.sky} fontFamily={FONT} opacity={Math.sin(p * Math.PI)}>z</text>;
      })}
    </g>
  );
};
export const NightScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const bubble = sp(L[1] + 2, 12);
  return (
    <SceneFade dur={s.dur}>
      <Layer>
        {Array.from({length: 26}).map((_, i) => <circle key={i} cx={random(`nx${i}`) * W} cy={190 + random(`ny${i}`) * 380} r={1.5 + random(`nr${i}`) * 2.6} fill={C.cream} opacity={0.25 + 0.7 * Math.abs(Math.sin(f / 18 + i))} />)}
        <g transform="translate(800 250)" opacity={ramp(f, 0, 20)}><Moon size={150} /></g>
        {/* house */}
        <g opacity={ramp(f, 2, 22)}>
          <polygon points="540,420 120,660 960,660" fill="#1a2a57" stroke="#3b4f93" strokeWidth="6" strokeLinejoin="round" />
          <rect x="160" y="660" width="760" height="500" fill="#2a3a6e" opacity="0.9" />
          <rect x="160" y="660" width="760" height="500" fill="none" stroke="#3b4f93" strokeWidth="6" />
          <rect x="180" y="680" width="720" height="460" fill={C.gold} opacity={0.13 + 0.03 * Math.sin(f / 14)} />
          <rect x="120" y="1160" width="840" height="14" rx="7" fill="#101a3d" />
          <circle cx="540" cy="560" r="34" fill={C.gold} opacity="0.85" /><circle cx="540" cy="560" r="34" fill="none" stroke="#3b4f93" strokeWidth="6" />
        </g>
        <Bed x={660} y={1090} blanket="#2fa58c" f={f} at={0} />
        <Bed x={660} y={1000} blanket="#d9a441" f={f} at={20} />
        <Bed x={660} y={910} blanket="#7a6ad8" f={f} at={40} />
        <Person x={330} y={1150} scale={0.84 * sp(6)} pose="stand" mood={f < L[1] ? 'neutral' : 'worried'} t={f} tilt={f > L[0] ? 8 : 0} />
        {/* thought bubble */}
        <g transform={`translate(300 340) scale(${bubble}) translate(-300 -340)`} opacity={bubble}>
          <circle cx="330" cy="496" r="13" fill={C.cream} /><circle cx="352" cy="545" r="9" fill={C.cream} />
          {[[300, 330, 110], [215, 365, 72], [385, 372, 78], [300, 405, 78], [245, 300, 64], [358, 296, 66]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} fill={C.cream} />)}
        </g>
        <g transform="translate(245 285)" opacity={bubble * (1 - ramp(f, L[2] - 4, L[2] + 8))}><Heart size={110} color={C.coral} /></g>
        <g transform={`translate(300 345) scale(${sp(L[2] + 4, 10)})`} opacity={ramp(f, L[2], L[2] + 8)}>
          <rect x="-70" y="-70" width="140" height="150" rx="16" fill="#fff" stroke={C.ink} strokeWidth="4" />
          <rect x="-70" y="-70" width="140" height="44" rx="16" fill={C.coral} /><rect x="-70" y="-40" width="140" height="14" fill={C.coral} />
          <text x="0" y="-38" textAnchor="middle" fontSize="28" fontWeight="900" fill="#fff" fontFamily={FONT}>ESOK</text>
          <text x="0" y="52" textAnchor="middle" fontSize="80" fontWeight="900" fill={C.ink} fontFamily={FONT}>?</text>
        </g>
      </Layer>
      <Chip text="ANAK-ANAK TIDUR" x={760} y={730} at={4} color={C.sky} size={28} />
    </SceneFade>
  );
};
