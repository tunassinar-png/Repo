import React from 'react';
import {AbsoluteFill, Easing, continueRender, delayRender, interpolate, interpolateColors, random, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import timeline from './timeline.json';

export const W = 1080;
export const H = 1920;
export const C = {
  deep: '#06221d', bg: '#0b3a31', teal: '#14806b', mint: '#59e3b5', gold: '#f4c95d', goldDeep: '#d99a1f',
  cream: '#fff4dc', coral: '#ff6b57', sky: '#7fb8ff', night: '#0b1536', slate: '#3b4a5a', ink: '#0a1f1b',
  skin: '#e9b88c', shirt: '#f2ead7', pants: '#1c2f4a',
};
export const FONT = "Inter, 'Helvetica Neue', Arial, sans-serif";
export const AR_FONT = "'AmiriQuran', 'Amiri', serif";
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

export type Word = {w: string; s: number; e: number};
export type Line = {text: string; start: number; end: number; words: Word[]};
export type SceneT = {id: string; label: string; from: number; dur: number; lines: Line[]};
export const scenes = timeline.scenes as SceneT[];

/* ---------- font loading (Arabic) ---------- */
let fontStarted = false;
export const useArabicFont = () => {
  const [handle] = React.useState(() => (fontStarted ? null : delayRender('arabic-font')));
  React.useEffect(() => {
    if (fontStarted || handle === null) return;
    fontStarted = true;
    const ff = new FontFace('AmiriQuran', `url(${staticFile('amiri-quran-arabic-400-normal.woff2')})`);
    ff.load().then((f) => { document.fonts.add(f); continueRender(handle); }).catch(() => continueRender(handle));
  }, [handle]);
};

/* ---------- helpers ---------- */
export const ease = Easing.out(Easing.cubic);
export const ramp = (f: number, a: number, b: number, e: (t: number) => number = ease) => interpolate(f, [a, b], [0, 1], {...clamp, easing: e});
export const useSp = () => {
  const f = useCurrentFrame();
  return (at: number, damping = 13, stiffness = 110) => spring({frame: f - at, fps: 30, config: {damping, stiffness, mass: 0.8}});
};
/** appear + optional disappear opacity */
export const win = (f: number, a: number, b: number | null = null, fade = 10) =>
  interpolate(f, b === null ? [a, a + fade] : [a, a + fade, b - fade, b], b === null ? [0, 1] : [0, 1, 1, 0], clamp);
export const localStarts = (s: SceneT) => s.lines.map((l) => l.start - s.from);

/* ---------- background ---------- */
const TINTS: Record<string, [string, string]> = {
  hook: ['#0d4a3f', '#06221d'], struggle: ['#2d4a47', '#10211f'], night: ['#13204a', '#070d24'], prayer: ['#17594a', '#08241e'],
  verse: ['#0f5143', '#051d18'], myth: ['#33454f', '#0c1a20'], balance: ['#134f45', '#061f1a'], formula: ['#176b58', '#082a22'], end: ['#0f4a3e', '#051d18'],
};
export const Background: React.FC = () => {
  const f = useCurrentFrame();
  const input: number[] = [0]; const top: string[] = [TINTS[scenes[0].id][0]]; const bot: string[] = [TINTS[scenes[0].id][1]];
  for (let i = 1; i < scenes.length; i++) {
    input.push(scenes[i].from - 14, scenes[i].from + 14);
    top.push(TINTS[scenes[i - 1].id][0], TINTS[scenes[i].id][0]); bot.push(TINTS[scenes[i - 1].id][1], TINTS[scenes[i].id][1]);
  }
  const c1 = interpolateColors(f, input, top), c2 = interpolateColors(f, input, bot);
  const t = f / 30;
  return (
    <AbsoluteFill style={{background: `linear-gradient(180deg, ${c1} 0%, ${c2} 100%)`}}>
      <svg width={W} height={H} style={{position: 'absolute', inset: 0, opacity: 0.07}}>
        <defs>
          <pattern id="star" width="180" height="180" patternUnits="userSpaceOnUse" patternTransform={`translate(${t * 6} ${t * 4})`}>
            <g fill="none" stroke="#fff" strokeWidth="2">
              <rect x="40" y="40" width="100" height="100" /><rect x="40" y="40" width="100" height="100" transform="rotate(45 90 90)" />
              <circle cx="90" cy="90" r="22" />
            </g>
          </pattern>
        </defs>
        <rect width={W} height={H} fill="url(#star)" />
      </svg>
      {[0, 1].map((i) => (
        <div key={i} style={{position: 'absolute', width: 900, height: 900, borderRadius: '50%', left: 100 + i * 300 + Math.sin(t * 0.4 + i * 2) * 90 - 450 + 300, top: 500 + i * 700 + Math.cos(t * 0.3 + i) * 80 - 450,
          background: 'radial-gradient(circle, rgba(244,201,93,0.13), transparent 62%)'}} />
      ))}
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 38}).map((_, i) => {
          const x = random(`x${i}`) * W; const sp = 10 + random(`s${i}`) * 28;
          const y = H + 30 - ((t * sp + random(`y${i}`) * H) % (H + 60));
          return <circle key={i} cx={x + Math.sin(t + i) * 16} cy={y} r={1.6 + random(`r${i}`) * 3.2} fill={C.gold} opacity={0.2 + 0.4 * Math.abs(Math.sin(t * 0.9 + i))} />;
        })}
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.5) 100%)'}} />
    </AbsoluteFill>
  );
};

/* ---------- HUD (chapter dots) ---------- */
export const Hud: React.FC = () => {
  const f = useCurrentFrame();
  const idx = Math.max(0, scenes.findIndex((s, i) => f >= s.from && (i === scenes.length - 1 || f < scenes[i + 1].from)));
  const sc = scenes[idx]; const sf = f - sc.from;
  return (
    <AbsoluteFill style={{fontFamily: FONT, opacity: interpolate(f, [0, 20, timeline.total - 20, timeline.total - 4], [0, 1, 1, 0], clamp)}}>
      <div style={{position: 'absolute', top: 96, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 10}}>
        {scenes.map((s, i) => (
          <div key={s.id} style={{height: 10, width: i === idx ? 64 : 22, borderRadius: 5, background: i < idx ? C.gold : i === idx ? `linear-gradient(90deg, ${C.gold} ${ramp(sf, 0, sc.dur, (x) => x) * 100}%, rgba(255,255,255,0.25) ${ramp(sf, 0, sc.dur, (x) => x) * 100}%)` : 'rgba(255,255,255,0.22)', transition: 'none'}} />
        ))}
      </div>
      <div key={sc.id} style={{position: 'absolute', top: 128, left: 0, right: 0, textAlign: 'center', fontSize: 26, fontWeight: 800, letterSpacing: 8, color: C.gold, opacity: ramp(sf, 4, 18)}}>{sc.label}</div>
    </AbsoluteFill>
  );
};

/* ---------- karaoke captions ---------- */
const KEY = /^(rezeki|takwa|bertakwa|solat|solatnya|allah|usaha|keberkatannya|diuji|sempit|kesempitan|duit|jalan|keluar|esok|asbab|memberi|janji|tidak|disangka-sangka)$/i;
export const Captions: React.FC = () => {
  const f = useCurrentFrame();
  const all = scenes.flatMap((s) => s.lines);
  const cur = all.find((l, i) => f >= l.start - 4 && f < (all[i + 1]?.start ?? 1e9) - 4 && f < l.end + 22);
  if (!cur) return null;
  const a = interpolate(f, [cur.start - 4, cur.start + 6, cur.end + 8, cur.end + 22], [0, 1, 1, 0], clamp);
  const y = (1 - ramp(f, cur.start - 4, cur.start + 8)) * 24;
  return (
    <div style={{position: 'absolute', left: 70, right: 70, top: 1290, height: 330, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: a, transform: `translateY(${y}px)`, fontFamily: FONT}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '6px 18px', fontSize: 60, fontWeight: 800, lineHeight: 1.18, textAlign: 'center', letterSpacing: -0.5, textShadow: '0 4px 24px rgba(0,0,0,0.6)'}}>
        {cur.words.map((w, i) => {
          const done = f >= w.e - 2, active = f >= w.s - 2 && !done;
          const key = KEY.test(w.w.replace(/[.,:?!]/g, ''));
                    return (
            <span key={i} style={{display: 'inline-block', color: key ? (done || active ? C.gold : 'rgba(244,201,93,0.4)') : (done || active ? C.cream : 'rgba(255,244,220,0.38)'),               textShadow: active ? '0 0 26px rgba(244,201,93,0.7)' : undefined}}>{w.w}</span>
          );
        })}
      </div>
    </div>
  );
};

/* ---------- icons ---------- */
export const Coin: React.FC<{size?: number; spin?: number}> = ({size = 80, spin = 0}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{transform: `scaleX(${Math.cos(spin)})`}}>
    <circle cx="50" cy="50" r="46" fill={C.gold} stroke={C.goldDeep} strokeWidth="6" />
    <circle cx="50" cy="50" r="33" fill="none" stroke={C.goldDeep} strokeWidth="3" opacity="0.7" />
    <text x="50" y="62" textAnchor="middle" fontSize="32" fontWeight="900" fontFamily={FONT} fill={C.goldDeep}>RM</text>
  </svg>
);
export const Heart: React.FC<{size?: number; color?: string}> = ({size = 80, color = C.mint}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><path d="M50 88S8 62 8 34a22 22 0 0 1 42-9 22 22 0 0 1 42 9c0 28-42 54-42 54z" fill={color} /></svg>
);
export const Moon: React.FC<{size?: number}> = ({size = 120}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><path d="M68 10a42 42 0 1 0 22 70A36 36 0 0 1 68 10z" fill={C.gold} /></svg>
);
export const Sun: React.FC<{size?: number; rot?: number}> = ({size = 120, rot = 0}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><g transform={`rotate(${rot} 50 50)`}>{Array.from({length: 12}).map((_, i) => <rect key={i} x="48" y="3" width="4" height="12" rx="2" fill={C.gold} transform={`rotate(${i * 30} 50 50)`} />)}</g><circle cx="50" cy="50" r="24" fill={C.gold} /></svg>
);
export const Cloud: React.FC<{size?: number; color?: string}> = ({size = 300, color = '#7b8a9a'}) => (
  <svg width={size} height={size * 0.6} viewBox="0 0 200 120"><path d="M50 100a32 32 0 0 1-4-63 44 44 0 0 1 84-8 36 36 0 0 1 22 71z" fill={color} /></svg>
);
export const Lantern: React.FC<{size?: number; glow?: number}> = ({size = 120, glow = 1}) => (
  <svg width={size} height={size * 1.7} viewBox="0 0 60 102">
    <line x1="30" y1="0" x2="30" y2="14" stroke={C.gold} strokeWidth="2" />
    <path d="M18 14h24l4 8H14z" fill={C.goldDeep} /><rect x="16" y="22" width="28" height="44" rx="8" fill={C.gold} opacity={0.35 + 0.65 * glow} />
    <rect x="16" y="22" width="28" height="44" rx="8" fill="none" stroke={C.gold} strokeWidth="3" />
    <path d="M18 66h24l-4 10H22z" fill={C.goldDeep} /><circle cx="30" cy="44" r="7" fill={C.cream} opacity={glow} />
  </svg>
);
export const Briefcase: React.FC<{size?: number}> = ({size = 70}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><rect x="30" y="18" width="40" height="18" rx="6" fill="none" stroke="#8a5a2b" strokeWidth="7" /><rect x="8" y="30" width="84" height="58" rx="10" fill="#b0743a" /><rect x="8" y="52" width="84" height="6" fill="#8a5a2b" /><rect x="44" y="48" width="12" height="14" rx="3" fill={C.gold} /></svg>
);
export const Wallet: React.FC<{size?: number; empty?: boolean}> = ({size = 140}) => (
  <svg width={size} height={size * 0.8} viewBox="0 0 120 96"><path d="M12 22 80 8l6 14" fill="#7b4a22" /><rect x="6" y="22" width="108" height="68" rx="12" fill="#a96a32" /><rect x="76" y="44" width="38" height="24" rx="10" fill="#7b4a22" /><circle cx="90" cy="56" r="5" fill={C.gold} /></svg>
);
export const ClockIcon: React.FC<{size?: number; t?: number}> = ({size = 90, t = 0}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><circle cx="50" cy="50" r="44" fill={C.cream} stroke={C.goldDeep} strokeWidth="6" />
    <line x1="50" y1="50" x2="50" y2="22" stroke={C.ink} strokeWidth="6" strokeLinecap="round" transform={`rotate(${t * 12} 50 50)`} />
    <line x1="50" y1="50" x2="50" y2="30" stroke={C.coral} strokeWidth="6" strokeLinecap="round" transform={`rotate(${t * 1} 50 50)`} /></svg>
);
export const Mosque: React.FC<{size?: number}> = ({size = 160}) => (
  <svg width={size} height={size} viewBox="0 0 100 100"><path d="M20 90V52h60v38z" fill={C.cream} opacity="0.92" /><path d="M24 52a26 26 0 0 1 52 0z" fill={C.gold} /><rect x="48" y="14" width="4" height="14" fill={C.gold} /><circle cx="50" cy="12" r="3" fill={C.gold} /><rect x="42" y="68" width="16" height="22" rx="8" fill={C.teal} /></svg>
);

/* ---------- person ---------- */
export type Mood = 'happy' | 'sad' | 'worried' | 'tired' | 'calm' | 'neutral';
export type Pose = 'stand' | 'walk' | 'qiyam' | 'raise' | 'run' | 'reach';
export const Person: React.FC<{x: number; y: number; scale?: number; pose?: Pose; mood?: Mood; t?: number; flip?: boolean; briefcase?: boolean; tilt?: number; shirt?: string}> =
  ({x, y, scale = 1, pose = 'stand', mood = 'neutral', t = 0, flip = false, briefcase = false, tilt = 0, shirt = C.shirt}) => {
    const sw = pose === 'walk' ? Math.sin(t * 0.32) : pose === 'run' ? Math.sin(t * 0.6) : 0;
    const legA = pose === 'run' ? 38 : 26;
    const bob = pose === 'walk' || pose === 'run' ? Math.abs(Math.cos(t * (pose === 'run' ? 0.6 : 0.32))) * -7 : Math.sin(t * 0.08) * -1.5;
    const arm = (sx: number, ang: number, len = 98) => {
      const r = (ang * Math.PI) / 180; return {x2: sx + Math.sin(r) * len, y2: 142 + Math.cos(r) * len};
    };
    let aL = arm(72, -10 - sw * 24 * (pose === 'run' ? 1.5 : 1)), aR = arm(128, 10 + sw * 24 * (pose === 'run' ? 1.5 : 1));
    if (pose === 'raise') { aL = arm(72, -158); aR = arm(128, 158); }
    if (pose === 'reach') { aL = arm(72, -10); aR = arm(128, 120); }
    const lg = (hx: number, ang: number) => { const r = (ang * Math.PI) / 180; return {x2: hx + Math.sin(r) * 138, y2: 268 + Math.cos(r) * 138}; };
    const lL = lg(88, -sw * legA), lR = lg(112, sw * legA);
    const eyes = mood === 'calm'
      ? <><path d="M80 76q8 7 16 0M104 76q8 7 16 0" stroke={C.ink} strokeWidth="3.4" fill="none" strokeLinecap="round" /></>
      : mood === 'tired'
        ? <><path d="M80 77h16M104 77h16" stroke={C.ink} strokeWidth="3.6" strokeLinecap="round" /></>
        : <><circle cx="88" cy="76" r="3.8" fill={C.ink} /><circle cx="112" cy="76" r="3.8" fill={C.ink} /></>;
    const brows = mood === 'worried' || mood === 'sad'
      ? <><path d="M79 66l17-6M121 66l-17-6" stroke={C.ink} strokeWidth="3.2" strokeLinecap="round" /></> : null;
    const mouth = mood === 'happy' ? 'M86 90q14 14 28 0' : mood === 'calm' ? 'M90 91q10 7 20 0' : mood === 'neutral' ? 'M90 92h20' : 'M88 96q12-11 24 0';
    return (
      <g transform={`translate(${x} ${y + bob}) scale(${(flip ? -1 : 1) * scale} ${scale}) translate(-100 -420)`}>
        <ellipse cx="100" cy="424" rx="64" ry="10" fill="#000" opacity="0.28" />
        {/* back limbs */}
        <line x1="112" y1="268" x2={lR.x2} y2={lR.y2} stroke={C.pants} strokeWidth="26" strokeLinecap="round" />
        <line x1="88" y1="268" x2={lL.x2} y2={lL.y2} stroke={C.pants} strokeWidth="26" strokeLinecap="round" />
        <ellipse cx={lR.x2 + 8} cy={lR.y2 + 6} rx="20" ry="9" fill="#14121a" /><ellipse cx={lL.x2 + 8} cy={lL.y2 + 6} rx="20" ry="9" fill="#14121a" />
        <rect x="64" y="116" width="72" height="162" rx="24" fill={shirt} />
        <path d="M84 116l16 22 16-22z" fill="#d8ccb0" />
        <rect x="64" y="236" width="72" height="42" rx="14" fill={C.pants} opacity="0.0" />
        {/* arms */}
        {pose === 'qiyam' ? (
          <>
            <path d="M72 142 66 204 104 190" stroke={shirt} strokeWidth="20" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <path d="M128 142 134 204 96 190" stroke={shirt} strokeWidth="20" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            <circle cx="100" cy="190" r="11" fill={C.skin} />
          </>
        ) : (
          <>
            <line x1="72" y1="142" x2={aL.x2} y2={aL.y2} stroke={shirt} strokeWidth="20" strokeLinecap="round" /><circle cx={aL.x2} cy={aL.y2} r="10.5" fill={C.skin} />
            <line x1="128" y1="142" x2={aR.x2} y2={aR.y2} stroke={shirt} strokeWidth="20" strokeLinecap="round" /><circle cx={aR.x2} cy={aR.y2} r="10.5" fill={C.skin} />
            {briefcase && <g transform={`translate(${aR.x2 - 28} ${aR.y2 - 6}) scale(0.62)`}><Briefcase size={90} /></g>}
          </>
        )}
        <g transform={`rotate(${tilt} 100 108)`}>
          <rect x="91" y="98" width="18" height="26" rx="6" fill={C.skin} />
          <circle cx="100" cy="72" r="35" fill={C.skin} />
          <path d="M66 54 70 26Q100 14 130 26L134 54Q100 44 66 54z" fill="#15151b" />
          <path d="M70 54Q100 46 130 54" stroke="#2a2a35" strokeWidth="3" fill="none" />
          {eyes}{brows}
          <path d={mouth} stroke={C.ink} strokeWidth="3.4" fill="none" strokeLinecap="round" />
          {mood === 'tired' && <path d="M138 54q8 12 0 20q-8-8 0-20z" fill={C.sky} opacity="0.9" transform={`translate(0 ${(t * 0.7) % 14})`} />}
        </g>
      </g>
    );
  };

/** wrap an <svg> full-canvas layer */
export const Layer: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0, ...style}}>{children}</svg>
);

/** scene wrapper: fade in/out + gentle push-in */
export const SceneFade: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 12, dur - 10, dur], [0, 1, 1, 0], clamp);
  return <AbsoluteFill style={{opacity: o, transform: `scale(${interpolate(f, [0, dur], [1, 1.025], clamp)})`}}>{children}</AbsoluteFill>;
};

/** big headline (kinetic) */
export const Headline: React.FC<{lines: {text: string; color?: string}[]; start: number; size?: number; top?: number; stagger?: number}> = ({lines, start, size = 96, top = 230, stagger = 9}) => {
  const f = useCurrentFrame();
  return (
    <div style={{position: 'absolute', top, left: 60, right: 60, textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1.04, color: C.cream, letterSpacing: -2}}>
      {lines.map((l, i) => {
        const p = spring({frame: f - start - i * stagger, fps: 30, config: {damping: 14, stiffness: 120}});
        return <div key={i} style={{color: l.color ?? C.cream, opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 60}px) scale(${0.9 + 0.1 * p})`, textShadow: '0 6px 30px rgba(0,0,0,0.45)'}}>{l.text}</div>;
      })}
    </div>
  );
};

/** info chip / label */
export const Chip: React.FC<{text: string; x: number; y: number; at: number; color?: string; fg?: string; size?: number; rot?: number}> = ({text, x, y, at, color = C.gold, fg = C.ink, size = 34, rot = 0}) => {
  const f = useCurrentFrame();
  const p = spring({frame: f - at, fps: 30, config: {damping: 10, stiffness: 140}});
  return (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) scale(${p}) rotate(${rot}deg)`, fontFamily: FONT, fontWeight: 900, fontSize: size, letterSpacing: 3, color: fg, background: color, padding: '10px 26px', borderRadius: 40, whiteSpace: 'nowrap', boxShadow: '0 10px 30px rgba(0,0,0,0.35)'}}>{text}</div>
  );
};

/** local frame (inside a scene) at which the first word of line `li` matching `re` starts */
export const wordStart = (s: SceneT, li: number, re: RegExp): number => {
  const w = s.lines[li].words.find((x) => re.test(x.w));
  return (w ? w.s : s.lines[li].start) - s.from;
};
