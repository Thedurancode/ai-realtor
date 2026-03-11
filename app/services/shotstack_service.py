"""Shotstack API Service — Official SDK Edition

100% JSON-driven video rendering via the shotstack-sdk-python package.
Builds multi-track timelines using typed models (VideoAsset, Clip, Track, etc.).

Features:
  - Style presets: luxury, friendly, professional
  - Template CRUD: save/load/render reusable templates with merge fields
  - Natural language → timeline builder (describe a video, get JSON)
"""
import logging
from typing import Dict, List, Optional

import shotstack_sdk as shotstack
from shotstack_sdk.api import edit_api
from shotstack_sdk.model.audio_asset import AudioAsset
from shotstack_sdk.model.clip import Clip
from shotstack_sdk.model.edit import Edit
from shotstack_sdk.model.html_asset import HtmlAsset
from shotstack_sdk.model.image_asset import ImageAsset
from shotstack_sdk.model.offset import Offset
from shotstack_sdk.model.output import Output
from shotstack_sdk.model.soundtrack import Soundtrack
from shotstack_sdk.model.template import Template
from shotstack_sdk.model.timeline import Timeline
from shotstack_sdk.model.track import Track
from shotstack_sdk.model.transition import Transition
from shotstack_sdk.model.video_asset import VideoAsset
from shotstack_sdk.model.merge_field import MergeField

from app.config import settings

logger = logging.getLogger(__name__)


# ======================================================================
# Style presets
# ======================================================================

STYLE_PRESETS: Dict[str, Dict] = {
    "luxury": {
        "intro_length": 17,
        "outro_length": 17,
        "scene_length": 10,
        "transition_in": "fade",
        "transition_out": "fade",
        "photo_scale": 0.60,
        "photo_opacity": 0.95,
        "logo_scale": 0.12,
        "title_font": "Georgia,Times New Roman,serif",
        "body_font": "Georgia,Times New Roman,serif",
        "title_size": 40,
        "body_size": 28,
        "text_bg_opacity": 0.70,
        "text_border_radius": 0,
        "text_padding": "16px 40px",
        "text_letter_spacing": "2px",
        "text_transform": "uppercase",
        "music_volume": 0.12,
        "output_fps": 30,
    },
    "friendly": {
        "intro_length": 12,
        "outro_length": 12,
        "scene_length": 7,
        "transition_in": "slideRight",
        "transition_out": "slideLeft",
        "photo_scale": 0.50,
        "photo_opacity": 0.90,
        "logo_scale": 0.18,
        "title_font": "Arial,Helvetica,sans-serif",
        "body_font": "Arial,Helvetica,sans-serif",
        "title_size": 38,
        "body_size": 26,
        "text_bg_opacity": 0.80,
        "text_border_radius": 12,
        "text_padding": "10px 24px",
        "text_letter_spacing": "0",
        "text_transform": "none",
        "music_volume": 0.20,
        "output_fps": 30,
    },
    "professional": {
        "intro_length": 15,
        "outro_length": 15,
        "scene_length": 8,
        "transition_in": "fade",
        "transition_out": "fade",
        "photo_scale": 0.55,
        "photo_opacity": 0.92,
        "logo_scale": 0.15,
        "title_font": "Arial,Helvetica,sans-serif",
        "body_font": "Arial,Helvetica,sans-serif",
        "title_size": 36,
        "body_size": 28,
        "text_bg_opacity": 0.75,
        "text_border_radius": 8,
        "text_padding": "12px 24px",
        "text_letter_spacing": "0.5px",
        "text_transform": "none",
        "music_volume": 0.15,
        "output_fps": 30,
    },
}


class ShotstackService:
    """Shotstack Edit API client using the official Python SDK."""

    def __init__(self, api_key: Optional[str] = None, stage: Optional[bool] = None):
        self.api_key = api_key or settings.shotstack_api_key
        self.stage = stage if stage is not None else settings.shotstack_stage

        host = (
            "https://api.shotstack.io/stage"
            if self.stage
            else "https://api.shotstack.io/v1"
        )

        config = shotstack.Configuration(host=host)
        config.api_key["DeveloperKey"] = self.api_key

        self._api_client = shotstack.ApiClient(config)
        self._api = edit_api.EditApi(self._api_client)

    # ------------------------------------------------------------------
    # Property video timeline builder (uses SDK typed models)
    # ------------------------------------------------------------------

    def build_property_timeline(
        self,
        *,
        intro_video_url: str,
        outro_video_url: str,
        stock_video_urls: List[str],
        zillow_photo_urls: List[str],
        logo_url: Optional[str],
        voiceover_url: str,
        background_music_url: Optional[str] = None,
        agent_name: str = "",
        agent_phone: str = "",
        agent_email: str = "",
        address: str = "",
        property_details: str = "",
        primary_color: str = "#1E3A8A",
        text_color: str = "#FFFFFF",
        style: str = "professional",
    ) -> Edit:
        """Build a full Edit payload using SDK typed models + style preset."""
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["professional"])

        intro_len = preset["intro_length"]
        outro_len = preset["outro_length"]
        scene_len = preset["scene_length"]
        trans_in = preset["transition_in"]
        trans_out = preset["transition_out"]

        text_clips: List[Clip] = []
        image_clips: List[Clip] = []
        video_clips: List[Clip] = []
        audio_clips: List[Clip] = []

        offset = 0.0

        # ── Intro ─────────────────────────────────────────────
        video_clips.append(_video_clip(intro_video_url, offset, intro_len, trans_in, trans_out))

        if logo_url:
            image_clips.append(_image_clip(
                logo_url, offset, intro_len,
                position="topRight", scale=preset["logo_scale"],
                offset_x=-0.03, offset_y=-0.03,
            ))

        offset += intro_len

        # ── Property scenes ───────────────────────────────────
        scene_count = min(len(stock_video_urls), 5)
        detail_lines = [l.strip() for l in property_details.split("\n") if l.strip()]

        for i in range(scene_count):
            video_clips.append(_video_clip(
                stock_video_urls[i], offset, scene_len, trans_in, trans_out,
            ))

            if i < len(zillow_photo_urls):
                image_clips.append(_image_clip(
                    zillow_photo_urls[i], offset, scene_len,
                    position="center", scale=preset["photo_scale"],
                    opacity=preset["photo_opacity"],
                ))

            if i == 0 and address:
                text_clips.append(_styled_text_clip(
                    address, offset, scene_len, preset,
                    font_size=preset["title_size"], is_title=True,
                    bg_color=primary_color, text_color=text_color,
                ))
            elif i < len(detail_lines) and detail_lines:
                text_clips.append(_styled_text_clip(
                    detail_lines[i], offset, scene_len, preset,
                    font_size=preset["body_size"], is_title=False,
                    bg_color=primary_color, text_color=text_color,
                ))

            offset += scene_len

        # ── Outro ─────────────────────────────────────────────
        video_clips.append(_video_clip(outro_video_url, offset, outro_len, trans_in, trans_out))

        contact_parts = [p for p in [agent_name, agent_phone, agent_email] if p]
        if contact_parts:
            text_clips.append(_styled_text_clip(
                "<br>".join(contact_parts), offset, outro_len, preset,
                font_size=preset["body_size"] - 2, is_title=False,
                bg_color=primary_color, text_color=text_color,
            ))

        if logo_url:
            image_clips.append(_image_clip(
                logo_url, offset, outro_len,
                position="topRight", scale=preset["logo_scale"],
                offset_x=-0.03, offset_y=-0.03,
            ))

        total_duration = offset + outro_len

        # Voiceover
        audio_clips.append(Clip(
            asset=AudioAsset(type="audio", src=voiceover_url, volume=1.0),
            start=0,
            length=total_duration,
        ))

        # Assemble tracks
        tracks = [
            Track(clips=text_clips),
            Track(clips=image_clips),
            Track(clips=video_clips),
            Track(clips=audio_clips),
        ]

        timeline = Timeline(tracks=tracks, background="#000000")

        if background_music_url:
            timeline.soundtrack = Soundtrack(
                src=background_music_url,
                effect="fadeInFadeOut",
                volume=preset["music_volume"],
            )

        output = Output(format="mp4", resolution="hd", fps=float(preset["output_fps"]))

        logger.info(
            f"Built {style} timeline: {total_duration:.0f}s, "
            f"{scene_count} scenes, {len(text_clips)} text overlays"
        )
        return Edit(timeline=timeline, output=output)

    # ------------------------------------------------------------------
    # Brand video: logo intro → HeyGen talking head (~2 min)
    # ------------------------------------------------------------------

    def build_brand_video_timeline(
        self,
        *,
        logo_url: str,
        heygen_video_url: str,
        heygen_video_duration: float = 116.0,
        logo_intro_length: float = 4.0,
        cta_outro_length: float = 6.0,
        primary_color: str = "#1E3A8A",
        text_color: str = "#FFFFFF",
        agent_name: str = "",
        company_name: str = "",
        agent_phone: str = "",
        agent_email: str = "",
        website_url: str = "",
        tagline: str = "",
        background_music_url: Optional[str] = None,
        background_music_volume: float = 0.10,
    ) -> Edit:
        """Build a ~2 min brand video:
        [4s logo intro] → [HeyGen talking head] → [6s branded CTA outro]

        The HeyGen video already contains lip-synced audio from the cloned voice,
        so we keep its audio (volume=1) and don't need a separate voiceover track.

        Timeline structure:
          Track 0 (top):   text overlays (name card + CTA contact info)
          Track 1:         logo overlays (watermark + centered on intro/outro)
          Track 2 (main):  logo intro image + HeyGen video + CTA outro background
        """
        total_duration = logo_intro_length + heygen_video_duration + cta_outro_length
        cta_start = logo_intro_length + heygen_video_duration

        # ── Track 2 (bottom): main video sequence ─────────────
        main_clips = []

        # 1. Logo intro: centered logo on branded background, fades out
        main_clips.append(Clip(
            asset=ImageAsset(type="image", src=logo_url),
            start=0,
            length=logo_intro_length,
            fit="none",
            scale=0.45,
            position="center",
            transition=Transition(**{"in": "fade", "out": "fade"}),
            effect="zoomInSlow",
        ))

        # 2. HeyGen talking head — audio ON (volume=1) since it has the cloned voice
        main_clips.append(Clip(
            asset=VideoAsset(type="video", src=heygen_video_url, volume=1.0),
            start=logo_intro_length,
            length=heygen_video_duration,
            fit="cover",
            transition=Transition(**{"in": "fade", "out": "fade"}),
        ))

        # 3. CTA outro: centered logo on branded background
        main_clips.append(Clip(
            asset=ImageAsset(type="image", src=logo_url),
            start=cta_start,
            length=cta_outro_length,
            fit="none",
            scale=0.35,
            position="center",
            offset=Offset(x=0, y=-0.15),
            transition=Transition(**{"in": "fade", "out": "fadeSlow"}),
        ))

        # ── Track 1: logo watermark (top-right, during talking head only) ──
        logo_overlay_clips = [
            _image_clip(
                logo_url,
                start=logo_intro_length,
                length=heygen_video_duration,
                position="topRight", scale=0.12,
                offset_x=-0.03, offset_y=-0.03, opacity=0.85,
            )
        ]

        # ── Track 0 (top): text overlays ──────────────────────
        text_clips = []

        # Name card lower-third at start of talking head (8s, fades in/out)
        if agent_name or company_name:
            label = agent_name
            if company_name:
                label = f"{agent_name}<br><span style='font-size:20px;opacity:0.8'>{company_name}</span>" if agent_name else company_name
            text_clips.append(_styled_intro_text_clip(
                label,
                start=logo_intro_length,
                length=8.0,
                bg_color=primary_color,
            ))

        # CTA outro: contact info + tagline below logo
        cta_lines = []
        if agent_name:
            cta_lines.append(f"<b>{agent_name}</b>")
        if company_name:
            cta_lines.append(company_name)
        if agent_phone:
            cta_lines.append(agent_phone)
        if agent_email:
            cta_lines.append(agent_email)
        if website_url:
            cta_lines.append(website_url)

        if cta_lines:
            cta_html = "<br>".join(cta_lines)
            cta_css = (
                f"font-family:Arial,Helvetica,sans-serif;"
                f"font-size:22px;"
                f"color:{text_color};"
                f"text-align:center;"
                f"line-height:1.6;"
            )
            text_clips.append(Clip(
                asset=HtmlAsset(
                    type="html",
                    html=f'<div style="{cta_css}">{cta_html}</div>',
                    width=700,
                    height=200,
                ),
                start=cta_start,
                length=cta_outro_length,
                position="center",
                offset=Offset(x=0, y=0.12),
                transition=Transition(**{"in": "fade", "out": "fade"}),
            ))

        # Tagline above logo on outro
        if tagline:
            tagline_css = (
                f"font-family:Georgia,Times New Roman,serif;"
                f"font-size:18px;"
                f"font-style:italic;"
                f"color:{text_color};"
                f"opacity:0.85;"
                f"text-align:center;"
            )
            text_clips.append(Clip(
                asset=HtmlAsset(
                    type="html",
                    html=f'<div style="{tagline_css}">{tagline}</div>',
                    width=600,
                    height=60,
                ),
                start=cta_start,
                length=cta_outro_length,
                position="center",
                offset=Offset(x=0, y=-0.35),
                transition=Transition(**{"in": "fadeSlow", "out": "fade"}),
            ))

        # Assemble tracks (0 = top, 2 = bottom)
        tracks = [
            Track(clips=text_clips) if text_clips else Track(clips=[]),
            Track(clips=logo_overlay_clips),
            Track(clips=main_clips),
        ]

        timeline = Timeline(tracks=tracks, background=primary_color)

        if background_music_url:
            timeline.soundtrack = Soundtrack(
                src=background_music_url,
                effect="fadeInFadeOut",
                volume=background_music_volume,
            )

        output = Output(format="mp4", resolution="hd", fps=30.0)

        logger.info(
            f"Built brand video timeline: {total_duration:.0f}s "
            f"({logo_intro_length:.0f}s intro + {heygen_video_duration:.0f}s talking head + "
            f"{cta_outro_length:.0f}s CTA outro)"
        )
        return Edit(timeline=timeline, output=output)

    # ------------------------------------------------------------------
    # Freeform timeline builder — describe a video in plain English
    # ------------------------------------------------------------------

    def build_custom_timeline(
        self,
        clips_spec: List[Dict],
        *,
        output_format: str = "mp4",
        output_resolution: str = "hd",
        output_fps: float = 30,
        background: str = "#000000",
        soundtrack_url: Optional[str] = None,
        soundtrack_volume: float = 0.15,
    ) -> Edit:
        """Build a timeline from a list of clip specifications.

        Each clip_spec dict:
            {
                "type": "video"|"image"|"audio"|"html"|"title",
                "src": "https://...",           # for video/image/audio
                "html": "<p>...</p>",           # for html type
                "text": "Hello",                # for title type
                "title_style": "minimal",       # for title type
                "start": 0.0,
                "length": 5.0,
                "track": 0,                     # track index (0 = top)
                "transition_in": "fade",        # optional
                "transition_out": "fade",       # optional
                "effect": "zoomIn",             # optional
                "filter": "boost",              # optional
                "fit": "cover",                 # optional
                "scale": 1.0,                   # optional
                "position": "center",           # optional
                "offset_x": 0.0,               # optional
                "offset_y": 0.0,               # optional
                "opacity": 1.0,                # optional
                "volume": 1.0,                  # optional (video/audio)
                "trim": 0.0,                    # optional (video/audio)
                "speed": 1.0,                   # optional (video)
            }
        """
        # Group clips by track index
        track_map: Dict[int, List[Clip]] = {}
        for spec in clips_spec:
            track_idx = spec.get("track", 0)
            clip = _build_clip_from_spec(spec)
            track_map.setdefault(track_idx, []).append(clip)

        # Build tracks in order (lowest index = topmost layer)
        max_track = max(track_map.keys()) if track_map else 0
        tracks = []
        for i in range(max_track + 1):
            tracks.append(Track(clips=track_map.get(i, [])))

        timeline = Timeline(tracks=tracks, background=background)

        if soundtrack_url:
            timeline.soundtrack = Soundtrack(
                src=soundtrack_url,
                effect="fadeInFadeOut",
                volume=soundtrack_volume,
            )

        output = Output(format=output_format, resolution=output_resolution, fps=float(output_fps))
        return Edit(timeline=timeline, output=output)

    # ------------------------------------------------------------------
    # Template API — save, list, render
    # ------------------------------------------------------------------

    def save_template(self, name: str, edit: Edit) -> str:
        """Save an Edit as a reusable Shotstack template. Returns template ID."""
        template = Template(name=name, template=edit)
        response = self._api.post_template(template)
        template_id = response["response"]["id"]
        logger.info(f"Saved template '{name}': {template_id}")
        return template_id

    def list_templates(self) -> List[Dict]:
        """List all saved templates."""
        response = self._api.get_templates()
        templates = response.get("response", {}).get("templates", [])
        return [{"id": t.get("id"), "name": t.get("name")} for t in templates]

    def get_template(self, template_id: str) -> Dict:
        """Get a template by ID."""
        response = self._api.get_template(template_id)
        return response.get("response", {})

    def delete_template(self, template_id: str):
        """Delete a template."""
        self._api.delete_template(template_id)
        logger.info(f"Deleted template: {template_id}")

    def render_template(self, template_id: str, merge_fields: Optional[Dict[str, str]] = None) -> Dict:
        """Render a saved template, optionally replacing merge fields.

        merge_fields: {"HEADLINE": "Summer Sale!", "PRICE": "$499,000"}
        Returns: {"id": "render-id", "status": "queued"}
        """
        from shotstack_sdk.model.template_render import TemplateRender

        merge = []
        if merge_fields:
            merge = [MergeField(find=k, replace=v) for k, v in merge_fields.items()]

        payload = TemplateRender(id=template_id, merge=merge) if merge else TemplateRender(id=template_id)
        response = self._api.post_template_render(payload)
        inner = response.get("response", {})
        return {"id": inner.get("id"), "status": inner.get("status", "queued")}

    # ------------------------------------------------------------------
    # Render API
    # ------------------------------------------------------------------

    def submit_render(self, edit: Edit) -> Dict:
        """Submit an Edit for rendering. Returns {"id": ..., "status": "queued"}."""
        try:
            response = self._api.post_render(edit)
        except Exception as e:
            # Extract useful message from SDK exceptions
            body = getattr(e, "body", None)
            if body:
                import json as _json
                try:
                    parsed = _json.loads(body) if isinstance(body, str) else body
                    msg = parsed.get("response", {}).get("error") or parsed.get("message", str(e))
                    raise RuntimeError(f"Shotstack API error: {msg}") from e
                except (ValueError, AttributeError):
                    pass
            raise
        inner = response.get("response", {})
        return {"id": inner.get("id"), "status": inner.get("status", "queued")}

    def get_render_status(self, render_id: str) -> Dict:
        """Poll render status. Returns {"id", "status", "url"}."""
        response = self._api.get_render(render_id)
        inner = response.get("response", {})
        return {
            "id": inner.get("id"),
            "status": inner.get("status"),
            "url": inner.get("url"),
        }

    def probe(self, url: str) -> Dict:
        """Probe a media URL for metadata (duration, dimensions, codec)."""
        response = self._api.probe(url)
        return response.get("response", {})

    def close(self):
        """Close the API client."""
        self._api_client.close()

    # Keep async close() for compatibility with pipeline service
    async def aclose(self):
        self._api_client.close()


# ======================================================================
# Clip builder helpers (module-level, used by both timeline builders)
# ======================================================================

def _video_clip(
    src: str, start: float, length: float,
    trans_in: str = "fade", trans_out: str = "fade",
    volume: float = 0, fit: str = "cover",
    effect: Optional[str] = None, filter_: Optional[str] = None,
    speed: Optional[float] = None, trim: Optional[float] = None,
) -> Clip:
    asset_kwargs = {"type": "video", "src": src, "volume": volume}
    if trim:
        asset_kwargs["trim"] = trim
    if speed:
        asset_kwargs["speed"] = speed

    clip_kwargs = {
        "asset": VideoAsset(**asset_kwargs),
        "start": start,
        "length": length,
        "fit": fit,
        "transition": Transition(**{"in": trans_in, "out": trans_out}),
    }
    if effect:
        clip_kwargs["effect"] = effect
    if filter_:
        clip_kwargs["filter"] = filter_
    return Clip(**clip_kwargs)


def _image_clip(
    src: str, start: float, length: float,
    position: str = "center", scale: float = 1.0,
    opacity: float = 1.0, offset_x: float = 0, offset_y: float = 0,
    effect: Optional[str] = None,
) -> Clip:
    clip_kwargs = {
        "asset": ImageAsset(type="image", src=src),
        "start": start,
        "length": length,
        "fit": "none",
        "scale": scale,
        "opacity": opacity,
        "position": position,
        "offset": Offset(x=offset_x, y=offset_y),
    }
    if effect:
        clip_kwargs["effect"] = effect
    return Clip(**clip_kwargs)


def _audio_clip(
    src: str, start: float, length: float,
    volume: float = 1.0, trim: Optional[float] = None,
) -> Clip:
    asset_kwargs = {"type": "audio", "src": src, "volume": volume}
    if trim:
        asset_kwargs["trim"] = trim
    return Clip(
        asset=AudioAsset(**asset_kwargs),
        start=start,
        length=length,
    )


def _styled_text_clip(
    html_body: str, start: float, length: float, preset: Dict,
    position: str = "bottom", bg_color: str = "#1E3A8A",
    text_color: str = "#FFFFFF", font_size: int = 30,
    is_title: bool = False,
) -> Clip:
    font = preset["title_font"] if is_title else preset["body_font"]
    css = (
        f"font-family:{font};"
        f"font-size:{font_size}px;"
        f"color:{text_color};"
        f"background:rgba({_hex_to_rgb_css(bg_color)},{preset['text_bg_opacity']});"
        f"padding:{preset['text_padding']};"
        f"border-radius:{preset['text_border_radius']}px;"
        f"text-align:center;"
        f"letter-spacing:{preset['text_letter_spacing']};"
        f"text-transform:{preset['text_transform']};"
    )
    if is_title:
        css += "font-weight:bold;"

    html = f'<div style="{css}">{html_body}</div>'
    return Clip(
        asset=HtmlAsset(type="html", html=html, width=800, height=120),
        start=start,
        length=length,
        position=position,
        offset=Offset(x=0, y=-0.05),
    )


def _styled_intro_text_clip(
    html_body: str, start: float, length: float,
    bg_color: str = "#1E3A8A", text_color: str = "#FFFFFF",
) -> Clip:
    """Lower-third name card that fades in/out over the talking head intro."""
    css = (
        f"font-family:Arial,Helvetica,sans-serif;"
        f"font-size:26px;"
        f"color:{text_color};"
        f"background:rgba({_hex_to_rgb_css(bg_color)},0.80);"
        f"padding:10px 32px;"
        f"border-radius:6px;"
        f"text-align:center;"
    )
    html = f'<div style="{css}">{html_body}</div>'
    return Clip(
        asset=HtmlAsset(type="html", html=html, width=600, height=100),
        start=start,
        length=length,
        position="bottom",
        offset=Offset(x=0, y=-0.08),
        transition=Transition(**{"in": "fade", "out": "fade"}),
    )


def _build_clip_from_spec(spec: Dict) -> Clip:
    """Build a Clip from a freeform spec dict."""
    clip_type = spec.get("type", "video")
    start = float(spec.get("start", 0))
    length = float(spec.get("length", 5))

    # Build asset
    if clip_type == "video":
        asset_kwargs = {"type": "video", "src": spec["src"], "volume": float(spec.get("volume", 0))}
        if spec.get("trim"):
            asset_kwargs["trim"] = float(spec["trim"])
        if spec.get("speed"):
            asset_kwargs["speed"] = float(spec["speed"])
        asset = VideoAsset(**asset_kwargs)
    elif clip_type == "image":
        asset = ImageAsset(type="image", src=spec["src"])
    elif clip_type == "audio":
        asset_kwargs = {"type": "audio", "src": spec["src"], "volume": float(spec.get("volume", 1.0))}
        if spec.get("trim"):
            asset_kwargs["trim"] = float(spec["trim"])
        asset = AudioAsset(**asset_kwargs)
    elif clip_type == "html":
        asset = HtmlAsset(
            type="html", html=spec.get("html", ""),
            width=int(spec.get("width", 800)), height=int(spec.get("height", 120)),
        )
    else:
        raise ValueError(f"Unknown clip type: {clip_type}")

    # Build clip
    clip_kwargs: Dict = {"asset": asset, "start": start, "length": length}

    if spec.get("fit"):
        clip_kwargs["fit"] = spec["fit"]
    if spec.get("scale"):
        clip_kwargs["scale"] = float(spec["scale"])
    if spec.get("opacity") is not None:
        clip_kwargs["opacity"] = float(spec["opacity"])
    if spec.get("position"):
        clip_kwargs["position"] = spec["position"]
    if spec.get("offset_x") is not None or spec.get("offset_y") is not None:
        clip_kwargs["offset"] = Offset(
            x=float(spec.get("offset_x", 0)), y=float(spec.get("offset_y", 0)),
        )
    if spec.get("transition_in") or spec.get("transition_out"):
        clip_kwargs["transition"] = Transition(
            **{"in": spec.get("transition_in", "fade"), "out": spec.get("transition_out", "fade")}
        )
    if spec.get("effect"):
        clip_kwargs["effect"] = spec["effect"]
    if spec.get("filter"):
        clip_kwargs["filter"] = spec["filter"]

    return Clip(**clip_kwargs)


def _hex_to_rgb_css(hex_color: str) -> str:
    """Convert '#RRGGBB' to 'R,G,B' for CSS rgba()."""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"
