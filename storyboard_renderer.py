# -*- coding: utf-8 -*-
"""
storyboard_renderer.py - Renders a single, high-resolution 9-panel (3x3 grid) Storyboard Sheet
from the uploaded product image and Gemini AI analysis.
"""

import os
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import video_engine


def wrap_thai_text(text: str, max_chars: int = 30) -> List[str]:
    """Clean wrapping for Thai text captions."""
    if len(text) <= max_chars:
        return [text]
    lines = []
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
        for i in range(0, len(text), max_chars):
            lines.append(text[i:i + max_chars])
    return lines[:3]


def render_panel_visual(
    product_img: Image.Image,
    shot_data: Dict[str, Any],
    width: int = 560,
    height: int = 340
) -> Image.Image:
    """Render the camera frame for a specific shot with unique lighting and framing."""
    shot_num = shot_data.get("shot_number", 1)
    
    # 1. Base frame background
    frame = Image.new("RGBA", (width, height), (12, 15, 24, 255))
    draw = ImageDraw.Draw(frame)

    # Ambient gradients based on shot number
    if shot_num == 1: # Hook: Dramatic dark spotlight
        center_x, center_y = width // 2, height // 2
        for r in range(160, 0, -20):
            alpha = int(45 * (1 - r / 160))
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=(255, 75, 75, alpha))
    elif shot_num == 2: # Reveal: Golden studio glow
        center_x, center_y = width // 2, int(height * 0.6)
        draw.ellipse([center_x - 180, center_y - 120, center_x + 180, center_y + 120], fill=(212, 175, 55, 35))
    elif shot_num in [3, 5]: # Feature / Macro: Cyan tech glow
        center_x, center_y = width // 2, height // 2
        draw.ellipse([center_x - 140, center_y - 140, center_x + 140, center_y + 140], fill=(0, 240, 255, 30))
    elif shot_num == 8: # Special Offer: Warm amber celebration
        draw.rectangle([0, 0, width, height], fill=(35, 25, 20, 255))
    elif shot_num == 9: # Outro: Clean hero aura
        center_x, center_y = width // 2, height // 2
        draw.ellipse([center_x - 190, center_y - 190, center_x + 190, center_y + 190], fill=(46, 204, 113, 35))

    # 2. Product placement & scaling per shot
    prod = product_img.copy().convert("RGBA")
    
    if shot_num in [3, 5]: # Macro: extreme scale
        max_size = int(height * 1.25)
    elif shot_num == 1: # Hook: dynamic close-up
        max_size = int(height * 0.95)
    elif shot_num in [6, 7]: # Lifestyle/Environment: slightly smaller in context
        max_size = int(height * 0.72)
    else: # Hero standard
        max_size = int(height * 0.85)

    prod.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    pw, ph = prod.size

    # Position product
    px = (width - pw) // 2
    py = (height - ph) // 2

    # Pedestal for shot 2
    if shot_num == 2:
        ped_w, ped_h = 240, 36
        ped_x = (width - ped_w) // 2
        ped_y = py + ph - 16
        draw.ellipse([ped_x, ped_y, ped_x + ped_w, ped_y + ped_h], fill=(220, 225, 235, 200), outline=(212, 175, 55, 255), width=2)

    # Soft drop shadow
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shadow)
    sh_draw.ellipse([px - 5, py + ph - 15, px + pw + 5, py + ph + 20], fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    frame = Image.alpha_composite(frame, shadow)

    # Paste product
    frame.paste(prod, (px, py), prod)

    # 3. Viewfinder Camera Overlays
    cam_draw = ImageDraw.Draw(frame)
    # Viewfinder corner brackets
    c_len, c_col = 18, (255, 255, 255, 120)
    # Top-left
    cam_draw.line([(14, 14), (14 + c_len, 14)], fill=c_col, width=2)
    cam_draw.line([(14, 14), (14, 14 + c_len)], fill=c_col, width=2)
    # Top-right
    cam_draw.line([(width - 14, 14), (width - 14 - c_len, 14)], fill=c_col, width=2)
    cam_draw.line([(width - 14, 14), (width - 14, 14 + c_len)], fill=c_col, width=2)
    # Bottom-left
    cam_draw.line([(14, height - 14), (14 + c_len, height - 14)], fill=c_col, width=2)
    cam_draw.line([(14, height - 14), (14, height - 14 - c_len)], fill=c_col, width=2)
    # Bottom-right
    cam_draw.line([(width - 14, height - 14), (width - 14 - c_len, height - 14)], fill=c_col, width=2)
    cam_draw.line([(width - 14, height - 14), (width - 14, height - 14 - c_len)], fill=c_col, width=2)

    # Center crosshair
    cx, cy = width // 2, height // 2
    cam_draw.line([(cx - 8, cy), (cx + 8, cy)], fill=(255, 255, 255, 60), width=1)
    cam_draw.line([(cx, cy - 8), (cx, cy + 8)], fill=(255, 255, 255, 60), width=1)

    # Shot 9: Add "ORDER NOW" badge
    if shot_num == 9:
        font_cta = video_engine.get_thai_font(18, bold=True)
        cam_draw.rounded_rectangle([width - 150, height - 42, width - 20, height - 14], radius=14, fill=(46, 204, 113, 230))
        cam_draw.text((width - 138, height - 38), "🛒 ORDER NOW", font=font_cta, fill=(255, 255, 255))

    return frame.convert("RGB")


def render_9grid_storyboard_image(
    product_img: Image.Image,
    storyboard_data: Dict[str, Any],
    output_path: str = "output/storyboard_9grid.png"
) -> str:
    """
    Renders a master 9-panel storyboard sheet (3x3 grid) into a single high-resolution image file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Master Canvas Dimensions: 2000 x 2360 px
    canvas_w, canvas_h = 2000, 2360
    board = Image.new("RGB", (canvas_w, canvas_h), (12, 15, 24))
    draw = ImageDraw.Draw(board)

    # Load high quality Thai fonts
    font_header_title = video_engine.get_thai_font(46, bold=True)
    font_header_sub = video_engine.get_thai_font(24, bold=False)
    font_panel_badge = video_engine.get_thai_font(19, bold=True)
    font_panel_head = video_engine.get_thai_font(25, bold=True)
    font_panel_cam = video_engine.get_thai_font(18, bold=True)
    font_panel_script = video_engine.get_thai_font(20, bold=False)
    font_footer = video_engine.get_thai_font(18, bold=False)

    # 1. Header Section
    product_name = storyboard_data.get("product_name", "สินค้าของคุณ")
    draw.text((60, 45), f"🎬 COMMERCIAL STORYBOARD: 9-SHOT FORMULA", font=font_header_title, fill=(255, 255, 255))
    
    concept = storyboard_data.get("concept_summary", f"โครงสร้างโฆษณาสินค้า 9 ช่องสำหรับ {product_name}")
    header_sub = f"📦 สินค้า: {product_name}  |  🤖 สร้างด้วย Google Gemini AI  |  ⏱️ 9 ช็อตมาตรฐานสากล"
    draw.text((60, 110), header_sub, font=font_header_sub, fill=(160, 174, 192))
    
    # Header dividing line
    draw.line([(60, 155), (canvas_w - 60, 155)], fill=(45, 55, 72), width=2)

    # 2. 3x3 Grid Layout Configuration
    start_x = 60
    start_y = 180
    grid_spacing_x = 35
    grid_spacing_y = 35

    panel_w = 600
    panel_h = 670

    shots = storyboard_data.get("shots", [])

    badge_colors = {
        1: (255, 75, 75),   # Hook
        2: (212, 175, 55),  # Reveal
        3: (0, 210, 255),   # Feature 1
        4: (75, 140, 255),  # Problem Solving
        5: (155, 89, 182),  # Texture
        6: (241, 196, 15),  # Lifestyle
        7: (52, 152, 219),  # Environment
        8: (230, 126, 34),  # Special Offer
        9: (46, 204, 113)   # CTA Outro
    }

    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            if idx >= len(shots):
                continue
            shot = shots[idx]
            shot_num = shot.get("shot_number", idx + 1)

            px = start_x + col * (panel_w + grid_spacing_x)
            py = start_y + row * (panel_h + grid_spacing_y)

            # Draw Panel Card Box
            draw.rounded_rectangle(
                [px, py, px + panel_w, py + panel_h],
                radius=18,
                fill=(20, 25, 38),
                outline=(45, 55, 75),
                width=2
            )

            # Panel Pill Header
            badge_col = badge_colors.get(shot_num, (100, 100, 200))
            role = shot.get("role", f"Shot {shot_num}").upper()
            badge_text = f"SHOT {shot_num}/9 • {role}"

            pill_w = 280
            draw.rounded_rectangle(
                [px + 18, py + 16, px + 18 + pill_w, py + 48],
                radius=16,
                fill=badge_col
            )
            draw.text((px + 32, py + 21), badge_text, font=font_panel_badge, fill=(255, 255, 255))

            # Duration tag on top-right of panel
            dur_text = f"⏱️ {shot.get('duration_seconds', 3.0)}s"
            draw.text((px + panel_w - 95, py + 22), dur_text, font=font_panel_cam, fill=(160, 174, 192))

            # Camera Viewfinder Visual
            vis_w = panel_w - 36
            vis_h = 320
            visual_img = render_panel_visual(product_img, shot, width=vis_w, height=vis_h)
            board.paste(visual_img, (px + 18, py + 62))

            # Border around camera frame
            draw.rounded_rectangle(
                [px + 18, py + 62, px + 18 + vis_w, py + 62 + vis_h],
                radius=10,
                outline=(60, 75, 100),
                width=2
            )

            # Camera Motion Indicator
            cam_motion = shot.get("camera_motion", "zoom_in").replace("_", " ").title()
            cam_text = f"🎥 Camera: {cam_motion}"
            draw.text((px + 22, py + 395), cam_text, font=font_panel_cam, fill=(0, 240, 255))

            # Headline (Thai)
            headline = shot.get("headline", shot.get("title", f"ช็อตที่ {shot_num}"))
            draw.text((px + 22, py + 425), headline, font=font_panel_head, fill=(255, 255, 255))

            # Script / Voiceover (Thai)
            voiceover = shot.get("thai_voiceover", "")
            script_lines = wrap_thai_text(voiceover, max_chars=36)
            s_y = py + 465
            draw.text((px + 22, s_y), "🗣️ Voiceover:", font=font_panel_cam, fill=(212, 175, 55))
            s_y += 28
            for line in script_lines:
                draw.text((px + 22, s_y), line, font=font_panel_script, fill=(210, 218, 230))
                s_y += 30

    # 3. Footer Section
    draw.line([(60, canvas_h - 70), (canvas_w - 60, canvas_h - 70)], fill=(45, 55, 72), width=1)
    footer_text = "✨ Generated with Google Gemini API • 9-Panel Commercial Storyboard Master Sheet • Ready for Production"
    draw.text((60, canvas_h - 50), footer_text, font=font_footer, fill=(120, 135, 155))

    # Save final high-res PNG
    board.save(output_path, format="PNG", quality=95)
    return output_path
