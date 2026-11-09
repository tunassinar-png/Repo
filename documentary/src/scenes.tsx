import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, FONT} from './theme';
import {clamp, ramp, SceneFade, Typewriter, WordReveal} from './common';

const STAGE_X = 140; // left edge of main stage (popups live on the right)
const Stage: React.FC<{children: React.ReactNode; top?: number}> = ({children, top = 170}) => (
  <div style={{position: 'absolute', left: STAGE_X, top, width: 1010, fontFamily: FONT}}>{children}</div>
);
const fadeBetween = (f: number, a: number, b: number, fade = 12) =>
  interpolate(f, [a, a + fade, b - fade, b], [0, 1, 1, 0], clamp);

const Sparkle: React.FC<{x: number; y: number; size: number; delay?: number; color?: string}> = ({x, y, size, delay = 0, color = C.gold}) => {
  const f = useCurrentFrame();
  const s = Math.max(0, Math.sin((f - delay) / 9)) ;
  return (
    <svg width={size} height={size} viewBox="-10 -10 20 20" style={{position: 'absolute', left: x - size / 2, top: y - size / 2, transform: `scale(${s}) rotate(${f * 2}deg)`, opacity: s}}>
      <path d="M0 -10 Q1 -1 10 0 Q1 1 0 10 Q-1 1 -10 0 Q-1 -1 0 -10Z" fill={color} />
    </svg>
  );
};

/* ───────── 1. TITLE ───────── */
export const TitleScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  return (
    <SceneFade dur={dur}>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', fontFamily: FONT}}>
        {[0, 1, 2].map((i) => {
          const p = ((f + i * 40) % 120) / 120;
          return <div key={i} style={{position: 'absolute', width: 300 + p * 1100, height: 300 + p * 1100, borderRadius: '50%', border: `2px solid rgba(255,210,122,${0.35 * (1 - p)})`}} />;
        })}
        <div style={{opacity: ramp(f, 4, 22), transform: `translateY(${(1 - ramp(f, 4, 22)) * -20}px)`, fontSize: 24, fontWeight: 800, letterSpacing: 9, color: C.gold, border: `1.5px solid ${C.gold}`, borderRadius: 40, padding: '10px 30px', marginBottom: 46}}>
          DOKUMENTARI PENDEK · 1 MINIT
        </div>
        <WordReveal text="Apa akan jadi sekiranya" start={16} size={72} weight={600} color="#e9dcf7" stagger={5} />
        <WordReveal text="semua wanita cantik" start={42} size={156} stagger={7} hi={['wanita', 'cantik']} style={{marginTop: 6}} />
        <WordReveal text="di dunia ni?" start={70} size={112} stagger={7} />
        <Sparkle x={420} y={330} size={60} delay={40} />
        <Sparkle x={1500} y={420} size={44} delay={55} color={C.rose} />
        <Sparkle x={1380} y={760} size={64} delay={70} />
        <Sparkle x={520} y={800} size={38} delay={85} color={C.rose} />
      </AbsoluteFill>
    </SceneFade>
  );
};

/* ───────── 2. INTRO ───────── */
export const IntroScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const count = Math.round(interpolate(f, [60, 150], [0, 400], {...clamp, easing: Easing.out(Easing.cubic)}));
  return (
    <SceneFade dur={dur}>
      <Stage top={190}>
        <Typewriter text="Sejak azali, kecantikan dianggap anugerah yang istimewa." start={8} cps={26} size={58} weight={700} />
        <div style={{marginTop: 34, opacity: ramp(f, 55, 75)}}>
          <Typewriter text="Kita sanggup habiskan masa, wang dan tenaga untuk mengejarnya." start={70} cps={30} size={36} color={C.mute} />
        </div>
        <div style={{marginTop: 70, display: 'flex', alignItems: 'baseline', gap: 18, opacity: ramp(f, 52, 70), transform: `translateY(${(1 - ramp(f, 52, 70)) * 30}px)`}}>
          <span style={{fontSize: 40, fontWeight: 700, color: C.gold}}>USD</span>
          <span style={{fontSize: 150, fontWeight: 900, letterSpacing: -4, background: `linear-gradient(90deg, ${C.gold}, ${C.rose})`, WebkitBackgroundClip: 'text', color: 'transparent', fontVariantNumeric: 'tabular-nums'}}>{count}+</span>
          <span style={{fontSize: 44, fontWeight: 700, color: C.cream}}>bilion</span>
        </div>
        <div style={{fontSize: 28, color: C.mute, fontWeight: 500, opacity: ramp(f, 100, 120)}}>nilai industri kecantikan dunia setiap tahun</div>
      </Stage>
    </SceneFade>
  );
};

/* ───────── 3. IMAGINE ───────── */
const Person: React.FC<{i: number; f: number; cx: number; cy: number}> = ({i, f, cx, cy}) => {
  const col = i % 12, row = Math.floor(i / 12);
  const dist = Math.hypot(col - 5.5, (row - 2) * 1.8);
  const p = ramp(f, 100 + dist * 9, 135 + dist * 9, Easing.inOut(Easing.cubic));
  const hue0 = 260 + random(`h${i}`) * 100;
  const sc0 = 0.72 + random(`sc${i}`) * 0.5;
  const sc = sc0 + (1 - sc0) * p;
  const pop = spring({frame: f - 10 - i * 0.8, fps: 30, config: {damping: 12}});
  const fill = p < 0.5 ? `hsl(${hue0}, 28%, ${34 + random(`l${i}`) * 22}%)` : C.gold;
  const glow = p;
  return (
    <div style={{position: 'absolute', left: cx, top: cy, width: 88, height: 100, transform: `scale(${pop * sc * 0.93})`, filter: `drop-shadow(0 0 ${glow * 16}px rgba(255,210,122,${glow * 0.8}))`}}>
      <svg width="88" height="100" viewBox="0 0 88 100">
        <circle cx="44" cy="30" r="17" fill={fill} />
        <path d="M14 92c0-22 13-34 30-34s30 12 30 34z" fill={fill} />
        {p > 0.6 && <path d="M70 12 Q71 20 79 21 Q71 22 70 30 Q69 22 61 21 Q69 20 70 12Z" fill="#fff" opacity={0.5 + 0.5 * Math.sin(f / 6 + i)} />}
      </svg>
    </div>
  );
};
export const ImagineScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  return (
    <SceneFade dur={dur}>
      <Stage top={150}>
        <div style={{position: 'relative', height: 190}}>
          <div style={{position: 'absolute', inset: 0, opacity: fadeBetween(f, 0, 100)}}>
            <WordReveal text="Sekarang, bayangkan..." size={84} start={6} align="left" />
          </div>
          <div style={{position: 'absolute', inset: 0, opacity: ramp(f, 100, 118)}}>
            <WordReveal text="Esok pagi, setiap wanita di dunia ini cantik." size={64} start={104} align="left" hi={['cantik']} />
          </div>
        </div>
      </Stage>
      <div style={{position: 'absolute', left: STAGE_X, top: 410}}>
        {Array.from({length: 60}).map((_, i) => (
          <Person key={i} i={i} f={f} cx={(i % 12) * 83} cy={Math.floor(i / 12) * 100} />
        ))}
      </div>
      <div style={{position: 'absolute', left: STAGE_X, top: 930, fontFamily: FONT, fontSize: 28, fontWeight: 600, letterSpacing: 2, color: C.mute, opacity: ramp(f, 190, 215)}}>
        Semuanya sama bercahaya. <span style={{color: C.gold}}>Tiada yang menonjol.</span>
      </div>
    </SceneFade>
  );
};

/* ───────── 4. VALUE ───────── */
export const ValueScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const N = 9;
  const star = (size: number, fill: string) => (
    <svg width={size} height={size} viewBox="0 0 24 24"><path d="M12 2l3 6.6 7 .8-5.2 4.8 1.5 7L12 17.6 5.7 21.2l1.5-7L2 9.4l7-.8z" fill={fill} /></svg>
  );
  const badge = f < 130 ? 'ISTIMEWA' : f < 200 ? 'ISTIMEWA?' : 'SAMA';
  const badgeCol = f < 130 ? C.gold : f < 200 ? C.rose : C.mute;
  return (
    <SceneFade dur={dur}>
      <Stage top={150}>
        <div style={{position: 'relative', height: 230}}>
          <div style={{position: 'absolute', inset: 0, opacity: fadeBetween(f, 0, 110)}}>
            <WordReveal text="Cantik dihargai kerana ia dianggap jarang." size={60} start={6} align="left" hi={['jarang']} />
          </div>
          <div style={{position: 'absolute', inset: 0, opacity: fadeBetween(f, 110, 205)}}>
            <WordReveal text="Tapi bila semua orang memilikinya..." size={60} start={114} align="left" />
          </div>
          <div style={{position: 'absolute', inset: 0, opacity: ramp(f, 205, 222)}}>
            <WordReveal text="cantik tak lagi jadi pembeza." size={72} start={208} align="left" hi={['pembeza.', 'pembeza']} />
          </div>
        </div>
      </Stage>
      <div style={{position: 'absolute', left: STAGE_X, top: 520, width: 1010, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
        {Array.from({length: N}).map((_, i) => {
          const mid = i === 4;
          const turn = ramp(f, 110 + Math.abs(i - 4) * 9, 128 + Math.abs(i - 4) * 9);
          const pop = spring({frame: f - 8 - i * 3, fps: 30, config: {damping: 11}});
          const big = mid ? 1.7 - 0.7 * ramp(f, 130, 190) : 1;
          const gold = mid || turn > 0.5;
          return (
            <div key={i} style={{transform: `scale(${pop * big})`, transformOrigin: 'bottom center', filter: gold ? `drop-shadow(0 0 ${mid ? 28 * (1 - ramp(f, 130, 190) * 0.6) : 12}px rgba(255,210,122,0.9))` : 'none', opacity: gold ? 1 : 0.9}}>
              {star(100, gold ? C.gold : '#5d4a74')}
            </div>
          );
        })}
      </div>
      <div style={{position: 'absolute', left: STAGE_X + 1010 / 2 - 150, top: 700, width: 300, textAlign: 'center', fontFamily: FONT}}>
        <div style={{fontSize: 22, fontWeight: 800, letterSpacing: 6, color: badgeCol, border: `1.5px solid ${badgeCol}`, borderRadius: 30, padding: '8px 0', opacity: ramp(f, 40, 60)}}>{badge}</div>
      </div>
      <div style={{position: 'absolute', left: STAGE_X, top: 820, width: 1010, textAlign: 'center', fontFamily: FONT, fontSize: 46, fontWeight: 800, color: C.cream, opacity: ramp(f, 235, 255)}}>
        <span style={{color: C.gold}}>Semua istimewa</span> = <span style={{color: C.rose}}>tiada yang istimewa</span>
      </div>
    </SceneFade>
  );
};

/* ───────── 5. INDUSTRY ───────── */
export const IndustryScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const bars = [
    {l: 'Kosmetik', a: 0.9, b: 0.28}, {l: 'Estetik', a: 0.72, b: 0.22}, {l: 'Penapis foto', a: 0.95, b: 0.3}, {l: 'Diet', a: 0.6, b: 0.15},
    {l: 'Pangkat', a: 0, b: 0.0, n: 0.7}, {l: 'Gaya hidup', a: 0, b: 0, n: 0.85}, {l: 'Ilmu', a: 0, b: 0, n: 0.62},
  ];
  const H = 430;
  return (
    <SceneFade dur={dur}>
      <Stage top={150}>
        <div style={{position: 'relative', height: 200}}>
          <div style={{position: 'absolute', inset: 0, opacity: fadeBetween(f, 0, 200, 14)}}>
            <WordReveal text="Industri kecantikan hidup daripada rasa 'kurang cantik'." size={54} start={6} align="left" hi={['kurang']} />
          </div>
          <div style={{position: 'absolute', inset: 0, opacity: ramp(f, 200, 218)}}>
            <WordReveal text="Tapi manusia tetap mahu membezakan diri." size={56} start={204} align="left" hi={['membezakan']} />
          </div>
        </div>
      </Stage>
      <div style={{position: 'absolute', left: STAGE_X, top: 390, width: 1010, height: H + 90, fontFamily: FONT}}>
        <div style={{position: 'absolute', left: 0, right: 0, top: H, height: 2, background: C.line}} />
        <div style={{position: 'absolute', left: 0, top: -30, fontSize: 22, color: C.mute, fontWeight: 700, letterSpacing: 3, opacity: ramp(f, 20, 40)}}>PERMINTAAN (JANGKAAN)</div>
        {bars.map((b, i) => {
          const old = i < 4;
          const x = i * 140;
          let h = 0;
          if (old) {
            const grow = ramp(f, 20 + i * 8, 80 + i * 8, Easing.out(Easing.back(1.2)));
            const fall = ramp(f, 120 + i * 6, 180 + i * 6, Easing.inOut(Easing.cubic));
            h = (b.a * grow + (b.b - b.a) * fall * grow) * H;
          } else {
            h = (b.n ?? 0) * H * ramp(f, 215 + (i - 4) * 12, 270 + (i - 4) * 12, Easing.out(Easing.back(1.2)));
          }
          const fallen = old && f > 150;
          return (
            <div key={i} style={{position: 'absolute', left: x, top: H - h, width: 104, height: h, borderRadius: '14px 14px 0 0',
              background: old ? (fallen ? `linear-gradient(180deg, ${C.rose}, #7a2a62)` : `linear-gradient(180deg, ${C.gold}, ${C.goldDeep})`) : `linear-gradient(180deg, #8ff5d0, #1fa384)`,
              boxShadow: old ? '0 0 30px rgba(255,126,182,0.25)' : '0 0 34px rgba(143,245,208,0.4)'}}>
              {old && f > 170 && h > 30 && <div style={{position: 'absolute', top: -58, width: '100%', textAlign: 'center', fontSize: 44, fontWeight: 900, color: C.rose, opacity: ramp(f, 170 + i * 6, 190 + i * 6)}}>?</div>}
              {!old && h > 40 && <div style={{position: 'absolute', top: -52, width: '100%', textAlign: 'center', fontSize: 40, fontWeight: 900, color: '#8ff5d0'}}>↑</div>}
              <div style={{position: 'absolute', top: H - (H - h) + 14, width: 140, left: -18, textAlign: 'center', fontSize: 20, fontWeight: 600, color: C.mute, whiteSpace: 'nowrap'}}>{b.l}</div>
            </div>
          );
        })}
        <div style={{position: 'absolute', left: 4 * 140 - 19, top: -30, width: 3, height: H + 40, background: 'repeating-linear-gradient(180deg, rgba(255,255,255,0.4) 0 8px, transparent 8px 16px)', opacity: ramp(f, 205, 220)}} />
      </div>
    </SceneFade>
  );
};

/* ───────── 6. NEW STANDARD ───────── */
export const NewStdScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const chips = ['Ilmu', 'Akhlak', 'Kemahiran', 'Budi bahasa', 'Keberanian', 'Humor', 'Kerjaya', 'Kejujuran'];
  const cx = STAGE_X + 540, cy = 560;
  return (
    <SceneFade dur={dur}>
      <Stage top={140}>
        <WordReveal text="Bila rupa tak lagi membezakan..." size={56} start={6} align="left" />
      </Stage>
      <div style={{position: 'absolute', left: cx - 190, top: cy - 190, width: 380, height: 380, borderRadius: '50%', border: `2px dashed ${C.gold}`, transform: `rotate(${f * 0.8}deg) scale(${ramp(f, 10, 40)})`, opacity: 0.7}} />
      <div style={{position: 'absolute', left: cx - 150, top: cy - 150, width: 300, height: 300, borderRadius: '50%', background: 'radial-gradient(circle, rgba(255,210,122,0.35), rgba(255,126,182,0.12) 70%)', display: 'grid', placeItems: 'center', textAlign: 'center', fontFamily: FONT, transform: `scale(${spring({frame: f - 14, fps: 30, config: {damping: 12}})})`}}>
        <div>
          <div style={{fontSize: 24, fontWeight: 800, letterSpacing: 5, color: C.gold}}>UKURAN</div>
          <div style={{fontSize: 56, fontWeight: 900, color: C.cream, letterSpacing: -1}}>BAHARU</div>
        </div>
      </div>
      {chips.map((c, i) => {
        const ang = (i / chips.length) * Math.PI * 2 + f * 0.012 - Math.PI / 2;
        const x = cx + Math.cos(ang) * 430, y = cy + Math.sin(ang) * 235;
        const p = spring({frame: f - 40 - i * 7, fps: 30, config: {damping: 10, stiffness: 120}});
        return (
          <div key={c} style={{position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) scale(${p})`, fontFamily: FONT, fontSize: 30, fontWeight: 700, color: '#2a0f3d', background: `linear-gradient(135deg, ${i % 2 ? C.gold : '#ffb0d3'}, ${i % 2 ? '#ffe9b8' : C.rose})`, padding: '12px 28px', borderRadius: 40, boxShadow: '0 10px 30px rgba(0,0,0,0.4)', whiteSpace: 'nowrap'}}>{c}</div>
        );
      })}
      <div style={{position: 'absolute', left: STAGE_X, top: 920, width: 1010, textAlign: 'center', fontFamily: FONT, fontSize: 36, fontWeight: 600, color: C.mute, opacity: ramp(f, 150, 175)}}>
        ...manusia akan mula menilai <span style={{color: C.gold, fontWeight: 800}}>apa yang ada di dalam</span>.
      </div>
    </SceneFade>
  );
};

/* ───────── 7. OUTRO ───────── */
export const OutroScene: React.FC<{dur: number}> = ({dur}) => {
  const f = useCurrentFrame();
  const content = 1 - ramp(f, 160, 176);
  const end = ramp(f, 176, 196);
  return (
    <SceneFade dur={dur}>
      <div style={{opacity: content}}>
        <Stage top={250}>
          <WordReveal text="Mungkin dunia tak jadi lebih baik." size={62} start={8} align="left" />
          <div style={{height: 30}} />
          <WordReveal text="Tapi kita berhenti bertanya, 'siapa paling cantik?'" size={58} start={52} align="left" weight={600} color="#e9dcf7" />
          <div style={{height: 30}} />
          <WordReveal text="dan mula bertanya, 'siapa paling bermakna?'" size={62} start={100} align="left" hi={["bermakna'", 'bermakna']} />
        </Stage>
      </div>
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', fontFamily: FONT, opacity: end, transform: `scale(${0.94 + end * 0.06})`}}>
        <div style={{fontSize: 30, fontWeight: 800, letterSpacing: 8, color: C.gold, marginBottom: 24}}>APA PENDAPAT ANDA?</div>
        <div style={{fontSize: 118, fontWeight: 900, textAlign: 'center', lineHeight: 1.1, background: `linear-gradient(90deg, ${C.gold}, ${C.rose})`, WebkitBackgroundClip: 'text', color: 'transparent'}}>Cantik itu apa?</div>
        <div style={{fontSize: 34, color: C.mute, marginTop: 28, fontWeight: 500}}>Tinggalkan komen anda di bawah.</div>
      </AbsoluteFill>
    </SceneFade>
  );
};
