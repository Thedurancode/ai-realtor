'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Player } from '@remotion/player';
import {
  ShotstackComposition,
  TRACK_COLORS,
  getClipColor,
} from '../../../components/remotion/ShotstackPreview';
import type {
  ShotstackEdit,
  ShotstackClip,
} from '../../../components/remotion/ShotstackPreview';
import { Film, Upload, Download, Eye, Code, Layers, ChevronDown, ChevronRight, LayoutTemplate, RefreshCw, Save, Plus, Trash2, Pencil, Sparkles } from 'lucide-react';
import AIChatPanel from '../../../components/video-editor/AIChatPanel';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const FPS = 30;

function computeTotalDuration(edit: ShotstackEdit | null): number {
  if (!edit?.timeline?.tracks) return 10;
  let maxEnd = 0;
  for (const track of edit.timeline.tracks) {
    for (const clip of track.clips) {
      const end = clip.start + clip.length;
      if (end > maxEnd) maxEnd = end;
    }
  }
  return Math.max(maxEnd, 1);
}

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

interface ClipInfo {
  trackIndex: number;
  clipIndex: number;
  clip: ShotstackClip;
}

// Editable input for numbers
function NumInput({ label, value, onChange, step = 0.1, min }: {
  label: string; value: number; onChange: (v: number) => void; step?: number; min?: number;
}) {
  return (
    <div>
      <label className="text-slate-400 text-xs block mb-0.5">{label}</label>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        className="border border-slate-300 rounded px-2 py-1 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
      />
    </div>
  );
}

// Editable input for text
function TextInput({ label, value, onChange, mono, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; mono?: boolean; placeholder?: string;
}) {
  return (
    <div className="col-span-2 md:col-span-4">
      <label className="text-slate-400 text-xs block mb-0.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`border border-slate-300 rounded px-2 py-1 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500 ${mono ? 'font-mono text-xs' : ''}`}
      />
    </div>
  );
}

// Editable textarea for HTML
function HtmlInput({ label, value, onChange }: {
  label: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div className="col-span-2 md:col-span-4">
      <label className="text-slate-400 text-xs block mb-0.5">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        className="border border-slate-300 rounded px-2 py-1 text-xs w-full font-mono resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
        spellCheck={false}
      />
    </div>
  );
}

function SelectInput({ label, value, options, onChange }: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="text-slate-400 text-xs block mb-0.5">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-slate-300 rounded px-2 py-1 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

const TRANSITION_TYPES = ['', 'fade', 'reveal', 'wipeLeft', 'wipeRight', 'slideLeft', 'slideRight', 'slideUp', 'slideDown', 'carouselLeft', 'carouselRight', 'carouselUp', 'carouselDown', 'shuffleTopRight', 'shuffleRightTop', 'zoom'];
const POSITION_OPTIONS = ['', 'center', 'top', 'topRight', 'right', 'bottomRight', 'bottom', 'bottomLeft', 'left', 'topLeft'];
const FIT_OPTIONS = ['', 'cover', 'contain', 'crop', 'none'];

export default function VideoEditorPage() {
  const [jsonInput, setJsonInput] = useState('');
  const [editJson, setEditJson] = useState<ShotstackEdit | null>(null);
  const [parseError, setParseError] = useState('');
  const [selectedClip, setSelectedClip] = useState<ClipInfo | null>(null);
  const [agentId, setAgentId] = useState('');
  const [jobId, setJobId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [showJson, setShowJson] = useState(false);
  const [templates, setTemplates] = useState<{ id: string; name: string }[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [templatesError, setTemplatesError] = useState('');
  const [saveTemplateName, setSaveTemplateName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  const [chatCollapsed, setChatCollapsed] = useState(false);

  const totalDuration = useMemo(() => computeTotalDuration(editJson), [editJson]);
  const totalFrames = Math.ceil(totalDuration * FPS);

  // ── Mutate a clip and propagate to editJson + selectedClip ──
  const updateClip = useCallback((trackIdx: number, clipIdx: number, updater: (clip: ShotstackClip) => ShotstackClip) => {
    setEditJson((prev) => {
      if (!prev?.timeline?.tracks) return prev;
      const next = deepClone(prev);
      const clip = next.timeline!.tracks![trackIdx].clips[clipIdx];
      next.timeline!.tracks![trackIdx].clips[clipIdx] = updater(clip);
      // Keep JSON panel in sync
      setJsonInput(JSON.stringify(next, null, 2));
      // Update selectedClip reference
      setSelectedClip((sel) => {
        if (sel && sel.trackIndex === trackIdx && sel.clipIndex === clipIdx) {
          return { ...sel, clip: next.timeline!.tracks![trackIdx].clips[clipIdx] };
        }
        return sel;
      });
      return next;
    });
  }, []);

  // ── Add a new clip to a track ──
  const addClip = useCallback((trackIdx: number) => {
    setEditJson((prev) => {
      if (!prev?.timeline?.tracks) return prev;
      const next = deepClone(prev);
      const track = next.timeline!.tracks![trackIdx];
      const lastEnd = track.clips.reduce((max, c) => Math.max(max, c.start + c.length), 0);
      track.clips.push({
        asset: { type: 'html', html: '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#fff;font-size:36px;font-family:Arial,sans-serif;">New Clip</div>', width: 1920, height: 1080 },
        start: lastEnd,
        length: 5,
      });
      setJsonInput(JSON.stringify(next, null, 2));
      return next;
    });
  }, []);

  // ── Add a new track ──
  const addTrack = useCallback(() => {
    setEditJson((prev) => {
      if (!prev?.timeline) return prev;
      const next = deepClone(prev);
      if (!next.timeline!.tracks) next.timeline!.tracks = [];
      next.timeline!.tracks!.push({
        clips: [{
          asset: { type: 'html', html: '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#fff;font-size:36px;font-family:Arial,sans-serif;">New Track</div>', width: 1920, height: 1080 },
          start: 0,
          length: 5,
        }],
      });
      setJsonInput(JSON.stringify(next, null, 2));
      return next;
    });
  }, []);

  // ── Delete a clip ──
  const deleteClip = useCallback((trackIdx: number, clipIdx: number) => {
    setEditJson((prev) => {
      if (!prev?.timeline?.tracks) return prev;
      const next = deepClone(prev);
      next.timeline!.tracks![trackIdx].clips.splice(clipIdx, 1);
      // Remove empty tracks
      if (next.timeline!.tracks![trackIdx].clips.length === 0) {
        next.timeline!.tracks!.splice(trackIdx, 1);
      }
      setJsonInput(JSON.stringify(next, null, 2));
      setSelectedClip(null);
      return next;
    });
  }, []);

  // ── AI timeline update (from chat panel) ──
  const handleAITimelineUpdate = useCallback((newEdit: ShotstackEdit) => {
    setEditJson(newEdit);
    setJsonInput(JSON.stringify(newEdit, null, 2));
    setSelectedClip(null);
    setParseError('');
  }, []);

  // ── Save as Shotstack template ──
  const handleSaveTemplate = useCallback(async () => {
    if (!editJson || !saveTemplateName.trim()) return;
    setSaving(true);
    setSaveMsg('');
    try {
      const res = await fetch(`${API_BASE}/agent-brand/shotstack/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: saveTemplateName.trim(), edit: editJson }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setSaveMsg(`Saved! ID: ${data.id || data.template_id || 'ok'}`);
      setSaveTemplateName('');
      fetchTemplates();
    } catch (e: any) {
      setSaveMsg(`Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  }, [editJson, saveTemplateName]);

  const handleParseJson = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonInput);
      const edit = parsed.timeline ? parsed : { timeline: parsed };
      setEditJson(edit);
      setParseError('');
      setSelectedClip(null);
    } catch (e: any) {
      setParseError(e.message);
    }
  }, [jsonInput]);

  const fetchTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    setTemplatesError('');
    try {
      const res = await fetch(`${API_BASE}/agent-brand/shotstack/templates`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      setTemplates(await res.json());
    } catch (e: any) {
      setTemplatesError(e.message);
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  const handleLoadTemplate = useCallback(async (templateId: string) => {
    setLoading(true);
    setLoadError('');
    try {
      const res = await fetch(`${API_BASE}/agent-brand/shotstack/templates/${templateId}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const editData = data.template || data;
      const edit = editData.timeline ? editData : { timeline: editData };
      setEditJson(edit);
      setJsonInput(JSON.stringify(edit, null, 2));
      setParseError('');
      setSelectedClip(null);
    } catch (e: any) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

  const handleLoadFromApi = useCallback(async () => {
    if (!agentId || !jobId) return;
    setLoading(true);
    setLoadError('');
    try {
      const token = localStorage.getItem('portal_token') || '';
      const res = await fetch(
        `${API_BASE}/agent-brand/${agentId}/property-video/${jobId}/timeline`,
        { headers: { 'x-api-key': token } }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      const edit = data.timeline ? data : { timeline: data };
      setEditJson(edit);
      setJsonInput(JSON.stringify(edit, null, 2));
      setParseError('');
      setSelectedClip(null);
    } catch (e: any) {
      setLoadError(e.message);
    } finally {
      setLoading(false);
    }
  }, [agentId, jobId]);

  const timelineData = useMemo(() => {
    if (!editJson?.timeline?.tracks) return [];
    return editJson.timeline.tracks.map((track, trackIdx) => ({
      trackIdx,
      clips: track.clips.map((clip, clipIdx) => ({
        trackIndex: trackIdx,
        clipIndex: clipIdx,
        clip,
      })),
    }));
  }, [editJson]);

  const sel = selectedClip;

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6">
      {/* AI Chat Panel */}
      <div className={`${chatCollapsed ? 'w-0' : 'w-[350px]'} shrink-0 transition-all duration-300 overflow-hidden h-full`}>
        <AIChatPanel
          editJson={editJson}
          onTimelineUpdate={handleAITimelineUpdate}
          collapsed={chatCollapsed}
          onToggle={() => setChatCollapsed(!chatCollapsed)}
        />
      </div>
      {chatCollapsed && (
        <AIChatPanel
          editJson={editJson}
          onTimelineUpdate={handleAITimelineUpdate}
          collapsed={true}
          onToggle={() => setChatCollapsed(false)}
        />
      )}

      {/* Main Editor */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Film className="w-7 h-7 text-blue-600" />
          <h1 className="text-2xl font-bold text-slate-900">Video Editor Preview</h1>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500">
          {!chatCollapsed ? null : (
            <button
              onClick={() => setChatCollapsed(false)}
              className="bg-purple-100 text-purple-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-purple-200 transition-colors flex items-center gap-1.5 mr-3"
            >
              <Sparkles className="w-3.5 h-3.5" />
              AI Chat
            </button>
          )}
          <Layers className="w-4 h-4" />
          {editJson?.timeline?.tracks?.length || 0} tracks
        </div>
      </div>

      {/* Shotstack Templates */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
            <LayoutTemplate className="w-4 h-4" />
            Shotstack Templates
          </h2>
          <button
            onClick={fetchTemplates}
            disabled={templatesLoading}
            className="text-slate-400 hover:text-slate-600 transition-colors"
            title="Refresh templates"
          >
            <RefreshCw className={`w-4 h-4 ${templatesLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
        {templatesError && <p className="text-red-500 text-sm mb-2">{templatesError}</p>}
        {templates.length === 0 && !templatesLoading && !templatesError && (
          <p className="text-slate-400 text-sm">No templates found.</p>
        )}
        {templates.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {templates.map((t) => (
              <button
                key={t.id}
                onClick={() => handleLoadTemplate(t.id)}
                disabled={loading}
                className="bg-slate-100 hover:bg-blue-50 hover:border-blue-300 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 font-medium transition-colors disabled:opacity-50"
              >
                {t.name || t.id}
              </button>
            ))}
          </div>
        )}
        {loading && <p className="text-blue-500 text-sm mt-2">Loading template...</p>}
        {loadError && <p className="text-red-500 text-sm mt-2">{loadError}</p>}
      </div>

      {/* Remotion Player */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-900 flex items-center justify-center" style={{ minHeight: 360 }}>
          {editJson ? (
            <Player
              component={ShotstackComposition as any}
              inputProps={{ editJson }}
              durationInFrames={totalFrames}
              fps={FPS}
              compositionWidth={1920}
              compositionHeight={1080}
              style={{ width: '100%', maxWidth: 960, aspectRatio: '16/9' }}
              controls
              autoPlay={false}
            />
          ) : (
            <div className="text-slate-500 text-center py-20">
              <Eye className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-lg">No timeline loaded</p>
              <p className="text-sm mt-1">Select a template above or paste JSON below</p>
            </div>
          )}
        </div>
      </div>

      {/* Timeline Bars */}
      {editJson?.timeline?.tracks && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Layers className="w-4 h-4" />
              Timeline
              <span className="text-xs text-slate-400 font-normal">
                {totalDuration.toFixed(1)}s total
              </span>
            </h2>
            <button
              onClick={addTrack}
              className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 px-2 py-1 rounded flex items-center gap-1 transition-colors"
            >
              <Plus className="w-3 h-3" /> Track
            </button>
          </div>
          <div className="space-y-2">
            {timelineData.map(({ trackIdx, clips }) => (
              <div key={trackIdx} className="flex items-center gap-2">
                <span className="text-xs text-slate-400 w-16 shrink-0 text-right">
                  Track {trackIdx}
                </span>
                <div
                  className="relative flex-1 h-8 bg-slate-100 rounded overflow-hidden"
                  style={{ minWidth: 200 }}
                >
                  {clips.map(({ clip, clipIndex }) => {
                    const left = (clip.start / totalDuration) * 100;
                    const width = (clip.length / totalDuration) * 100;
                    const color = getClipColor(clip.asset.type);
                    const isSelected =
                      sel?.trackIndex === trackIdx && sel?.clipIndex === clipIndex;

                    return (
                      <button
                        key={clipIndex}
                        onClick={() => setSelectedClip({ trackIndex: trackIdx, clipIndex, clip })}
                        className={`absolute top-0.5 bottom-0.5 rounded text-[10px] text-white font-medium flex items-center px-1.5 overflow-hidden cursor-pointer transition-all ${
                          isSelected ? 'ring-2 ring-white ring-offset-1 ring-offset-slate-100 z-10' : 'hover:brightness-110'
                        }`}
                        style={{
                          left: `${left}%`,
                          width: `${Math.max(width, 0.5)}%`,
                          backgroundColor: color,
                        }}
                        title={`${clip.asset.type} | ${clip.start.toFixed(1)}s - ${(clip.start + clip.length).toFixed(1)}s`}
                      >
                        <span className="truncate">{clip.asset.type}</span>
                      </button>
                    );
                  })}
                </div>
                <button
                  onClick={() => addClip(trackIdx)}
                  className="text-slate-400 hover:text-blue-500 transition-colors"
                  title="Add clip"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex gap-4 mt-3 pt-3 border-t border-slate-100">
            {Object.entries(TRACK_COLORS).filter(([k]) => !['luma'].includes(k)).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5 text-xs text-slate-500">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
                {type}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Clip Inspector (Editable) */}
      {sel && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Pencil className="w-4 h-4" />
              Edit Clip — Track {sel.trackIndex}, Clip {sel.clipIndex}
            </h2>
            <button
              onClick={() => deleteClip(sel.trackIndex, sel.clipIndex)}
              className="text-red-400 hover:text-red-600 transition-colors text-xs flex items-center gap-1"
              title="Delete clip"
            >
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {/* Type */}
            <SelectInput
              label="Type"
              value={sel.clip.asset.type}
              options={['html', 'image', 'video', 'audio', 'title']}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, asset: { ...c.asset, type: v } }))}
            />

            {/* Timing */}
            <NumInput
              label="Start (s)"
              value={sel.clip.start}
              min={0}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, start: v }))}
            />
            <NumInput
              label="Length (s)"
              value={sel.clip.length}
              min={0.1}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, length: v }))}
            />
            <div>
              <label className="text-slate-400 text-xs block mb-0.5">End</label>
              <div className="border border-slate-200 bg-slate-50 rounded px-2 py-1 text-sm font-mono text-slate-500">
                {(sel.clip.start + sel.clip.length).toFixed(2)}s
              </div>
            </div>

            {/* Source URL (image / video) */}
            {(sel.clip.asset.type === 'image' || sel.clip.asset.type === 'video' || sel.clip.asset.type === 'audio') && (
              <TextInput
                label="Source URL"
                value={sel.clip.asset.src || ''}
                mono
                placeholder="https://..."
                onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, asset: { ...c.asset, src: v } }))}
              />
            )}

            {/* Text (title type) */}
            {(sel.clip.asset.type === 'title' || sel.clip.asset.type === 'text') && (
              <TextInput
                label="Text"
                value={sel.clip.asset.text || ''}
                onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, asset: { ...c.asset, text: v } }))}
              />
            )}

            {/* HTML */}
            {sel.clip.asset.type === 'html' && (
              <HtmlInput
                label="HTML"
                value={sel.clip.asset.html || ''}
                onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, asset: { ...c.asset, html: v } }))}
              />
            )}

            {/* Position */}
            <SelectInput
              label="Position"
              value={sel.clip.position || ''}
              options={POSITION_OPTIONS}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, position: v || undefined }))}
            />

            {/* Fit */}
            <SelectInput
              label="Fit"
              value={sel.clip.fit || ''}
              options={FIT_OPTIONS}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, fit: v || undefined }))}
            />

            {/* Scale */}
            <NumInput
              label="Scale"
              value={sel.clip.scale ?? 1}
              step={0.05}
              min={0}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, scale: v }))}
            />

            {/* Opacity */}
            <NumInput
              label="Opacity"
              value={sel.clip.opacity ?? 1}
              step={0.05}
              min={0}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({ ...c, opacity: v }))}
            />

            {/* Transitions */}
            <SelectInput
              label="Transition In"
              value={sel.clip.transition?.in?.type || sel.clip.transition?.in || ''}
              options={TRANSITION_TYPES}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({
                ...c,
                transition: v
                  ? { ...c.transition, in: v }
                  : { ...c.transition, in: undefined },
              }))}
            />
            <SelectInput
              label="Transition Out"
              value={sel.clip.transition?.out?.type || sel.clip.transition?.out || ''}
              options={TRANSITION_TYPES}
              onChange={(v) => updateClip(sel.trackIndex, sel.clipIndex, (c) => ({
                ...c,
                transition: v
                  ? { ...c.transition, out: v }
                  : { ...c.transition, out: undefined },
              }))}
            />
          </div>
        </div>
      )}

      {/* Save as Template */}
      {editJson && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Save className="w-4 h-4" />
            Save as Template
          </h2>
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs text-slate-500 block mb-1">Template Name</label>
              <input
                type="text"
                value={saveTemplateName}
                onChange={(e) => setSaveTemplateName(e.target.value)}
                placeholder="My Custom Template"
                className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleSaveTemplate}
              disabled={saving || !saveTemplateName.trim()}
              className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2 shrink-0"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
          {saveMsg && (
            <p className={`text-sm mt-2 ${saveMsg.startsWith('Error') ? 'text-red-500' : 'text-green-600'}`}>
              {saveMsg}
            </p>
          )}
        </div>
      )}

      {/* Load from API */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Download className="w-4 h-4" />
          Load from API
        </h2>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs text-slate-500 block mb-1">Agent ID</label>
            <input
              type="text"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              placeholder="1"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-xs text-slate-500 block mb-1">Job ID</label>
            <input
              type="text"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="1"
              className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleLoadFromApi}
            disabled={loading || !agentId || !jobId}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Load Timeline'}
          </button>
        </div>
      </div>

      {/* JSON Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <button
          onClick={() => setShowJson(!showJson)}
          className="text-sm font-semibold text-slate-700 flex items-center gap-2 w-full"
        >
          <Code className="w-4 h-4" />
          JSON Editor
          {showJson ? <ChevronDown className="w-4 h-4 ml-auto" /> : <ChevronRight className="w-4 h-4 ml-auto" />}
        </button>
        {showJson && (
          <div className="mt-3 space-y-3">
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder='Paste Shotstack Edit JSON here...'
              className="w-full h-64 border border-slate-300 rounded-lg px-3 py-2 text-xs font-mono resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
              spellCheck={false}
            />
            <div className="flex items-center gap-3">
              <button
                onClick={handleParseJson}
                disabled={!jsonInput.trim()}
                className="bg-slate-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                <Upload className="w-4 h-4" />
                Load JSON
              </button>
              {parseError && <p className="text-red-500 text-sm">Parse error: {parseError}</p>}
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
}
