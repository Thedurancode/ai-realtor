import React, { useState, useRef, useCallback } from "react";
import { Player } from "@remotion/player";

import { TimelineEditor, TimelineTrack } from "./TimelineEditor";

interface TimelinePreviewProps {
  timeline: {
    tracks: TimelineTrack[];
    duration: number;
  };
  onTimelineChange?: (timeline: any) => void;
}

const TRACK_HEIGHT = 40;
const TRACK_COLORS: Record<string, string> = {
  video: "#3B82F6",
  image: "#10B981",
  text: "#F59E0B",
  audio: "#8B5CF6",
};

export const TimelinePreview: React.FC<TimelinePreviewProps> = ({
  timeline,
  onTimelineChange,
}) => {
  const playerRef = useRef<any>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);

  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      playerRef.current?.pause();
    } else {
      playerRef.current?.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const fraction = (e.clientX - rect.left) / rect.width;
    const targetFrame = Math.floor(fraction * timeline.duration);
    playerRef.current?.seekTo(targetFrame);
    setCurrentFrame(targetFrame);
  }, [timeline.duration]);

  const formatTime = (frames: number) => {
    const seconds = Math.floor(frames / 30);
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const scrubberPosition = timeline.duration > 0
    ? (currentFrame / timeline.duration) * 100
    : 0;

  return (
    <div style={{ width: "100%", fontFamily: "Inter, system-ui, sans-serif", color: "#fff" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 16,
          padding: 20,
          backgroundColor: "#0f172a",
          borderRadius: 12,
        }}
      >
        {/* Preview Player */}
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start" }}>
          <div
            style={{
              width: 270,
              height: 480,
              border: "2px solid #334155",
              borderRadius: 8,
              overflow: "hidden",
              flexShrink: 0,
            }}
          >
            <Player
              ref={playerRef}
              component={() => <TimelineEditor {...timeline} />}
              durationInFrames={timeline.duration || 1}
              compositionWidth={1080}
              compositionHeight={1920}
              fps={30}
              style={{ width: "100%", height: "100%" }}
              playbackRate={playbackRate}
            />
          </div>

          {/* Track visualization */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, color: "#94a3b8", marginBottom: 8 }}>
              Timeline — {timeline.tracks.length} track{timeline.tracks.length !== 1 ? "s" : ""} | {formatTime(timeline.duration)}
            </div>

            {/* Track lanes */}
            <div
              style={{
                backgroundColor: "#1e293b",
                borderRadius: 8,
                padding: 8,
                overflow: "hidden",
              }}
            >
              {timeline.tracks.map((track) => (
                <div key={track.id} style={{ marginBottom: 4 }}>
                  <div style={{ fontSize: 11, color: "#64748b", marginBottom: 2, textTransform: "uppercase" }}>
                    {track.type} — {track.id}
                  </div>
                  <div
                    style={{
                      position: "relative",
                      height: TRACK_HEIGHT,
                      backgroundColor: "#0f172a",
                      borderRadius: 4,
                    }}
                  >
                    {track.clips.map((clip) => {
                      const left = (clip.start / timeline.duration) * 100;
                      const clipWidth = (clip.duration / timeline.duration) * 100;
                      const color = TRACK_COLORS[clip.type] || "#6b7280";
                      return (
                        <div
                          key={clip.id}
                          title={`${clip.type}: ${clip.text || clip.src || clip.id} (${clip.duration} frames)`}
                          style={{
                            position: "absolute",
                            left: `${left}%`,
                            width: `${clipWidth}%`,
                            height: TRACK_HEIGHT - 4,
                            top: 2,
                            backgroundColor: color,
                            borderRadius: 3,
                            opacity: 0.85,
                            display: "flex",
                            alignItems: "center",
                            padding: "0 6px",
                            overflow: "hidden",
                          }}
                        >
                          <span style={{ fontSize: 11, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {clip.text || clip.id}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* Scrubber / playhead on click */}
              <div
                onClick={handleSeek}
                style={{
                  position: "relative",
                  height: 16,
                  marginTop: 8,
                  backgroundColor: "#334155",
                  borderRadius: 3,
                  cursor: "pointer",
                }}
              >
                {/* Progress fill */}
                <div
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: `${scrubberPosition}%`,
                    backgroundColor: "#3B82F6",
                    borderRadius: 3,
                    transition: "width 0.1s ease",
                  }}
                />
                {/* Playhead marker */}
                <div
                  style={{
                    position: "absolute",
                    left: `${scrubberPosition}%`,
                    top: -2,
                    width: 3,
                    height: 20,
                    backgroundColor: "#fff",
                    borderRadius: 2,
                    transform: "translateX(-1px)",
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Transport controls */}
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            onClick={handlePlayPause}
            style={{
              padding: "8px 20px",
              fontSize: 14,
              cursor: "pointer",
              backgroundColor: isPlaying ? "#dc2626" : "#3B82F6",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontWeight: 600,
            }}
          >
            {isPlaying ? "Pause" : "Play"}
          </button>

          {/* Playback speed */}
          <select
            value={playbackRate}
            onChange={(e) => setPlaybackRate(Number(e.target.value))}
            style={{
              padding: "8px 12px",
              fontSize: 13,
              backgroundColor: "#1e293b",
              color: "#fff",
              border: "1px solid #334155",
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            <option value={0.25}>0.25x</option>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={1.5}>1.5x</option>
            <option value={2}>2x</option>
          </select>

          <div style={{ fontSize: 13, color: "#94a3b8" }}>
            Frame {currentFrame} / {timeline.duration} | {formatTime(currentFrame)} / {formatTime(timeline.duration)}
          </div>
        </div>
      </div>
    </div>
  );
};
