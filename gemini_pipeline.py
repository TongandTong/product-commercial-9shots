# -*- coding: utf-8 -*-
"""
gemini_pipeline.py - Module for generating 9-shot commercial storyboards using Google Gemini API.
"""

import json
import os
import re
from typing import Dict, Any, Optional
from PIL import Image
import io

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


SHOT_TEMPLATES = [
    {
        "shot_number": 1,
        "title": "Hook / เปิดตัวดึงดูดสายตา",
        "role": "Hook & Problem Statement",
        "default_ratio": 0.11,
        "camera_motion": "zoom_in",
        "sample_visual": "Dynamic opening close-up of {product_name}, sharp focus, cinematic lighting, eye-catching visual hook",
        "sample_script": "เบื่อไหมกับปัญหาเดิมๆ? พบกับ {product_name}",
        "sample_headline": "สัมผัสความต่างที่เหนือกว่า"
    },
    {
        "shot_number": 2,
        "title": "Product Reveal / เปิดตัวสินค้า",
        "role": "Product Introduction",
        "default_ratio": 0.11,
        "camera_motion": "float",
        "sample_visual": "Elegant beauty reveal shot of {product_name}, rotating gracefully with subtle light reflection",
        "sample_script": "ดีไซน์พรีเมียม ตอบโจทย์ทุกไลฟ์สไตล์",
        "sample_headline": "เปิดตัวนวัตกรรมล่าสุด"
    },
    {
        "shot_number": 3,
        "title": "Feature 1 / จุดเด่นหลักที่ 1",
        "role": "Key Selling Point #1",
        "default_ratio": 0.11,
        "camera_motion": "pan_up",
        "sample_visual": "Macro close-up highlighting key premium ingredient and texture of {product_name}",
        "sample_script": "โดดเด่นด้วย {highlight}",
        "sample_headline": "คุณภาพระดับท็อป"
    },
    {
        "shot_number": 4,
        "title": "Problem-Solving / แก้ไขปัญหาตรงจุด",
        "role": "Solution Demonstration",
        "default_ratio": 0.11,
        "camera_motion": "zoom_out",
        "sample_visual": "Dramatic demonstration visual, showcasing effectiveness and effortless performance",
        "sample_script": "แก้ปัญหาได้จริง เห็นผลลัพธ์ชัดเจน",
        "sample_headline": "ตอบโจทย์ตรงจุด"
    },
    {
        "shot_number": 5,
        "title": "Feature 2 / จุดเด่นที่ 2 & ดีเทล",
        "role": "Key Selling Point #2",
        "default_ratio": 0.11,
        "camera_motion": "macro_zoom",
        "sample_visual": "Detailed texture and craftmanship shot of {product_name}, luxury aesthetic reflections",
        "sample_script": "ใส่ใจในทุกรายละเอียด ใช้งานง่าย",
        "sample_headline": "ประณีตทุกสัมผัส"
    },
    {
        "shot_number": 6,
        "title": "Lifestyle & Action / การใช้งานจริง",
        "role": "Lifestyle Application",
        "default_ratio": 0.11,
        "camera_motion": "pan_down",
        "sample_visual": "Aesthetic lifestyle framing of {product_name} in everyday modern setting, sleek and natural",
        "sample_script": "เพิ่มความสะดวกสบายให้ทุกวันของคุณ",
        "sample_headline": "ลงตัวกับทุกวันของคุณ"
    },
    {
        "shot_number": 7,
        "title": "Social Proof & Results / ผลลัพธ์ที่ได้",
        "role": "Benefits & Trust",
        "default_ratio": 0.11,
        "camera_motion": "zoom_in",
        "sample_visual": "Bright radiant scene with {product_name}, 5-star customer satisfaction vibe",
        "sample_script": "การันตีความพึงพอใจ ยอดนิยมอันดับ 1",
        "sample_headline": "ผู้ใช้จริงประทับใจ 99%"
    },
    {
        "shot_number": 8,
        "title": "Special Offer / ข้อเสนอสุดพิเศษ",
        "role": "Value Proposition & Promo",
        "default_ratio": 0.11,
        "camera_motion": "slow_push",
        "sample_visual": "Exciting commercial spotlight on {product_name}, special seasonal gift set framing",
        "sample_script": "โปรโมชั่นพิเศษเฉพาะวันนี้ คุ้มค่าที่สุด",
        "sample_headline": "โปรสุดคุ้มจำกัดเวลา"
    },
    {
        "shot_number": 9,
        "title": "Call to Action / สั่งซื้อตอนนี้",
        "role": "Outro & CTA",
        "default_ratio": 0.12,
        "camera_motion": "zoom_out",
        "sample_visual": "Final iconic product shot with clean outro background, official branding aesthetic",
        "sample_script": "คลิกลิงก์สั่งซื้อด่วน สินค้ามีจำนวนจำกัด!",
        "sample_headline": "สั่งซื้อเลยที่นี่"
    }
]


def calculate_shot_durations(total_duration: int) -> list:
    """Distribute total duration across 9 shots smoothly."""
    # Base split
    if total_duration == 10:
        # 10s: ~1.1s per shot
        durations = [1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.2]
    elif total_duration == 15:
        # 15s: ~1.67s per shot
        durations = [1.6, 1.6, 1.7, 1.7, 1.7, 1.7, 1.6, 1.7, 1.7]
    elif total_duration == 30:
        # 30s: ~3.33s per shot
        durations = [3.3, 3.3, 3.3, 3.4, 3.4, 3.3, 3.3, 3.3, 3.4]
    else:
        per_shot = round(total_duration / 9.0, 2)
        durations = [per_shot] * 8
        durations.append(round(total_duration - sum(durations), 2))
    return durations


def generate_fallback_storyboard(
    product_name: str,
    highlights: str,
    style: str,
    mood_tone: str,
    total_duration: int
) -> Dict[str, Any]:
    """Generate a high-quality fallback storyboard if API key is not configured."""
    durations = calculate_shot_durations(total_duration)
    
    style_descriptors = {
        "Minimal Clean": "minimalist aesthetic, soft natural daylight, clean matte shadows, modern scandinavian simplicity, neutral beige and white tones",
        "Studio Luxury": "high-end luxury commercial, obsidian black and gold reflections, dramatic dramatic rim lighting, premium gloss, 8k studio product photography",
        "Bright Summer": "sun-drenched golden hour, vibrant tropical pastel colors, energetic warmth, fresh and sparkling ambiance",
        "Futuristic": "cyberpunk high-tech neon glow, dark reflective glass, sleek laser lines, electric cyan and violet lighting, ultra-modern"
    }
    
    style_desc = style_descriptors.get(style, f"{style} style with {mood_tone}")
    clean_hl = highlights if highlights.strip() else "ฟังก์ชันครบครัน ดีไซน์ทันสมัย"
    
    shots = []
    for i, tpl in enumerate(SHOT_TEMPLATES):
        shot_dur = durations[i]
        
        # Adjust script length for total duration
        if total_duration == 10:
            words_map = [
                f"พบกับ {product_name}",
                "ดีไซน์สวย พรีเมียม",
                f"{clean_hl[:20]}",
                "ตอบโจทย์ทุกวัน",
                "ใส่ใจทุกดีเทล",
                "ใช้ง่าย พกพาสะดวก",
                "ยอดนิยมอันดับหนึ่ง",
                "โปรคุ้มพิเศษวันนี้",
                "สั่งซื้อด่วนเลย!"
            ]
            script = words_map[i]
        elif total_duration == 15:
            words_map = [
                f"มองหาไอเทมเด็ด ต้อง {product_name}",
                "สัมผัสดีไซน์สุดหรู โดดเด่นไม่ซ้ำใคร",
                f"มาพร้อมคุณสมบัติพิเศษ {clean_hl[:25]}",
                "หมดกังวลเรื่องปัญหาเดิมๆ ใช้งานได้จริง",
                "คัดสรรวัสดุระดับพรีเมียม เพื่อคุณ",
                "เติมเต็มชีวิตประจำวันให้ง่ายและสะดวกกว่าเดิม",
                "ลูกค้ามากกว่า 90% การันตีความประทับใจ",
                "รับข้อเสนอพิเศษเฉพาะช่วงเปิดตัวเท่านั้น",
                "คลิกสั่งซื้อตอนนี้ ก่อนสินค้าจะหมด!"
            ]
            script = words_map[i]
        else: # 30s
            script = tpl["sample_script"].replace("{product_name}", product_name).replace("{highlight}", clean_hl)
            script += f" สำหรับคนรุ่นใหม่ที่มองหา {clean_hl[:20]}"
            
        ai_prompt = (
            f"Cinematic vertical 9:16 advertising video shot. Shot {i+1}: {tpl['role']}. "
            f"Featuring {product_name}, {tpl['sample_visual'].format(product_name=product_name)}. "
            f"Visual style: {style_desc}. Camera motion: {tpl['camera_motion']}. "
            f"Shot duration: {shot_dur}s. Photorealistic 8k, Octane render quality."
        )
        
        shots.append({
            "shot_number": i + 1,
            "title": tpl["title"],
            "role": tpl["role"],
            "duration_seconds": shot_dur,
            "camera_motion": tpl["camera_motion"],
            "ai_video_prompt": ai_prompt,
            "thai_voiceover": script,
            "headline": tpl["sample_headline"]
        })
        
    return {
        "product_name": product_name,
        "style": style,
        "mood_tone": mood_tone,
        "total_duration": total_duration,
        "concept_summary": f"คลิปโฆษณา 9 ช็อตแนวตั้ง 9:16 สำหรับ '{product_name}' ในสไตล์ {style} โทน {mood_tone} ความยาวรวม {total_duration} วินาที",
        "shots": shots
    }


def generate_storyboard_with_gemini(
    image_bytes: Optional[bytes],
    image_mime: str,
    product_name: str,
    highlights: str,
    style: str,
    mood_tone: str,
    total_duration: int,
    api_key: str
) -> Dict[str, Any]:
    """Call Google Gemini API to analyze product image and generate a 9-shot commercial storyboard."""
    if not HAS_GENAI:
        return generate_fallback_storyboard(product_name, highlights, style, mood_tone, total_duration)
        
    client = genai.Client(api_key=api_key)
    durations = calculate_shot_durations(total_duration)
    
    # Word count guidelines based on duration
    if total_duration == 10:
        word_guideline = "แต่ละช็อตมีความยาวสั้นมาก (~1.1 วินาที) ดังนั้นบทพากย์ไทยต้องกระชับ สั้น มีเพียง 3-6 คำต่อช็อต พูดง่าย กระชับ ตรงประเด็น"
    elif total_duration == 15:
        word_guideline = "แต่ละช็อตมีความยาว ~1.6-1.7 วินาที ดังนั้นบทพากย์ไทยควรมีประมาณ 6-10 คำต่อช็อต สละสลวย กระชับน่าฟัง"
    else:
        word_guideline = "แต่ละช็อตมีความยาว ~3.3 วินาที บทพากย์ไทยควรมีประมาณ 12-18 คำต่อช็อต เล่าเรื่องได้เต็มประโยค ชัดเจนและจูงใจ"

    system_instruction = (
        "คุณคือ Creative Director และ AI Video Producer ผู้เชี่ยวชาญด้านการผลิตคลิปโฆษณาสินค้าแบบสั้น (Vertical 9:16 TikTok / Reels / Shorts Commercial). "
        "หน้าที่ของคุณคือ วิเคราะห์รูปภาพสินค้าที่ได้รับ พร้อมข้อมูลสินค้า และวางโครงสร้าง Storyboard วิดีโอโฆษณา 9 ช็อต (9-Shot Commercial Formula) "
        "ให้ตอบกลับเป็นโครงสร้าง JSON ที่ถูกต้องสมบูรณ์เท่านั้น ห้ามใส่ markdown block หรือคำอธิบายนอก JSON"
    )

    prompt = f"""
วิเคราะห์รูปภาพสินค้านี้และสร้าง Storyboard โฆษณา 9 ช็อต สำหรับแพลตฟอร์มวิดีโอแนวตั้ง (9:16):

ข้อมูลสินค้า:
- ชื่อสินค้า: {product_name or 'สินค้าพรีเมียม'}
- จุดเด่นที่ต้องการเน้น: {highlights or 'คุณภาพดี ดีไซน์ทันสมัย คุ้มค่า'}
- สไตล์วิดีโอ: {style}
- Mood & Tone เพิ่มเติม: {mood_tone or 'ทันสมัย น่าดึงดูดใจ'}
- ความยาววิดีโอรวม: {total_duration} วินาที
- เวลาต่อช็อตที่กำหนด (ต้องใช้ตัวเลขนี้เป๊ะๆ ในแต่ละช็อต): {durations}

เกณฑ์บทพากย์ไทย:
{word_guideline}

โครงสร้าง 9 ช็อตที่ต้องมีครบถ้วน:
1. Hook (ดึงดูดสายตา / เปิดด้วยปัญหาหรือความน่าตื่นเต้น)
2. Product Reveal (เปิดตัวสินค้า ดีไซน์ ความสวยงาม)
3. Key Feature #1 (เจาะลึกจุดเด่นหลัก)
4. Problem Solving (แก้ปัญหาอย่างไร ผลลัพธ์อย่างไร)
5. Key Feature #2 & Details (รายละเอียด สัมผัส เทคโนโลยี)
6. Lifestyle & Usage (การใช้งานจริงในชีวิตประจำวัน)
7. Social Proof & Benefits (ความพึงพอใจ ความมั่นใจ ผลลัพธ์)
8. Special Offer (ข้อเสนอ ความคุ้มค่า โปรโมชั่น)
9. Call to Action & Outro (ปิดการขาย สั่งซื้อตอนนี้ ชี้เป้าพิกัด)

สำหรับแต่ละช็อต จงระบุ:
- shot_number: เลขช็อต 1-9
- title: ชื่อช็อตสั้นๆ ภาษาไทย
- role: บทบาทของช็อต เช่น "Hook", "Reveal", "Feature 1", etc.
- duration_seconds: ความยาววินาที (ใช้ค่าจาก {durations})
- camera_motion: ชนิดการเคลื่อนไหวของกล้อง เลือกจาก: "zoom_in", "zoom_out", "pan_up", "pan_down", "float", "macro_zoom", "slow_push"
- ai_video_prompt: Prompt ภาษาอังกฤษอย่างละเอียดสำหรับส่งให้ AI Video Generator (เช่น Runway Gen-3, Kling, Luma) ต้องระบุ "Vertical 9:16 cinematic product commercial", สไตล์ {style}, แสง, สี, องค์ประกอบภาพ และการเคลื่อนไหว
- thai_voiceover: บทพากย์ภาษาไทยสำหรับช็อตนี้ (ความยาวต้องพอดีกับวินาทีที่กำหนด)
- headline: ข้อความพาดหัวสั้นๆ บนหน้าจอ (ไม่เกิน 4-6 คำ)

รูปแบบ JSON ที่ต้องส่งกลับ:
{{
  "product_name": "{product_name}",
  "style": "{style}",
  "mood_tone": "{mood_tone}",
  "total_duration": {total_duration},
  "concept_summary": "สรุปคอนเซปต์โฆษณาภาษาไทย 2-3 บรรทัด",
  "shots": [
    {{
      "shot_number": 1,
      "title": "...",
      "role": "...",
      "duration_seconds": {durations[0]},
      "camera_motion": "zoom_in",
      "ai_video_prompt": "...",
      "thai_voiceover": "...",
      "headline": "..."
    }},
    ... จนครบ 9 ช็อต
  ]
}}
"""

    contents = []
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    contents.append(prompt)

    # Prioritize available models with graceful fallback for temporary 503 load
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.1-pro-preview",
        "gemini-pro-latest"
    ]
    last_error = None
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            raw_text = (response.text or "").strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            # Parse JSON
            data = json.loads(raw_text)
            if "shots" in data and len(data["shots"]) >= 9:
                return data
        except Exception as e:
            last_error = e
            print(f"Model {model_name} failed: {e}")
            continue

    print(f"Gemini API generation failed with {last_error}, falling back to template.")
    return generate_fallback_storyboard(product_name, highlights, style, mood_tone, total_duration)
