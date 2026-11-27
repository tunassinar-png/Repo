import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Briefcase, C, Chip, Coin, FONT, Headline, Heart, Lantern, Layer, Moon, Person, SceneFade, SceneT, W, clamp, localStarts, ramp, useSp, wordStart} from './common';

type P = {s: SceneT};
export const CREDIT = 'Diinspirasikan daripada video oleh @hafiznaimraduan';   // set '' to remove

/* ───────── 7. BALANCE: duit vs takwa ───────── */
export const BalanceScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const lose = ramp(f, L[1] + 4, L[1] + 40);
  const back = ramp(f, L[2] + 24, L[2] + 80);
  const tilt = -8 * ramp(f, 6, 40) - 10 * lose + 20 * back;                  // degrees (negative = left side down)
  const th = (tilt * Math.PI) / 180;
  const bx = 540, by = 700, half = 330;
  const left = {x: bx - half * Math.cos(th), y: by - half * Math.sin(th)}, right = {x: bx + half * Math.cos(th), y: by + half * Math.sin(th)};
  const panY = 230;
  const coins = 2 + Math.floor(ramp(f, 10, L[1]) * 4 + lose * 3);
  const heartFall = ramp(f, L[1] + 6, L[1] + 44, (x) => x * x);
  const heartBack = sp(L[2] + 40, 9);
  const heartVisible = f < L[1] + 44 ? 1 - heartFall : f > L[2] + 40 ? Math.min(1, heartBack) : 0;
  const beam = ramp(f, L[2], L[2] + 30);
  const swap = ramp(f, L[2] - 6, L[2] + 8);
  const Pan: React.FC<{c: {x: number; y: number}}> = ({c}) => (
    <g>
      <line x1={c.x} y1={c.y} x2={c.x - 120} y2={c.y + panY} stroke={C.gold} strokeWidth="4" /><line x1={c.x} y1={c.y} x2={c.x + 120} y2={c.y + panY} stroke={C.gold} strokeWidth="4" />
      <path d={`M${c.x - 135} ${c.y + panY} Q${c.x} ${c.y + panY + 110} ${c.x + 135} ${c.y + panY} Z`} fill={C.goldDeep} stroke={C.gold} strokeWidth="5" strokeLinejoin="round" />
    </g>
  );
  return (
    <SceneFade dur={s.dur}>
      <div style={{opacity: 1 - swap}}><Headline lines={[{text: 'JANGAN LEPASKAN'}, {text: 'TAKWA', color: C.gold}]} start={4} size={88} top={215} /></div>
      <div style={{opacity: swap}}><Headline lines={[{text: 'REZEKI ITU'}, {text: 'DARI ALLAH', color: C.gold}]} start={L[2]} size={96} top={215} /></div>
      <Layer>
        <defs><linearGradient id="beam2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={C.gold} stopOpacity="0.6" /><stop offset="1" stopColor={C.gold} stopOpacity="0" /></linearGradient></defs>
        <polygon points="470,520 610,520 900,1180 180,1180" fill="url(#beam2)" opacity={beam} />
        {/* stand */}
        <rect x="528" y="700" width="24" height="470" rx="10" fill={C.goldDeep} /><rect x="400" y="1150" width="280" height="26" rx="13" fill={C.goldDeep} />
        <g transform={`rotate(${tilt} ${bx} ${by})`}><rect x={bx - half - 14} y={by - 10} width={half * 2 + 28} height="20" rx="10" fill={C.gold} /></g>
        <circle cx={bx} cy={by} r="26" fill={C.gold} stroke={C.goldDeep} strokeWidth="6" />
        <Pan c={left} /><Pan c={right} />
        {/* coins pile left */}
        {Array.from({length: coins}).map((_, i) => {
          const col = i % 3, row = Math.floor(i / 3);
          return <g key={i} transform={`translate(${left.x - 82 + col * 54 + (row % 2) * 24} ${left.y + panY + 18 - row * 38 - 66})`}><Coin size={70} /></g>;
        })}
        {/* heart (takwa) on right pan */}
        <g transform={`translate(${right.x - 55} ${right.y + panY - 100 + (f < L[2] + 36 ? heartFall * 420 : -(1 - Math.min(1, heartBack)) * 380)}) rotate(${f < L[2] + 36 ? heartFall * 80 : 0} 55 55)`} opacity={heartVisible}>
          <Heart size={110} color={C.mint} />
        </g>
        <Person x={140} y={1180} scale={0.0} />
      </Layer>
      <Chip text="DUIT" x={left.x} y={by + panY + 190} at={8} color={C.gold} size={34} />
      <Chip text="TAKWA" x={right.x} y={by + panY + 190} at={8} color={C.mint} size={34} />
      <div style={{opacity: beam}}><Chip text="DARIPADA ALLAH" x={540} y={560} at={L[2] + 6} color={C.cream} size={34} /></div>
    </SceneFade>
  );
};

/* ───────── 8. FORMULA: usaha + takwa = keberkatan ───────── */
export const FormulaScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const tUsaha = wordStart(s, 0, /usaha/i) - 6, tTakwa = L[1] - 2, tEq = wordStart(s, 1, /keberkatan/i) - 4, tPulse = wordStart(s, 1, /^takwa/i);
  const Card: React.FC<{y: number; h: number; at: number; label: string; sub: string; col: string; icon: React.ReactNode; big?: boolean}> = ({y, h, at, label, sub, col, icon, big}) => {
    const p = sp(at, 11);
    const pulse = big ? 1 + 0.025 * Math.sin(f / 7) * ramp(f, at + 20, at + 40) : 1;
    return (
      <div style={{position: 'absolute', left: 130, right: 130, top: y, height: h, borderRadius: 40, background: big ? `linear-gradient(135deg, ${C.goldDeep}, ${C.gold})` : 'rgba(0,0,0,0.34)', border: `4px solid ${col}`, transform: `scale(${p * pulse})`, opacity: Math.min(1, p * 1.5), display: 'flex', alignItems: 'center', gap: 30, padding: '0 44px', boxSizing: 'border-box', fontFamily: FONT, boxShadow: big ? '0 0 80px rgba(244,201,93,0.55)' : '0 14px 40px rgba(0,0,0,0.35)'}}>
        <div style={{width: 120, height: 120, display: 'grid', placeItems: 'center'}}>{icon}</div>
        <div>
          <div style={{fontSize: big ? 66 : 62, fontWeight: 900, letterSpacing: 2, color: big ? C.ink : col}}>{label}</div>
          <div style={{fontSize: 30, fontWeight: 600, color: big ? 'rgba(10,31,27,0.8)' : 'rgba(255,244,220,0.75)'}}>{sub}</div>
        </div>
      </div>
    );
  };
  const Sign: React.FC<{t: string; y: number; at: number}> = ({t, y, at}) => (
    <div style={{position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center', fontFamily: FONT, fontWeight: 900, fontSize: 90, color: C.gold, transform: `scale(${sp(at, 8)})`, lineHeight: 1}}>{t}</div>
  );
  return (
    <SceneFade dur={s.dur}>
      <Layer>
        <g transform="translate(8 250)" opacity={ramp(f, tEq, tEq + 20)}><Lantern size={110} glow={ramp(f, tEq, tEq + 30)} /></g>
        <g transform="translate(962 250)" opacity={ramp(f, tEq, tEq + 20)}><Lantern size={110} glow={ramp(f, tEq, tEq + 30)} /></g>
        {/* sparkles around result */}
        {Array.from({length: 14}).map((_, i) => {
          const a = (i / 14) * Math.PI * 2 + f * 0.01, r = 380 + Math.sin(f / 9 + i) * 30;
          return <circle key={i} cx={540 + Math.cos(a) * r} cy={1000 + Math.sin(a) * 190} r={4 + (i % 3) * 2} fill={C.gold} opacity={ramp(f, tEq + 10, tEq + 30) * (0.4 + 0.5 * Math.abs(Math.sin(f / 8 + i)))} />;
        })}
      </Layer>
      <Card y={250} h={190} at={tUsaha} label="USAHA" sub="Kerja & ikhtiar" col={C.sky} icon={<Briefcase size={100} />} />
      <Sign t="+" y={460} at={tTakwa} />
      <Card y={570} h={190} at={tTakwa} label="TAKWA" sub="Taat kepada Allah" col={C.mint} icon={<Heart size={100} color={C.mint} />} />
      <Sign t="=" y={780} at={tEq} />
      <Card y={890} h={250} at={tEq + 2} label="KEBERKATAN" sub="Rezeki yang mencukupi & menenangkan" col={C.gold} big icon={<svg width="110" height="110" viewBox="0 0 100 100"><path d="M50 6l12 30 32 3-24 21 8 32-28-17-28 17 8-32L6 39l32-3z" fill={C.ink} transform={`rotate(${Math.sin(f / 14) * 6} 50 50)`} /></svg>} />
      <div style={{position: 'absolute', left: 0, right: 0, top: 1160, textAlign: 'center', opacity: ramp(f, tPulse, tPulse + 10)}}><Chip text="USAHA + TAKWA" x={540} y={1190} at={tPulse} color={C.cream} size={30} /></div>
    </SceneFade>
  );
};

/* ───────── 9. END: kongsi → asbab kebaikan ───────── */
export const EndScene: React.FC<P> = ({s}) => {
  const f = useCurrentFrame(); const L = localStarts(s); const sp = useSp();
  const cx = 540, cy = 880;
  const l1 = [-90, 30, 150].map((a) => ({a, x: cx + Math.cos((a * Math.PI) / 180) * 200, y: cy + Math.sin((a * Math.PI) / 180) * 200}));
  const l2 = l1.flatMap((p) => [-26, 26].map((d) => ({x: cx + Math.cos(((p.a + d) * Math.PI) / 180) * 360, y: cy + Math.sin(((p.a + d) * Math.PI) / 180) * 360, px: p.x, py: p.y})));
  const spread = L[1] + 10;
  const Node: React.FC<{x: number; y: number; at: number; r?: number}> = ({x, y, at, r = 44}) => {
    const p = sp(at, 9); const lit = ramp(f, at + 6, at + 22);
    return (
      <g transform={`translate(${x} ${y}) scale(${p})`}>
        <circle r={r + 16} fill={C.gold} opacity={0.18 * lit} />
        <circle r={r} fill={lit > 0.5 ? C.gold : '#2d6a5d'} stroke={C.cream} strokeWidth="4" />
        <circle cy={-r * 0.22} r={r * 0.3} fill={C.ink} /><path d={`M${-r * 0.55} ${r * 0.62}a${r * 0.55} ${r * 0.5} 0 0 1 ${r * 1.1} 0z`} fill={C.ink} />
      </g>
    );
  };
  return (
    <SceneFade dur={s.dur}>
      <Headline lines={[{text: 'SEMOGA'}, {text: 'BERMANFAAT', color: C.gold}]} start={4} size={100} top={215} />
      <Layer>
        <g transform="translate(90 470)" opacity={ramp(f, 10, 30)}><Lantern size={96} glow={0.5 + 0.5 * Math.sin(f / 15)} /></g>
        <g transform="translate(880 480)" opacity={ramp(f, 10, 30)}><Moon size={110} /></g>
        {l1.map((p, i) => <line key={'a' + i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke={C.gold} strokeWidth="4" opacity={0.6 * ramp(f, spread + i * 8, spread + i * 8 + 14)} />)}
        {l2.map((p, i) => <line key={'b' + i} x1={p.px} y1={p.py} x2={p.x} y2={p.y} stroke={C.gold} strokeWidth="3" opacity={0.5 * ramp(f, spread + 30 + i * 6, spread + 44 + i * 6)} />)}
        {/* ripples from the origin */}
        {[0, 1, 2].map((i) => { const p = ((f * 1.2 + i * 40) % 120) / 120; return <circle key={i} cx={cx} cy={cy} r={60 + p * 300} fill="none" stroke={C.gold} strokeWidth="3" opacity={(1 - p) * 0.5 * ramp(f, L[0] + 20, L[0] + 40)} />; })}
        {l2.map((p, i) => <Node key={'n2' + i} x={p.x} y={p.y} at={spread + 36 + i * 6} r={34} />)}
        {l1.map((p, i) => <Node key={'n1' + i} x={p.x} y={p.y} at={spread + i * 8} r={40} />)}
        <Node x={cx} y={cy} at={L[0] + 14} r={58} />
        <g transform={`translate(${cx - 30} ${cy + 78 + 0}) scale(${sp(L[0] + 24, 9)})`}><Heart size={60} color={C.coral} /></g>
      </Layer>
      <Chip text="KONGSIKAN" x={540} y={1240} at={L[0] + 20} color={C.gold} size={40} />
      {CREDIT && <div style={{position: 'absolute', left: 60, right: 60, top: 1700, textAlign: 'center', fontFamily: FONT, fontSize: 26, fontWeight: 600, color: 'rgba(255,244,220,0.6)', opacity: ramp(f, L[2], L[2] + 20)}}>{CREDIT}</div>}
    </SceneFade>
  );
};
