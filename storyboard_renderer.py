# -*- coding: utf-8 -*-
"""
storyboard_renderer.py - Renders a true 9-scene narrative Storyboard Master Sheet.
Each panel is a distinct visual illustration depicting the character's story journey:
Problem -> Frustration -> Discovery -> Texture -> Application -> Glow -> Confidence -> Admiration -> Outro CTA.
"""

import os
import math
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import video_engine


def wrap_thai_text(text: str, max_chars: int = 34) -> List[str]:
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


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r_outer: float = 9, r_inner: float = 4, fill=(255, 215, 100)):
    """Draw crisp vector star polygon without font glyph dependencies."""
    points = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill)


def render_scene_illustration(
    shot_num: int,
    product_img: Image.Image,
    width: int = 560,
    height: int = 340
) -> Image.Image:
    """
    Renders a dedicated, cinematic storyboard illustration for each of the 9 narrative story scenes.
    Every panel depicts a completely different scene, angle, and action.
    """
    canvas = Image.new("RGBA", (width, height), (15, 18, 28, 255))
    draw = ImageDraw.Draw(canvas)

    cx, cy = width // 2, height // 2

    # -------------------------------------------------------------
    # PANEL 1: THE PROBLEM (ตื่นนอน ส่องกระจกเจอปัญหา)
    # Cool moody dim blue, mirror frame, stressed character silhouette
    # -------------------------------------------------------------
    if shot_num == 1:
        # Dim bedroom / bathroom background
        for y in range(height):
            ratio = y / height
            draw.line([(0, y), (width, y)], fill=(int(10 + ratio*15), int(14 + ratio*18), int(30 + ratio*25), 255))
        # Mirror outline
        draw.ellipse([cx - 150, 30, cx + 150, height - 30], outline=(80, 100, 140, 160), width=3)
        draw.ellipse([cx - 142, 38, cx + 142, height - 38], fill=(20, 26, 45, 200))
        # Character silhouette in mirror looking tired
        head_x, head_y = cx, cy - 20
        draw.ellipse([head_x - 45, head_y - 50, head_x + 45, head_y + 40], fill=(45, 55, 80)) # Head
        draw.polygon([(head_x - 80, height - 20), (head_x + 80, height - 20), (head_x + 50, head_y + 35), (head_x - 50, head_y + 35)], fill=(35, 45, 70)) # Shoulders
        # Stress / dullness markers
        draw.arc([head_x - 25, head_y - 5, head_x + 25, head_y + 25], start=180, end=360, fill=(180, 80, 80), width=3) # Frown
        draw.text((head_x + 60, head_y - 40), "หมองคล้ำ ไม่สดใส", font=video_engine.get_thai_font(18, bold=True), fill=(255, 110, 110))
        draw.text((head_x - 145, head_y - 20), "อ่อนล้า ขาดพลัง", font=video_engine.get_thai_font(18, bold=True), fill=(160, 185, 220))

    # -------------------------------------------------------------
    # PANEL 2: THE FRUSTRATION (ลองมาหลายวิธี โต๊ะเครื่องแป้งรก กังวลใจ)
    # Dressing table, cosmetics clutter, hands holding face
    # -------------------------------------------------------------
    elif shot_num == 2:
        for y in range(height):
            ratio = y / height
            draw.line([(0, y), (width, y)], fill=(int(25 + ratio*10), int(15 + ratio*10), int(22 + ratio*15), 255))
        # Dressing table surface
        draw.rectangle([0, height - 90, width, height], fill=(35, 30, 40))
        draw.line([(0, height - 90), (width, height - 90)], fill=(70, 60, 80), width=2)
        # Cluttered cosmetics silhouettes on table
        draw.rectangle([60, height - 150, 95, height - 90], fill=(60, 50, 70)) # Bottle 1
        draw.rectangle([110, height - 130, 140, height - 90], fill=(50, 45, 65)) # Bottle 2
        draw.ellipse([155, height - 120, 195, height - 90], fill=(70, 55, 75)) # Jar
        # Frustrated character profile clutching cheek
        draw.ellipse([cx + 30, 60, cx + 130, 160], fill=(55, 45, 65)) # Head
        draw.polygon([(cx + 10, height - 20), (cx + 170, height - 20), (cx + 140, 155), (cx + 40, 155)], fill=(45, 35, 55))
        # Hand on forehead/cheek frustration tags
        draw.text((cx - 145, 80), "ลองแล้วไม่เห็นผล", font=video_engine.get_thai_font(20, bold=True), fill=(255, 130, 130))
        draw.text((cx - 125, 120), "ขาดความมั่นใจ", font=video_engine.get_thai_font(18, bold=False), fill=(220, 160, 160))

    # -------------------------------------------------------------
    # PANEL 3: THE DISCOVERY (พบกับตัวช่วย สินค้าวางเด่นพร้อมแสงประกาย)
    # Warm golden hopeful beam shining onto the actual product
    # -------------------------------------------------------------
    elif shot_num == 3:
        for y in range(height):
            ratio = y / height
            draw.line([(0, y), (width, y)], fill=(int(18 + ratio*18), int(18 + ratio*18), int(12 + ratio*8), 255))
        # Warm golden light beam from top-left
        beam = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(beam)
        b_draw.polygon([(cx - 80, 0), (cx + 80, 0), (cx + 220, height), (cx - 220, height)], fill=(255, 215, 100, 35))
        beam = beam.filter(ImageFilter.GaussianBlur(15))
        canvas = Image.alpha_composite(canvas, beam)
        draw = ImageDraw.Draw(canvas)

        # Marble pedestal
        draw.ellipse([cx - 130, height - 90, cx + 130, height - 35], fill=(220, 225, 235), outline=(212, 175, 55), width=2)
        # Paste real product
        prod = product_img.copy().convert("RGBA")
        prod.thumbnail((260, 260), Image.Resampling.LANCZOS)
        pw, ph = prod.size
        canvas.paste(prod, (cx - pw//2, height - 75 - ph), prod)
        draw.text((30, 40), "ค้นพบตัวช่วยใหม่!", font=video_engine.get_thai_font(22, bold=True), fill=(255, 220, 100))

    # -------------------------------------------------------------
    # PANEL 4: TEXTURE & MACRO (เปิดฝา หยดเซรั่ม ละอองน้ำแตกตัว)
    # Macro dropper, glistening droplets, golden ripples
    # -------------------------------------------------------------
    elif shot_num == 4:
        # Dark luxury macro background
        draw.rectangle([0, 0, width, height], fill=(12, 16, 26))
        # Dropper pipette illustration
        draw.polygon([(cx - 16, 20), (cx + 16, 20), (cx + 12, 150), (cx - 12, 150)], fill=(220, 225, 235))
        draw.polygon([(cx - 12, 150), (cx + 12, 150), (cx + 5, 200), (cx - 5, 200)], fill=(200, 210, 230))
        # Glass reflection
        draw.line([(cx - 6, 25), (cx - 3, 190)], fill=(255, 255, 255, 180), width=2)
        # Glistening active droplet hanging & falling
        draw.ellipse([cx - 16, 205, cx + 16, 245], fill=(255, 215, 100, 240)) # Main droplet
        draw.ellipse([cx - 8, 260, cx + 8, 280], fill=(255, 225, 130, 220)) # Falling drop
        # Ripple circles on surface below
        draw.ellipse([cx - 120, height - 60, cx + 120, height - 10], outline=(255, 215, 100, 140), width=2)
        draw.ellipse([cx - 70, height - 48, cx + 70, height - 22], outline=(255, 235, 150, 180), width=2)
        # Feature text tag
        draw.text((30, 40), "ซูมเนื้อสัมผัสเข้มข้น", font=video_engine.get_thai_font(20, bold=True), fill=(0, 240, 255))
        draw.text((30, 75), "ซึมไว ไม่เหนอะหนะ", font=video_engine.get_thai_font(18, bold=False), fill=(200, 220, 240))

    # -------------------------------------------------------------
    # PANEL 5: APPLICATION (ทาลงบนผิวหน้า สัมผัสนุ่มนวล สบายผิว)
    # Gentle hand applying serum to glowing cheek, soothing motion arcs
    # -------------------------------------------------------------
    elif shot_num == 5:
        draw.rectangle([0, 0, width, height], fill=(18, 22, 34))
        # Soft warm glow on face
        draw.ellipse([cx - 80, 50, cx + 160, 290], fill=(255, 210, 180, 50))
        # Cheek profile contour
        draw.arc([cx - 70, 70, cx + 130, 270], start=90, end=270, fill=(245, 200, 180), width=3)
        # Hand / Fingers gently patting
        hand_col = (255, 220, 200)
        draw.polygon([(cx - 140, height - 20), (cx - 70, 170), (cx - 30, 160), (cx - 100, height - 20)], fill=hand_col)
        draw.ellipse([cx - 35, 150, cx - 15, 175], fill=hand_col) # Finger tip touching cheek
        # Soothing motion wave arcs
        draw.arc([cx - 5, 135, cx + 45, 185], start=0, end=180, fill=(0, 240, 255), width=2)
        draw.arc([cx + 10, 120, cx + 70, 180], start=0, end=180, fill=(255, 220, 100), width=2)
        # Text
        draw.text((30, 35), "ทาบำรุงอย่างนุ่มนวล", font=video_engine.get_thai_font(20, bold=True), fill=(255, 220, 180))
        draw.text((30, 70), "ผ่อนคลาย สบายผิว", font=video_engine.get_thai_font(18, bold=False), fill=(180, 220, 240))

    # -------------------------------------------------------------
    # PANEL 6: INSTANT GLOW (ผิวฉ่ำวาว อิ่มน้ำทันที ออร่าเปล่งประกาย)
    # Radiant smiling face in mirror, sparkle stars, hydration aura
    # -------------------------------------------------------------
    elif shot_num == 6:
        draw.rectangle([0, 0, width, height], fill=(20, 24, 40))
        # Aura halo
        halo = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        h_draw = ImageDraw.Draw(halo)
        h_draw.ellipse([cx - 140, 40, cx + 140, height - 40], fill=(255, 220, 100, 45))
        h_draw.ellipse([cx - 90, 70, cx + 90, height - 70], fill=(0, 240, 255, 40))
        halo = halo.filter(ImageFilter.GaussianBlur(25))
        canvas = Image.alpha_composite(canvas, halo)
        draw = ImageDraw.Draw(canvas)
        # Happy glowing character silhouette
        draw.ellipse([cx - 45, 60, cx + 45, 160], fill=(255, 220, 200)) # Glowing head
        draw.polygon([(cx - 85, height - 20), (cx + 85, height - 20), (cx + 50, 155), (cx - 50, 155)], fill=(60, 75, 110))
        # Smiling lips
        draw.arc([cx - 20, 115, cx + 20, 145], start=0, end=180, fill=(240, 80, 100), width=3)
        # Sparkle star bursts
        for sx, sy in [(cx - 90, 80), (cx + 100, 70), (cx - 70, 190), (cx + 90, 180)]:
            draw.line([(sx - 12, sy), (sx + 12, sy)], fill=(255, 255, 255), width=2)
            draw.line([(sx, sy - 12), (sx, sy + 12)], fill=(255, 255, 255), width=2)
        # Text
        draw.text((30, 35), "ผิวฉ่ำโกลว์ อิ่มน้ำทันตา", font=video_engine.get_thai_font(20, bold=True), fill=(255, 220, 100))

    # -------------------------------------------------------------
    # PANEL 7: CONFIDENT LIFESTYLE (ก้าวออกจากบ้านอย่างมั่นใจ ท้าแดด)
    # Bright sunny daylight, outdoor city skyline, confident walking figure
    # -------------------------------------------------------------
    elif shot_num == 7:
        # Sunny daylight sky gradient
        for y in range(height):
            ratio = y / height
            draw.line([(0, y), (width, y)], fill=(int(40 + ratio*60), int(120 + ratio*80), int(210 + ratio*30), 255))
        # Sun flare top-right
        draw.ellipse([width - 130, -30, width + 50, 150], fill=(255, 245, 180, 220))
        draw.ellipse([width - 160, -60, width + 80, 180], outline=(255, 230, 120, 120), width=4)
        # City skyline silhouette
        draw.rectangle([40, height - 160, 110, height], fill=(30, 45, 75))
        draw.rectangle([130, height - 190, 200, height], fill=(25, 38, 65))
        draw.rectangle([220, height - 140, 300, height], fill=(35, 50, 80))
        # Confident character walking in stylish silhouette
        draw.ellipse([cx + 60, height - 230, cx + 110, height - 170], fill=(255, 255, 255)) # Head
        draw.polygon([(cx + 40, height - 10), (cx + 130, height - 10), (cx + 105, height - 170), (cx + 65, height - 170)], fill=(240, 245, 255)) # Body
        # Text
        draw.text((30, 35), "สวยมั่นใจ ท้าแดดทุกวัน", font=video_engine.get_thai_font(20, bold=True), fill=(255, 255, 255))
        draw.text((30, 70), "พร้อมลุยทุกกิจกรรม", font=video_engine.get_thai_font(18, bold=False), fill=(220, 240, 255))

    # -------------------------------------------------------------
    # PANEL 8: SOCIAL ADMIRATION (คนรอบข้างทัก ชื่นชมในความเปลี่ยนแปลง)
    # Friends gathered in cafe/work, thumbs up, praise speech bubbles
    # -------------------------------------------------------------
    elif shot_num == 8:
        draw.rectangle([0, 0, width, height], fill=(28, 22, 38))
        # Multiple friendly character silhouettes
        draw.ellipse([80, 110, 140, 180], fill=(60, 50, 80)) # Friend 1
        draw.polygon([(50, height - 20), (170, height - 20), (130, 175), (90, 175)], fill=(50, 40, 70))
        draw.ellipse([width - 140, 110, width - 80, 180], fill=(60, 50, 80)) # Friend 2
        draw.polygon([(width - 170, height - 20), (width - 50, height - 20), (width - 90, 175), (width - 130, 175)], fill=(50, 40, 70))
        # Main smiling hero in center
        draw.ellipse([cx - 40, 80, cx + 40, 170], fill=(255, 220, 200))
        draw.polygon([(cx - 75, height - 20), (cx + 75, height - 20), (cx + 45, 165), (cx - 45, 165)], fill=(230, 100, 140))
        # Compliment speech bubble
        bubble_x, bubble_y = cx - 110, 20
        draw.rounded_rectangle([bubble_x, bubble_y, bubble_x + 220, bubble_y + 45], radius=12, fill=(255, 255, 255))
        draw.polygon([(cx, bubble_y + 45), (cx - 10, bubble_y + 45), (cx - 5, bubble_y + 55)], fill=(255, 255, 255))
        draw.text((bubble_x + 18, bubble_y + 10), "'หน้าใสขึ้นมาก ไปทำอะไรมา?!'", font=video_engine.get_thai_font(16, bold=True), fill=(30, 30, 50))
        # Praise note
        draw.text((50, 60), "เสียงชื่นชมจากเพื่อนๆ", font=video_engine.get_thai_font(18, bold=True), fill=(255, 215, 100))

    # -------------------------------------------------------------
    # PANEL 9: HERO PACKSHOT & CTA (ถือสินค้าคู่รอยยิ้ม ปิดการขาย สั่งซื้อด่วน)
    # Spotlight, hero product presentation, 5-star rating, CTA order badge
    # -------------------------------------------------------------
    else:
        # Grand stage spotlight
        draw.rectangle([0, 0, width, height], fill=(15, 20, 35))
        center_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        cg_draw = ImageDraw.Draw(center_glow)
        cg_draw.ellipse([cx - 180, cy - 130, cx + 180, cy + 130], fill=(46, 204, 113, 50))
        cg_draw.ellipse([cx - 100, cy - 80, cx + 100, cy + 80], fill=(255, 215, 100, 45))
        center_glow = center_glow.filter(ImageFilter.GaussianBlur(30))
        canvas = Image.alpha_composite(canvas, center_glow)
        draw = ImageDraw.Draw(canvas)

        # Real Product Packshot
        prod = product_img.copy().convert("RGBA")
        prod.thumbnail((260, 260), Image.Resampling.LANCZOS)
        pw, ph = prod.size
        canvas.paste(prod, (cx - pw//2, cy - ph//2 - 20), prod)

        # 5-Star Rating badge (vector stars)
        star_start_x = cx - 65
        for s_i in range(5):
            draw_star(draw, star_start_x + s_i * 18, 30, r_outer=7, r_inner=3, fill=(255, 215, 100))
        draw.text((star_start_x + 95, 20), "4.9 / 5.0", font=video_engine.get_thai_font(18, bold=True), fill=(255, 215, 100))

        # Order Now CTA Button
        btn_w, btn_h = 240, 45
        btn_x = (width - btn_w) // 2
        btn_y = height - 65
        draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], radius=22, fill=(46, 204, 113))
        draw.text((btn_x + 40, btn_y + 9), "สั่งซื้อเลย ตอนนี้!", font=video_engine.get_thai_font(20, bold=True), fill=(255, 255, 255))

    # Viewfinder border brackets on all panels
    c_len, c_col = 16, (255, 255, 255, 100)
    draw.line([(12, 12), (12 + c_len, 12)], fill=c_col, width=2)
    draw.line([(12, 12), (12, 12 + c_len)], fill=c_col, width=2)
    draw.line([(width - 12, 12), (width - 12 - c_len, 12)], fill=c_col, width=2)
    draw.line([(width - 12, 12), (width - 12, 12 + c_len)], fill=c_col, width=2)
    draw.line([(12, height - 12), (12 + c_len, height - 12)], fill=c_col, width=2)
    draw.line([(12, height - 12), (12, height - 12 - c_len)], fill=c_col, width=2)
    draw.line([(width - 12, height - 12), (width - 12 - c_len, height - 12)], fill=c_col, width=2)
    draw.line([(width - 12, height - 12), (width - 12, height - 12 - c_len)], fill=c_col, width=2)

    return canvas.convert("RGB")


def render_9grid_storyboard_image(
    product_img: Image.Image,
    storyboard_data: Dict[str, Any],
    output_path: str = "output/storyboard_9grid.png"
) -> str:
    """
    Renders the complete 9-Panel Narrative Storyboard Sheet into a single high-resolution image file.
    Each of the 9 panels is a completely distinct scene depicting the story from Problem to Solution & CTA.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Master Canvas: 2000 x 2380 px
    canvas_w, canvas_h = 2000, 2380
    board = Image.new("RGB", (canvas_w, canvas_h), (10, 13, 20))
    draw = ImageDraw.Draw(board)

    # Fonts
    font_header_title = video_engine.get_thai_font(44, bold=True)
    font_header_sub = video_engine.get_thai_font(22, bold=False)
    font_panel_badge = video_engine.get_thai_font(18, bold=True)
    font_panel_head = video_engine.get_thai_font(23, bold=True)
    font_panel_cam = video_engine.get_thai_font(17, bold=True)
    font_panel_script = video_engine.get_thai_font(19, bold=False)
    font_footer = video_engine.get_thai_font(17, bold=False)

    # 1. Header
    product_name = storyboard_data.get("product_name", "สินค้าของคุณ")
    draw.text((60, 40), "COMMERCIAL NARRATIVE STORYBOARD (9-ACT STORY SHEET)", font=font_header_title, fill=(255, 255, 255))
    
    header_sub = f"เรื่องราวโฆษณา: {product_name}  |  วิเคราะห์และเขียนบทด้วย Google Gemini AI  |  สูตรเล่าเรื่อง 9 ตอนจบในรูปเดียว"
    draw.text((60, 100), header_sub, font=font_header_sub, fill=(160, 174, 192))
    
    draw.line([(60, 145), (canvas_w - 60, 145)], fill=(45, 55, 75), width=2)

    # 2. 3x3 Grid Layout (9 Distinct Story Panels)
    start_x = 60
    start_y = 168
    grid_spacing_x = 35
    grid_spacing_y = 35

    panel_w = 600
    panel_h = 680

    shots = storyboard_data.get("shots", [])

    badge_colors = {
        1: (230, 75, 75),   # Act 1: The Problem
        2: (220, 100, 50),  # Act 2: The Frustration
        3: (212, 175, 55),  # Act 3: The Discovery
        4: (0, 210, 255),   # Act 4: Texture & Dropper
        5: (155, 89, 182),  # Act 5: Application
        6: (241, 196, 15),  # Act 6: Instant Glow
        7: (52, 152, 219),  # Act 7: Confident Lifestyle
        8: (230, 126, 34),  # Act 8: Social Admiration
        9: (46, 204, 113)   # Act 9: Outro & Call to Action
    }

    story_acts = {
        1: "ACT 1 • THE PROBLEM (ปัญหา)",
        2: "ACT 2 • FRUSTRATION (กังวลใจ)",
        3: "ACT 3 • DISCOVERY (พบตัวช่วย)",
        4: "ACT 4 • TEXTURE (สัมผัสแรก)",
        5: "ACT 5 • APPLICATION (ใช้จริง)",
        6: "ACT 6 • INSTANT GLOW (ผลลัพธ์)",
        7: "ACT 7 • LIFESTYLE (ชีวิตใหม่)",
        8: "ACT 8 • ADMIRATION (คนทักชม)",
        9: "ACT 9 • OUTRO CTA (ปิดการขาย)"
    }

    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            if idx >= len(shots):
                continue
            shot = shots[idx]
            shot_num = idx + 1

            px = start_x + col * (panel_w + grid_spacing_x)
            py = start_y + row * (panel_h + grid_spacing_y)

            # Panel Box
            draw.rounded_rectangle(
                [px, py, px + panel_w, py + panel_h],
                radius=18,
                fill=(18, 23, 35),
                outline=(45, 55, 75),
                width=2
            )

            # Story Act Badge
            badge_col = badge_colors.get(shot_num, (100, 100, 200))
            act_text = story_acts.get(shot_num, f"ACT {shot_num}")

            draw.rounded_rectangle(
                [px + 18, py + 14, px + 330, py + 46],
                radius=16,
                fill=badge_col
            )
            draw.text((px + 30, py + 19), act_text, font=font_panel_badge, fill=(255, 255, 255))

            # Duration
            dur_text = f"~{shot.get('duration_seconds', 2.0)}s"
            draw.text((px + panel_w - 95, py + 20), dur_text, font=font_panel_cam, fill=(160, 174, 192))

            # Scene Visual Illustration (Distinct for every single panel!)
            vis_w = panel_w - 36
            vis_h = 325
            scene_img = render_scene_illustration(shot_num, product_img, width=vis_w, height=vis_h)
            board.paste(scene_img, (px + 18, py + 58))

            draw.rounded_rectangle(
                [px + 18, py + 58, px + 18 + vis_w, py + 58 + vis_h],
                radius=10,
                outline=(55, 70, 95),
                width=2
            )

            # Scene Type & Camera Info
            scene_type = shot.get("scene_type", "INT. SCENE").upper()
            cam_info = f"SCENE: {scene_type}  |  CAM: {shot.get('camera_motion', 'Camera Motion').replace('_', ' ').title()}"
            draw.text((px + 22, py + 395), cam_info, font=font_panel_cam, fill=(0, 240, 255))

            # Headline (Thai)
            headline = shot.get("headline", shot.get("title", f"ฉากที่ {shot_num}"))
            draw.text((px + 22, py + 425), headline, font=font_panel_head, fill=(255, 255, 255))

            # Narrative Voiceover / Dialogue (Thai)
            voiceover = shot.get("thai_voiceover", "")
            script_lines = wrap_thai_text(voiceover, max_chars=36)
            s_y = py + 465
            draw.text((px + 22, s_y), "[ เรื่องราว / บทพากย์ ]", font=font_panel_cam, fill=(212, 175, 55))
            s_y += 28
            for line in script_lines:
                draw.text((px + 22, s_y), f'"{line}"', font=font_panel_script, fill=(210, 220, 235))
                s_y += 28

            # Action notes
            action_note = shot.get("action_note", shot.get("environment", ""))
            if action_note:
                draw.text((px + 22, py + panel_h - 45), f"ACTION: {action_note[:38]}", font=font_footer, fill=(140, 155, 175))

    # 3. Footer
    draw.line([(60, canvas_h - 65), (canvas_w - 60, canvas_h - 65)], fill=(45, 55, 72), width=1)
    footer_text = "9-Panel Commercial Narrative Storyboard Master Sheet • Powered by Google Gemini AI • Ready for Production"
    draw.text((60, canvas_h - 45), footer_text, font=font_footer, fill=(120, 135, 155))

    # Save final high-res PNG
    board.save(output_path, format="PNG", quality=95)
    return output_path
