import React, { useState, useRef, useEffect } from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  delayRender,
  continueRender,
} from "remotion";
import { Player, CurrentTimeContext } from "@remotion/player";

import { TimelineEditor, TimelineClip, TimelineTrack } from "./TimelineEditor";

interface TimelinePreviewProps {
  timeline: {
    tracks: TimelineTrack[];
    duration: number;
  };
  onTimelineChange?: (timeline: any) => void;
}

export const TimelinePreview: React.FC<TimelinePreviewProps> = ({
  timeline,
  onTimelineChange,
}) => {
  const playerRef = useRef<any>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  const handlePlayPause = () => {
    if (isPlaying) {
      playerRef.current?.pause();
    } else {
      playerRef.current?.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
          padding: "20px",
        }}
      >
        {/* Preview Player */}
        <div
          style={{
            width: "360px",
            height: "640px",
            border: "2px solid #333",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          <Player
            ref={playerRef}
            component={() => <TimelineEditor {...timeline} />}
            durationInFrames={timeline.duration}
            compositionWidth={1080}
            compositionHeight={1920}
            fps={30}
            style={{ width: "100%", height: "100%" }}
            onPlay={handleTimeUpdate}
            onPause={handleTimeUpdate}
          />
        </div>

        {/* Controls */}
        <div
          style={{
            display: "flex",
            gap: "10px",
            alignItems: "center",
          }}
        >
          <button
            onClick={handlePlayPause}
            style={{
              padding: "10px 20px",
              fontSize: "16px",
              cursor: "pointer",
            }}
          >
            {isPlaying ? "⏸️ Pause" : "▶️ Play"}
          </button>

          <div style={{ fontSize: "14px" }}>
            Frame: {Math.floor(currentTime * 30)} / {timeline.duration}
          </div>
        </div>
      </div>
    </div>
  );
};
