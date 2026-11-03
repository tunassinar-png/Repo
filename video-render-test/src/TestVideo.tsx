import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export const TestVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, width, durationInFrames} = useVideoConfig();

  const titleIn = spring({frame, fps, config: {damping: 14}});
  const subOpacity = interpolate(frame, [30, 55], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const circleX = interpolate(frame, [0, durationInFrames], [200, width - 200]);
  const rectRotate = interpolate(frame, [0, durationInFrames], [0, 360]);
  const progress = interpolate(frame, [0, durationInFrames - 1], [0, 1]);
  const fadeOut = interpolate(frame, [130, 149], [1, 0], {extrapolateLeft: 'clamp'});

  return (
    <AbsoluteFill style={{background: 'linear-gradient(135deg, #0f172a, #1e3a8a)', fontFamily: 'sans-serif', opacity: fadeOut}}>
      <div style={{position: 'absolute', top: 260, width: '100%', textAlign: 'center', color: 'white',
        fontSize: 140, fontWeight: 800, transform: `scale(${titleIn})`}}>
        Render Test OK
      </div>
      <div style={{position: 'absolute', top: 440, width: '100%', textAlign: 'center', color: '#93c5fd',
        fontSize: 56, opacity: subOpacity}}>
        Remotion + Node.js + ffmpeg
      </div>
      <div style={{position: 'absolute', top: 700, left: circleX - 70, width: 140, height: 140,
        borderRadius: '50%', background: '#f59e0b'}} />
      <div style={{position: 'absolute', top: 730, left: 140, width: 100, height: 100,
        background: '#10b981', transform: `rotate(${rectRotate}deg)`}} />
      <div style={{position: 'absolute', bottom: 80, left: 160, width: width - 320, height: 16,
        background: 'rgba(255,255,255,0.2)', borderRadius: 8}}>
        <div style={{width: `${progress * 100}%`, height: '100%', background: '#f8fafc', borderRadius: 8}} />
      </div>
    </AbsoluteFill>
  );
};
