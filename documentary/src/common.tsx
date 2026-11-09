import React from 'react';
import {AbsoluteFill, Easing, interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import timeline from './timeline.json';
import {C, FONT} from './theme';

export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** progress 0..1 between two local frames with easing */
export const ramp = (frame: number, a: number, b: number, easing = Easing.out(Easing.cubic)) =>
  interpolate(frame, [a, b], [0, 1], {...clamp, easing});

/** Animated background: drifting gradient + glowing orbs + floating particles */
export const Background: React.FC<{hue?: number}> = ({hue = 0}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const t = frame / 30;
  return (
    <AbsoluteFill style={{background: `radial-gradient(ellipse at ${50 + Math.sin(t * 0.3) * 15}% ${40 + Math.cos(t * 0.25) * 12}%, ${C.bg3} 0%, ${C.bg2} 40%, ${C.bg1} 100%)`, filter: `hue-rotate(${hue}deg)`}}>
      {[0, 1, 2].map((i) => (
        <div key={i} style={{
          position: 'absolute', width: 700, height: 700, borderRadius: '50%',
          left: width * (0.15 + i * 0.35) + Math.sin(t * 0.4 + i * 2) * 120 - 350,
          top: height * (0.2 + (i % 2) * 0.5) + Math.cos(t * 0.35 + i) * 90 - 350,
          background: `radial-gradient(circle, ${i === 1 ? 'rgba(255,210,122,0.16)' : 'rgba(255,126,182,0.18)'}, transparent 65%)`,
          filter: 'blur(20px)',
        }} />
      ))}
      <svg width={width} height={height} style={{position: 'absolute', inset: 0}}>
        {Array.from({length: 46}).map((_, i) => {
          const x = random(`x${i}`) * width;
          const speed = 8 + random(`s${i}`) * 26;
          const y = (height + 40 - ((t * speed + random(`y${i}`) * height) % (height + 80)));
          const r = 1.5 + random(`r${i}`) * 3.5;
          const tw = 0.35 + 0.65 * Math.abs(Math.sin(t * (0.6 + random(`t${i}`) * 1.5) + i));
          return <circle key={i} cx={x + Math.sin(t + i) * 14} cy={y} r={r} fill={i % 3 ? C.gold : C.rose} opacity={tw * 0.55} />;
        })}
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)'}} />
    </AbsoluteFill>
  );
};

/** Text that reveals word by word, rising + fading */
export const WordReveal: React.FC<{text: string; start?: number; size: number; weight?: number; color?: string; gap?: number; stagger?: number; align?: 'left' | 'center'; style?: React.CSSProperties; hi?: string[]}> =
  ({text, start = 0, size, weight = 800, color = C.cream, stagger = 4, align = 'center', style, hi = []}) => {
    const frame = useCurrentFrame();
    const {fps} = useVideoConfig();
    const words = text.split(' ');
    return (
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: align === 'center' ? 'center' : 'flex-start', gap: `0 ${size * 0.28}px`, fontFamily: FONT, fontSize: size, fontWeight: weight, color, lineHeight: 1.18, letterSpacing: -size * 0.01, ...style}}>
        {words.map((w, i) => {
          const p = spring({frame: frame - start - i * stagger, fps, config: {damping: 16, stiffness: 110}});
          const isHi = hi.includes(w.replace(/[.,?!]/g, ''));
          return (
            <span key={i} style={{display: 'inline-block', opacity: Math.min(1, p * 1.4), transform: `translateY(${(1 - p) * 40}px) scale(${0.92 + p * 0.08})`, filter: `blur(${(1 - Math.min(1, p)) * 8}px)`,
              ...(isHi ? {background: `linear-gradient(90deg, ${C.gold}, ${C.rose})`, WebkitBackgroundClip: 'text', color: 'transparent'} : {})}}>
              {w}
            </span>
          );
        })}
      </div>
    );
  };

/** Typewriter with blinking cursor */
export const Typewriter: React.FC<{text: string; start?: number; cps?: number; size: number; color?: string; weight?: number; style?: React.CSSProperties}> =
  ({text, start = 0, cps = 22, size, color = C.cream, weight = 500, style}) => {
    const frame = useCurrentFrame();
    const n = Math.max(0, Math.min(text.length, Math.floor(((frame - start) / 30) * cps)));
    const done = n >= text.length;
    const blink = done ? (Math.floor(frame / 15) % 2 === 0 && frame - start < (text.length / cps) * 30 + 45) : true;
    return (
      <div style={{fontFamily: FONT, fontSize: size, fontWeight: weight, color, lineHeight: 1.4, ...style}}>
        {text.slice(0, n)}
        <span style={{display: 'inline-block', width: size * 0.08, height: size * 0.9, background: C.gold, marginLeft: 6, verticalAlign: 'middle', opacity: blink ? 1 : 0}} />
      </div>
    );
  };

/** Scene wrapper: fade/scale in and out */
export const SceneFade: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 14, dur - 14, dur], [0, 1, 1, 0], clamp);
  const s = interpolate(frame, [0, dur], [1.0, 1.045], clamp);
  return <AbsoluteFill style={{opacity: o, transform: `scale(${s})`}}>{children}</AbsoluteFill>;
};

const Icon: React.FC<{name: string; size?: number}> = ({name, size = 40}) => {
  const p = {fill: 'none', stroke: '#2a0f3d', strokeWidth: 2.2, strokeLinecap: 'round', strokeLinejoin: 'round'} as const;
  const paths: Record<string, React.ReactNode> = {
    coin: <><circle cx="12" cy="12" r="9" {...p} /><path d="M12 7v10M9.5 9.5c0-1 1.2-1.7 2.5-1.7s2.5.7 2.5 1.7-1.2 1.5-2.5 1.8-2.5.8-2.5 1.8 1.2 1.7 2.5 1.7 2.5-.7 2.5-1.7" {...p} /></>,
    globe: <><circle cx="12" cy="12" r="9" {...p} /><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" {...p} /></>,
    q: <><circle cx="12" cy="12" r="9" {...p} /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 1-1 1.7M12 17h.01" {...p} /></>,
    star: <path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" {...p} />,
    eye: <><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z" {...p} /><circle cx="12" cy="12" r="3" {...p} /></>,
    down: <path d="M3 6l6 6 4-4 8 8M21 11v5h-5" {...p} />,
    bolt: <path d="M13 2L4 14h7l-1 8 9-12h-7z" {...p} />,
    clock: <><circle cx="12" cy="12" r="9" {...p} /><path d="M12 7v5l3 2" {...p} /></>,
    spark: <path d="M12 3v5M12 16v5M3 12h5M16 12h5M6 6l3 3M15 15l3 3M18 6l-3 3M9 15l-3 3" {...p} />,
    heart: <path d="M12 20s-8-4.6-8-10.4A4.6 4.6 0 0 1 12 7a4.6 4.6 0 0 1 8 2.6C20 15.4 12 20 12 20z" {...p} />,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24">{paths[name]}</svg>;
};

export type PopupData = (typeof timeline.popups)[number];

/** Notification-style pop-up card: springs in, shows a timer bar, then pops out */
export const Popup: React.FC<{data: PopupData; index: number}> = ({data, index}) => {
  const frame = useCurrentFrame() - data.at;
  const {fps} = useVideoConfig();
  if (frame < 0 || frame > data.dur + 20) return null;
  const inP = spring({frame, fps, config: {damping: 11, stiffness: 140, mass: 0.7}});
  const outP = interpolate(frame, [data.dur, data.dur + 14], [0, 1], {...clamp, easing: Easing.in(Easing.cubic)});
  const top = index % 2 === 0;
  const scale = (0.4 + inP * 0.6) * (1 - outP * 0.25);
  const opacity = Math.min(1, inP * 2) * (1 - outP);
  const bar = interpolate(frame, [8, data.dur], [100, 0], clamp);
  const typed = Math.floor(interpolate(frame, [10, 10 + data.text.length * 0.9], [0, data.text.length], clamp));
  return (
    <div style={{position: 'absolute', top: top ? 120 : 'auto', bottom: top ? 'auto' : 170, right: 100, width: 640,
      transform: `translateX(${(1 - inP) * 160}px) scale(${scale})`, transformOrigin: top ? 'top right' : 'bottom right', opacity, fontFamily: FONT}}>
      <div style={{background: 'rgba(24,10,38,0.78)', backdropFilter: 'blur(14px)', border: '1.5px solid rgba(255,210,122,0.5)', borderRadius: 28, padding: '26px 30px 30px', boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(255,126,182,0.25)', overflow: 'hidden', position: 'relative'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 18, marginBottom: 14}}>
          <div style={{width: 68, height: 68, borderRadius: 20, background: `linear-gradient(135deg, ${C.gold}, ${C.rose})`, display: 'grid', placeItems: 'center', transform: `rotate(${(1 - inP) * -25}deg)`}}>
            <Icon name={data.icon} size={40} />
          </div>
          <div>
            <div style={{fontSize: 20, fontWeight: 800, letterSpacing: 4, color: C.gold}}>{data.tag}</div>
            <div style={{fontSize: 32, fontWeight: 800, color: C.cream, lineHeight: 1.15, marginTop: 2}}>{data.title}</div>
          </div>
        </div>
        <div style={{fontSize: 27, fontWeight: 500, color: '#e6d9f2', lineHeight: 1.4, minHeight: 76}}>{data.text.slice(0, typed)}</div>
        <div style={{position: 'absolute', left: 0, bottom: 0, height: 6, width: `${bar}%`, background: `linear-gradient(90deg, ${C.gold}, ${C.rose})`}} />
      </div>
    </div>
  );
};

/** Persistent HUD: chapter label, timecode, progress bar */
export const Hud: React.FC = () => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const scene = [...timeline.scenes].reverse().find((s) => frame >= s.from) ?? timeline.scenes[0];
  const sec = Math.min(60, Math.floor(frame / 30));
  const tc = `00:${String(sec).padStart(2, '0')} / 01:00`;
  const sf = frame - scene.from;
  const o = interpolate(frame, [0, 20, timeline.total - 25, timeline.total - 8], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{opacity: o, fontFamily: FONT}}>
      <div style={{position: 'absolute', left: 70, top: 56, display: 'flex', alignItems: 'center', gap: 14}}>
        <div style={{width: 12, height: 12, borderRadius: 6, background: C.rose, boxShadow: `0 0 14px ${C.rose}`, opacity: 0.6 + 0.4 * Math.sin(frame / 6)}} />
        <div key={scene.id} style={{fontSize: 22, fontWeight: 800, letterSpacing: 5, color: C.cream, opacity: ramp(sf, 0, 12), transform: `translateX(${(1 - ramp(sf, 0, 12)) * -20}px)`}}>{scene.label}</div>
      </div>
      <div style={{position: 'absolute', right: 70, bottom: 56, fontSize: 22, fontWeight: 600, color: C.mute, letterSpacing: 3, fontVariantNumeric: 'tabular-nums'}}>{tc}</div>
      <div style={{position: 'absolute', left: 70, bottom: 66, width: width - 140 - 230, height: 6, borderRadius: 3, background: C.line}}>
        <div style={{width: `${(frame / timeline.total) * 100}%`, height: '100%', borderRadius: 3, background: `linear-gradient(90deg, ${C.rose}, ${C.gold})`}} />
        {timeline.scenes.slice(1).map((s) => (
          <div key={s.id} style={{position: 'absolute', left: `${(s.from / timeline.total) * 100}%`, top: -4, width: 3, height: 14, background: 'rgba(255,255,255,0.35)'}} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
