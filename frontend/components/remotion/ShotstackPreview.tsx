'use client';

import React from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';

interface ShotstackClip {
  asset: {
    type: string;
    src?: string;
    text?: string;
    html?: string;
    width?: number;
    height?: number;
  };
  start: number;
  length: number;
  offset?: { x: number; y: number };
  scale?: number;
  opacity?: number;
  transition?: {
    in?: { type: string; duration: number };
    out?: { type: string; duration: number };
  };
  fit?: string;
  position?: string;
}

interface ShotstackTrack {
  clips: ShotstackClip[];
}

interface ShotstackTimeline {
  tracks?: ShotstackTrack[];
  background?: string;
}

interface ShotstackEdit {
  timeline?: ShotstackTimeline;
  output?: { resolution?: string };
}

export interface ShotstackPreviewProps {
  editJson: ShotstackEdit | null;
}

const TRACK_COLORS: Record<string, string> = {
  video: '#3B82F6',
  image: '#10B981',
  audio: '#F59E0B',
  html: '#8B5CF6',
  title: '#8B5CF6',
  text: '#8B5CF6',
  'luma': '#6B7280',
};

function getClipColor(type: string): string {
  return TRACK_COLORS[type] || '#6B7280';
}

function computeOpacity(
  clip: ShotstackClip,
  currentTimeSec: number
): number {
  let opacity = clip.opacity ?? 1;
  const clipEnd = clip.start + clip.length;

  if (clip.transition?.in) {
    const fadeInEnd = clip.start + clip.transition.in.duration;
    if (currentTimeSec < fadeInEnd) {
      const progress = (currentTimeSec - clip.start) / clip.transition.in.duration;
      opacity *= Math.max(0, Math.min(1, progress));
    }
  }

  if (clip.transition?.out) {
    const fadeOutStart = clipEnd - clip.transition.out.duration;
    if (currentTimeSec > fadeOutStart) {
      const progress = (clipEnd - currentTimeSec) / clip.transition.out.duration;
      opacity *= Math.max(0, Math.min(1, progress));
    }
  }

  return opacity;
}

function RenderClip({
  clip,
  currentTimeSec,
}: {
  clip: ShotstackClip;
  currentTimeSec: number;
}) {
  const opacity = computeOpacity(clip, currentTimeSec);
  const type = clip.asset.type;

  if (type === 'image' && clip.asset.src) {
    return (
      <div style={{ width: '100%', height: '100%', opacity }}>
        <img
          src={clip.asset.src}
          alt=""
          style={{
            width: '100%',
            height: '100%',
            objectFit: (clip.fit as any) || 'cover',
          }}
        />
      </div>
    );
  }

  if (type === 'video') {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          opacity,
          background: `linear-gradient(135deg, ${getClipColor('video')}CC, ${getClipColor('video')}88)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          color: '#fff',
          fontSize: 14,
          fontFamily: 'monospace',
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 8 }}>&#9654;</div>
        <div>Video Clip</div>
        {clip.asset.src && (
          <div style={{ fontSize: 10, opacity: 0.7, maxWidth: '80%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 4 }}>
            {clip.asset.src.split('/').pop()}
          </div>
        )}
      </div>
    );
  }

  if (type === 'html' && clip.asset.html) {
    return (
      <div
        style={{ width: '100%', height: '100%', opacity }}
        dangerouslySetInnerHTML={{ __html: clip.asset.html }}
      />
    );
  }

  if ((type === 'title' || type === 'text') && clip.asset.text) {
    return (
      <div
        style={{
          width: '100%',
          height: '100%',
          opacity,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          fontSize: 24,
          fontWeight: 'bold',
          textAlign: 'center',
          padding: 20,
          textShadow: '0 2px 4px rgba(0,0,0,0.5)',
        }}
      >
        {clip.asset.text}
      </div>
    );
  }

  if (type === 'audio') {
    return null; // audio is invisible
  }

  // Fallback
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        opacity,
        background: getClipColor(type) + '44',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontSize: 12,
        fontFamily: 'monospace',
      }}
    >
      {type} asset
    </div>
  );
}

export const ShotstackComposition: React.FC<ShotstackPreviewProps> = ({
  editJson,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTimeSec = frame / fps;

  if (!editJson?.timeline?.tracks) {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: '#1a1a2e',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#64748b',
          fontSize: 18,
          fontFamily: 'system-ui',
        }}
      >
        Paste Shotstack JSON to preview
      </AbsoluteFill>
    );
  }

  const bg = editJson.timeline.background || '#000000';
  // Tracks render bottom-up: track 0 is the topmost layer
  const tracks = editJson.timeline.tracks;

  return (
    <AbsoluteFill style={{ backgroundColor: bg }}>
      {[...tracks].reverse().map((track, reversedIdx) => {
        const trackIdx = tracks.length - 1 - reversedIdx;
        const activeClips = track.clips.filter(
          (c) => currentTimeSec >= c.start && currentTimeSec < c.start + c.length
        );

        return activeClips.map((clip, clipIdx) => (
          <AbsoluteFill key={`${trackIdx}-${clipIdx}`}>
            <RenderClip clip={clip} currentTimeSec={currentTimeSec} />
          </AbsoluteFill>
        ));
      })}
    </AbsoluteFill>
  );
};

export { TRACK_COLORS, getClipColor };
export type { ShotstackClip, ShotstackTrack, ShotstackEdit };
