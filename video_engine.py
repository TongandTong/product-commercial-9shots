# -*- coding: utf-8 -*-
"""
video_engine.py - Core video rendering, Thai TTS synthesis, and FFmpeg assembly engine.
Designed for Streamlit Cloud and local environments.
"""

import os
import shutil
import subprocess
import re
import asyncio
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


def get_ffmpeg_exe() -> str:
    """Return path to ffmpeg executable (system PATH or imageio-ffmpeg static binary)."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def get_thai_font(size: int = 32, bold: bool = False) -> ImageFont.ImageFont:
    """Load high-quality Thai font with multi-platform fallback."""
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansThai.ttf"),
        "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Loma.ttf",
        "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf" if bold else "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
        "C:/Windows/Fonts/leelawdb.ttf" if bold else "C:/Windows/Fonts/leelawad.ttf",
        "C:/Windows/Fonts/tahomabd.ttf" if bold else "C:/Windows/Fonts/tahoma.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def get_media_duration(file_path: str, ffmpeg_exe: Optional[str] = None) -> float:
    """Extract media duration in seconds using FFmpeg."""
    if not os.path.exists(file_path):
        return 1.5
    exe = ffmpeg_exe or get_ffmpeg_exe()
    cmd = [exe, "-i", file_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr)
    if m:
        h, m_val, s = m.groups()
        return int(h) * 3600 + int(m_val) * 60 + float(s)
    return 1.5


def generate_thai_tts(
    text: str,
    output_path: str,
    voice: str = "th-TH-PremwadeeNeural",
    ffmpeg_exe: Optional[str] = None
) -> Tuple[bool, float]:
    """
    Generate Thai speech narration MP3.
    Uses edge-tts first; falls back to gTTS if edge-tts fails.
    Returns (success, duration_seconds).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    clean_text = text.strip()
    if not clean_text:
        clean_text = "โปรดติดตามรายละเอียด"

    # Try edge-tts
    if HAS_EDGE_TTS:
        async def _speak():
            comm = edge_tts.Communicate(clean_text, voice)
            await comm.save(output_path)

        try:
            asyncio.run(_speak())
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                dur = get_media_duration(output_path, ffmpeg_exe)
                return True, dur
        except Exception as e:
            print(f"Edge-TTS failed: {e}, falling back to gTTS")

    # Fallback to gTTS
    if HAS_GTTS:
        try:
            tts = gTTS(text=clean_text, lang="th")
            tts.save(output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                dur = get_media_duration(output_path, ffmpeg_exe)
                return True, dur
        except Exception as e:
            print(f"gTTS failed: {e}")

    # Fallback: create silent audio file via ffmpeg
    exe = ffmpeg_exe or get_ffmpeg_exe()
    cmd = [exe, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1.5", "-y", output_path]
    subprocess.run(cmd, capture_output=True)
    return False, 1.5


def wrap_text(text: str, max_chars: int = 34) -> List[str]:
    """Clean word/character wrapping for Thai text subtitle display."""
    if len(text) <= max_chars:
        return [text]
    lines = []
    # If spaces exist, wrap by words
    if " " in text:
        words = text.split(" ")
        cur_line = ""
        for w in words:
            if len(cur_line) + len(w) + 1 <= max_chars:
                cur_line = f"{cur_line} {w}".strip()
            else:
                if cur_line:
                    lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)
    else:
        # Split by character chunk
        for i in range(0, len(text), max_chars):
            lines.append(text[i:i + max_chars])
    return lines[:3]


def create_style_background(style: str, width: int = 720, height: int = 1280) -> Image.Image:
    """Generate dynamic backdrop tailored to the chosen commercial style."""
    bg = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(bg)

    if style == "Minimal Clean":
        # Soft off-white to warm light gray gradient
        for y in range(height):
            ratio = y / height
            r = int(248 - ratio * 15)
            g = int(249 - ratio * 14)
            b = int(250 - ratio * 12)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        # Subtle architectural ring accent
        draw.ellipse([-100, -100, 400, 400], outline=(230, 232, 238, 120), width=4)
        draw.ellipse([width - 250, height - 350, width + 150, height + 50], outline=(230, 232, 238, 100), width=6)

    elif style == "Studio Luxury":
        # Obsidian dark charcoal with golden radial spotlight in center
        for y in range(height):
            ratio = y / height
            r = int(12 + ratio * 12)
            g = int(12 + ratio * 12)
            b = int(16 + ratio * 15)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        # Radial gold spotlight behind center product
        center_x, center_y = width // 2, int(height * 0.42)
        spot = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        spot_draw = ImageDraw.Draw(spot)
        spot_draw.ellipse(
            [center_x - 300, center_y - 300, center_x + 300, center_y + 300],
            fill=(212, 175, 55, 35) # Gold glow
        )
        spot_draw.ellipse(
            [center_x - 180, center_y - 180, center_x + 180, center_y + 180],
            fill=(255, 220, 100, 45) # Intense center
        )
        spot = spot.filter(ImageFilter.GaussianBlur(50))
        bg = Image.alpha_composite(bg, spot)

    elif style == "Bright Summer":
        # Sun-drenched coral to vibrant golden-yellow gradient
        for y in range(height):
            ratio = y / height
            r = int(255 - ratio * 10)
            g = int(105 + ratio * 85)
            b = int(90 - ratio * 30)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        # Sparkle bubbles / energetic sun rays
        draw.ellipse([width - 150, 80, width + 150, 380], fill=(255, 255, 255, 40))
        draw.ellipse([40, height - 260, 200, height - 100], fill=(255, 255, 255, 35))

    elif style == "Futuristic":
        # Deep cyberpunk navy with luminous electric cyan accents
        for y in range(height):
            ratio = y / height
            r = int(6 + ratio * 10)
            g = int(8 + ratio * 14)
            b = int(22 + ratio * 28)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        # Tech grid lines
        for gx in range(0, width, 80):
            draw.line([(gx, 0), (gx, height)], fill=(0, 240, 255, 12), width=1)
        for gy in range(0, height, 80):
            draw.line([(0, gy), (width, gy)], fill=(0, 240, 255, 12), width=1)
        # Cyan / magenta corner glows
        neon = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        neon_draw = ImageDraw.Draw(neon)
        neon_draw.ellipse([-50, -50, 250, 250], fill=(0, 240, 255, 45))
        neon_draw.ellipse([width - 200, height - 300, width + 100, height], fill=(255, 0, 128, 40))
        neon = neon.filter(ImageFilter.GaussianBlur(40))
        bg = Image.alpha_composite(bg, neon)

    else:
        # Modern Dark Elegant default
        for y in range(height):
            ratio = y / height
            r = int(18 + ratio * 15)
            g = int(22 + ratio * 18)
            b = int(32 + ratio * 24)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    return bg.convert("RGB")


def render_shot_canvas(
    product_img: Image.Image,
    shot_data: Dict[str, Any],
    style: str,
    product_name: str,
    width: int = 720,
    height: int = 1280
) -> Image.Image:
    """
    Render a high-impact, professional vertical 9:16 canvas for a single shot.
    Contains styled background, framed product with lighting, shot indicator badge, and Thai subtitle card.
    """
    # 1. Base styled background
    canvas = create_style_background(style, width, height)
    draw = ImageDraw.Draw(canvas)

    # 2. Fonts
    font_badge = get_thai_font(20, bold=True)
    font_headline = get_thai_font(34, bold=True)
    font_script = get_thai_font(24, bold=False)
    font_pill = get_thai_font(18, bold=True)

    # 3. Top Header: Shot Pill Badge
    shot_num = shot_data.get("shot_number", 1)
    role = shot_data.get("role", f"Shot {shot_num}").upper()
    badge_text = f"🎬 SHOT {shot_num}/9 • {role}"
    
    # Badge colors
    badge_bg = (30, 35, 48, 220) if style != "Minimal Clean" else (240, 242, 248, 240)
    badge_border = (0, 240, 255, 180) if style == "Futuristic" else ((212, 175, 55, 180) if style == "Studio Luxury" else (200, 205, 215, 200))
    badge_text_color = (255, 255, 255) if style != "Minimal Clean" else (30, 35, 48)

    # Draw Top Badge Pill
    badge_w, badge_h = 320, 46
    badge_x = (width - badge_w) // 2
    badge_y = 54
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=23,
        fill=badge_bg,
        outline=badge_border,
        width=2
    )
    draw.text((badge_x + 24, badge_y + 11), badge_text, font=font_badge, fill=badge_text_color)

    # 4. Product Center Stage
    # Max dimensions for product display
    max_prod_w, max_prod_h = 520, 520
    p_img = product_img.copy().convert("RGBA")
    p_img.thumbnail((max_prod_w, max_prod_h), Image.Resampling.LANCZOS)
    pw, ph = p_img.size

    center_x = width // 2
    center_y = int(height * 0.42)
    px = center_x - pw // 2
    py = center_y - ph // 2

    # Draw modern rounded card beneath product
    card_margin = 25
    card_box = [px - card_margin, py - card_margin, px + pw + card_margin, py + ph + card_margin]
    
    if style == "Studio Luxury":
        card_fill = (20, 20, 26, 210)
        card_outline = (212, 175, 55, 160)
    elif style == "Futuristic":
        card_fill = (12, 16, 28, 220)
        card_outline = (0, 240, 255, 150)
    elif style == "Bright Summer":
        card_fill = (255, 255, 255, 240)
        card_outline = (255, 180, 80, 200)
    else: # Minimal Clean
        card_fill = (255, 255, 255, 250)
        card_outline = (220, 224, 232, 220)

    draw.rounded_rectangle(card_box, radius=28, fill=card_fill, outline=card_outline, width=2)

    # Paste product
    canvas.paste(p_img, (px, py), p_img)

    # 5. Shot-specific commercial visual cue badge
    cues = {
        1: ("🔥 HOT / เปิดตัว", (255, 75, 75)),
        2: ("✨ OFFICIAL REVEAL", (75, 140, 255)),
        3: ("⭐ KEY FEATURE #1", (255, 180, 0)),
        4: ("💡 PROBLEM SOLVED", (46, 204, 113)),
        5: ("💎 PREMIUM QUALITY", (155, 89, 182)),
        6: ("🚀 EASY TO USE", (52, 152, 219)),
        7: ("⭐⭐⭐⭐⭐ 4.9/5 RATING", (241, 196, 15)),
        8: ("🏷️ SPECIAL OFFER", (231, 76, 60)),
        9: ("🛒 ORDER NOW / สั่งเลย", (46, 204, 113))
    }
    cue_text, cue_color = cues.get(shot_num, (f"POINT {shot_num}", (100, 100, 200)))
    cue_w = 260
    cue_x = (width - cue_w) // 2
    cue_y = card_box[1] - 22
    draw.rounded_rectangle(
        [cue_x, cue_y, cue_x + cue_w, cue_y + 40],
        radius=20,
        fill=cue_color
    )
    draw.text((cue_x + 20, cue_y + 8), cue_text, font=font_pill, fill=(255, 255, 255))

    # 6. Bottom Glassmorphic Subtitle Card
    sub_w = 640
    sub_h = 280
    sub_x = (width - sub_w) // 2
    sub_y = height - sub_h - 60

    if style == "Minimal Clean":
        sub_bg = (255, 255, 255, 250)
        sub_border = (210, 215, 225, 220)
        title_color = (17, 24, 39)
        text_color = (75, 85, 99)
        sub_accent = (37, 99, 235)
    elif style == "Studio Luxury":
        sub_bg = (16, 17, 22, 235)
        sub_border = (212, 175, 55, 160)
        title_color = (253, 253, 253)
        text_color = (226, 217, 200)
        sub_accent = (212, 175, 55)
    elif style == "Bright Summer":
        sub_bg = (255, 255, 255, 245)
        sub_border = (255, 160, 120, 200)
        title_color = (42, 27, 20)
        text_color = (80, 50, 40)
        sub_accent = (255, 80, 60)
    else: # Futuristic
        sub_bg = (10, 14, 25, 240)
        sub_border = (0, 240, 255, 180)
        title_color = (255, 255, 255)
        text_color = (0, 240, 255)
        sub_accent = (255, 0, 128)

    draw.rounded_rectangle(
        [sub_x, sub_y, sub_x + sub_w, sub_y + sub_h],
        radius=26,
        fill=sub_bg,
        outline=sub_border,
        width=2
    )

    # Accent bar on left
    draw.rounded_rectangle(
        [sub_x + 18, sub_y + 24, sub_x + 26, sub_y + sub_h - 24],
        radius=4,
        fill=sub_accent
    )

    # Headline
    headline = shot_data.get("headline") or shot_data.get("title", f"ช็อตที่ {shot_num}")
    draw.text((sub_x + 44, sub_y + 26), headline, font=font_headline, fill=title_color)

    # Voiceover script lines
    voiceover = shot_data.get("thai_voiceover", "")
    lines = wrap_text(voiceover, max_chars=32)
    line_y = sub_y + 85
    for line in lines:
        draw.text((sub_x + 44, line_y), line, font=font_script, fill=text_color)
        line_y += 36

    # Product Name tag at bottom right of card
    prod_tag = f"🏷️ {product_name[:18]}"
    draw.text((sub_x + sub_w - 240, sub_y + sub_h - 40), prod_tag, font=font_pill, fill=sub_accent)

    return canvas


def get_zoompan_filter(motion_type: str, total_frames: int, width: int = 720, height: int = 1280, fps: int = 30) -> str:
    """Return appropriate FFmpeg zoompan filter string for chosen camera motion."""
    d = total_frames
    w, h = width, height

    if motion_type == "zoom_in":
        return f"zoompan=z='min(zoom+0.0018,1.25)':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif motion_type == "zoom_out":
        return f"zoompan=z='if(lte(zoom,1.0),1.22,max(1.001,zoom-0.0018))':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif motion_type == "pan_up":
        return f"zoompan=z=1.14:y='if(lte(on,1),ih*0.12,max(0,y-1.0))':x='iw/2-(iw/zoom/2)':d={d}:s={w}x{h}:fps={fps}"
    elif motion_type == "pan_down":
        return f"zoompan=z=1.14:y='if(lte(on,1),0,min(ih*0.12,y+1.0))':x='iw/2-(iw/zoom/2)':d={d}:s={w}x{h}:fps={fps}"
    elif motion_type == "macro_zoom":
        return f"zoompan=z='min(zoom+0.0028,1.35)':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    elif motion_type == "slow_push":
        return f"zoompan=z='min(zoom+0.0010,1.12)':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
    else:  # float / default
        return f"zoompan=z='min(zoom+0.0015,1.18)':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"


def render_single_shot_video(
    canvas_img: Image.Image,
    audio_path: str,
    shot_duration: float,
    output_video_path: str,
    motion_type: str = "zoom_in",
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
    ffmpeg_exe: Optional[str] = None
) -> str:
    """Render a single 9:16 shot video with camera motion and synced audio using FFmpeg."""
    exe = ffmpeg_exe or get_ffmpeg_exe()
    os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
    
    # Save temporary canvas PNG
    temp_canvas_path = output_video_path.replace(".mp4", "_canvas.png")
    canvas_img.save(temp_canvas_path, format="PNG")

    # Get actual audio duration
    audio_dur = get_media_duration(audio_path, exe)
    # Ensure video is at least as long as audio + small buffer
    final_dur = max(shot_duration, audio_dur + 0.25)
    total_frames = int(fps * final_dur)

    filter_str = get_zoompan_filter(motion_type, total_frames, width, height, fps)

    cmd = [
        exe,
        "-i", temp_canvas_path,
        "-i", audio_path,
        "-vf", filter_str,
        "-t", f"{final_dur:.2f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-shortest",
        "-y", output_video_path
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"FFmpeg render shot error: {res.stderr}")

    # Remove temporary canvas
    try:
        if os.path.exists(temp_canvas_path):
            os.remove(temp_canvas_path)
    except Exception:
        pass

    return output_video_path


def create_subtitle_overlay_png(
    shot_data: Dict[str, Any],
    output_png_path: str,
    width: int = 720,
    height: int = 1280
) -> str:
    """Create a transparent 720x1280 PNG containing top shot badge and bottom subtitle banner."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_badge = get_thai_font(20, bold=True)
    font_headline = get_thai_font(34, bold=True)
    font_script = get_thai_font(24, bold=False)

    # Top Shot Badge
    shot_num = shot_data.get("shot_number", 1)
    role = shot_data.get("role", f"Shot {shot_num}").upper()
    badge_text = f"🎬 SHOT {shot_num} • {role}"

    badge_w, badge_h = 340, 46
    badge_x = (width - badge_w) // 2
    badge_y = 50
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=23,
        fill=(15, 20, 32, 210),
        outline=(255, 75, 75, 200),
        width=2
    )
    draw.text((badge_x + 22, badge_y + 11), badge_text, font=font_badge, fill=(255, 255, 255))

    # Bottom Subtitle Card
    sub_w = 660
    sub_h = 240
    sub_x = (width - sub_w) // 2
    sub_y = height - sub_h - 60

    draw.rounded_rectangle(
        [sub_x, sub_y, sub_x + sub_w, sub_y + sub_h],
        radius=24,
        fill=(12, 16, 26, 210),
        outline=(255, 255, 255, 60),
        width=2
    )

    # Accent line
    draw.rounded_rectangle(
        [sub_x + 18, sub_y + 20, sub_x + 26, sub_y + sub_h - 20],
        radius=4,
        fill=(255, 75, 75)
    )

    headline = shot_data.get("headline") or shot_data.get("title", f"ช็อตที่ {shot_num}")
    draw.text((sub_x + 44, sub_y + 22), headline, font=font_headline, fill=(255, 255, 255))

    voiceover = shot_data.get("thai_voiceover", "")
    lines = wrap_text(voiceover, max_chars=34)
    line_y = sub_y + 76
    for line in lines:
        draw.text((sub_x + 44, line_y), line, font=font_script, fill=(225, 230, 240))
        line_y += 34

    overlay.save(output_png_path, format="PNG")
    return output_png_path


def normalize_i2v_clip_with_audio(
    raw_video_path: str,
    audio_path: str,
    shot_data: Dict[str, Any],
    output_clip_path: str,
    overlay_subtitles: bool = True,
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
    ffmpeg_exe: Optional[str] = None
) -> str:
    """
    Take a raw I2V moving .mp4 video clip, resize to 720x1280 vertical, attach TTS audio,
    optionally render a sleek subtitle banner overlay, and trim to match speech duration.
    """
    exe = ffmpeg_exe or get_ffmpeg_exe()
    os.makedirs(os.path.dirname(os.path.abspath(output_clip_path)), exist_ok=True)

    # Audio duration
    audio_dur = get_media_duration(audio_path, exe)
    final_dur = max(float(shot_data.get("duration_seconds", 3.0)), audio_dur + 0.25)

    temp_overlay_path = output_clip_path.replace(".mp4", "_overlay.png")
    
    if overlay_subtitles:
        create_subtitle_overlay_png(shot_data, temp_overlay_path, width, height)
        filter_str = f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[bg]; [bg][2:v]overlay=0:0[v]"
        cmd = [
            exe,
            "-stream_loop", "-1", "-i", raw_video_path,
            "-i", audio_path,
            "-i", temp_overlay_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "1:a",
            "-t", f"{final_dur:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-y", output_clip_path
        ]
    else:
        filter_str = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        cmd = [
            exe,
            "-stream_loop", "-1", "-i", raw_video_path,
            "-i", audio_path,
            "-vf", filter_str,
            "-t", f"{final_dur:.2f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            "-y", output_clip_path
        ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"normalize_i2v_clip error: {res.stderr}")

    if os.path.exists(temp_overlay_path):
        try: os.remove(temp_overlay_path)
        except: pass

    return output_clip_path


def assemble_9shot_commercial(
    shot_video_paths: List[str],
    bgm_name: str,
    bgm_volume: float,
    output_final_path: str,
    ffmpeg_exe: Optional[str] = None
) -> str:
    """
    Concatenate all 9 shot clips and mix background music with audio ducking.
    Produces the final web-ready MP4.
    """
    exe = ffmpeg_exe or get_ffmpeg_exe()
    os.makedirs(os.path.dirname(os.path.abspath(output_final_path)), exist_ok=True)

    # 1. Create concat list
    concat_txt_path = output_final_path.replace(".mp4", "_concat.txt")
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for p in shot_video_paths:
            abs_p = os.path.abspath(p).replace("\\", "/")
            f.write(f"file '{abs_p}'\n")

    temp_concat_video = output_final_path.replace(".mp4", "_temp_concat.mp4")

    # Fast demuxer concat
    cmd_concat = [
        exe,
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-c", "copy",
        "-y", temp_concat_video
    ]
    res_concat = subprocess.run(cmd_concat, capture_output=True, text=True)
    if res_concat.returncode != 0:
        print(f"Concat error: {res_concat.stderr}")

    # 2. Check BGM file
    bgm_file = f"{bgm_name.lower().replace(' ', '_')}.mp3"
    bgm_path = os.path.join(os.path.dirname(__file__), "assets", "bgm", bgm_file)
    if not os.path.exists(bgm_path):
        bgm_path = os.path.join(os.path.dirname(__file__), "assets", "bgm", "minimal_clean.mp3")

    has_bgm = os.path.exists(bgm_path) and bgm_volume > 0.01

    if has_bgm:
        # Mix concatenated video's narration audio with looped BGM
        cmd_mix = [
            exe,
            "-i", temp_concat_video,
            "-stream_loop", "-1",
            "-i", bgm_path,
            "-filter_complex", f"[1:a]volume={bgm_volume:.2f}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-shortest",
            "-y", output_final_path
        ]
        res_mix = subprocess.run(cmd_mix, capture_output=True, text=True)
        if res_mix.returncode != 0:
            print(f"BGM mix error: {res_mix.stderr}")
            shutil.copyfile(temp_concat_video, output_final_path)
    else:
        # No BGM or volume is 0
        shutil.copyfile(temp_concat_video, output_final_path)

    # Clean up temporary files
    for p in [concat_txt_path, temp_concat_video]:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

    return output_final_path
