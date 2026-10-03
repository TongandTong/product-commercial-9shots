# -*- coding: utf-8 -*-
"""
gemini_pipeline.py - Advanced Scene & Storyboard Generation using Google Gemini API.
Generates unique scene variations and I2V motion prompts for 6-shot or 9-shot commercials.
"""

import json
import os
import re
from typing import Dict, Any, Optional, List
from PIL import Image
import io

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


SHOTS_6_TEMPLATES = [
    {
        "shot_number": 1,
        "title": "Hook / เปิดตัวดึงดูดสายตา",
        "role": "Dramatic Studio Hook",
        "environment": "สตูดิโอระดับไฮเอนด์ แสงสปอตไลต์และเอฟเฟกต์สะดุดตา",
        "camera_motion": "dynamic_push_in",
        "image_prompt": "Cinematic vertical 9:16 product advertising photography of {product_name}. Dramatic lighting, volumetric god rays, intense studio spotlight with luxury dark background, subtle water droplets and particle shimmer, 8k resolution, octane render.",
        "motion_prompt": "Fast dynamic camera push-in toward {product_name}, dramatic lighting shift, particles gently floating in air, commercial grade 4k smooth motion.",
        "sample_script": "เบื่อไหมกับปัญหาเดิมๆ? สัมผัสความต่างกับ {product_name}",
        "headline": "สัมผัสความต่างที่เหนือกว่า"
    },
    {
        "shot_number": 2,
        "title": "Product Reveal / เปิดตัวสินค้าบนแท่นโชว์",
        "role": "Pedestal Reveal",
        "environment": "แท่นวางสินค้าหินอ่อน/กระจกพรีเมียม สไตล์สตูดิโอ",
        "camera_motion": "slow_pan_orbit",
        "image_prompt": "Elegant vertical 9:16 commercial reveal shot of {product_name} resting on a modern circular marble pedestal, soft reflective studio floor, diffused daylight ambiance, clean luxury aesthetic, 8k photorealistic.",
        "motion_prompt": "Smooth 360 slow camera orbit around {product_name} on marble pedestal, soft light reflections gleaming across packaging surface, ultra-smooth cinematic motion.",
        "sample_script": "เปิดตัวนวัตกรรมล่าสุด ดีไซน์พรีเมียม โดดเด่น",
        "headline": "เปิดตัวนวัตกรรมล่าสุด"
    },
    {
        "shot_number": 3,
        "title": "Macro Feature / ซูมเจาะดีเทลและเนื้อสัมผัส",
        "role": "Macro Close-Up & Texture",
        "environment": "โคลสอัปแบบมาโคร เจาะลึกเนื้อสัมผัสและส่วนผสม",
        "camera_motion": "macro_glide",
        "image_prompt": "Extreme macro close-up vertical 9:16 shot of {product_name}, focusing on rich texture, glowing active ingredients, droplet ripples, crisp packaging craftsmanship, shallow depth of field, 8k.",
        "motion_prompt": "Gentle macro camera glide across {product_name} surface, glistening droplets gently sliding, soft focus pull to product logo, photorealistic fluid motion.",
        "sample_script": "เจาะลึกส่วนผสมเข้มข้น {highlight}",
        "headline": "เข้มข้น ตอบโจทย์ตรงจุด"
    },
    {
        "shot_number": 4,
        "title": "In-Hand Lifestyle / คนถือใช้งานจริง",
        "role": "Human Interaction & Usage",
        "environment": "มือคนถือสินค้าใช้งานจริง บรรยากาศอบอุ่นเป็นธรรมชาติ",
        "camera_motion": "natural_handheld",
        "image_prompt": "Aesthetic close-up vertical 9:16 photo of a stylish person's hand holding and using {product_name}, modern bright warm daylight, authentic lifestyle moment, soft bokeh background, 8k.",
        "motion_prompt": "Natural hand movement holding and gently presenting {product_name} to camera, soft finger touch on packaging, subtle breathing motion, realistic natural lighting.",
        "sample_script": "ใช้งานง่าย สัมผัสสบาย เหมาะกับทุกวันของคุณ",
        "headline": "ใช้งานง่าย เห็นผลจริง"
    },
    {
        "shot_number": 5,
        "title": "Real-World Environment / สภาพแวดล้อมใช้งานจริง",
        "role": "In-Situ Environment",
        "environment": "บรรยากาศห้องใช้งานจริง เช่น โต๊ะเครื่องแป้ง ห้องนั่งเล่น หรือธรรมชาติ",
        "camera_motion": "slow_reveal_tilt",
        "image_prompt": "Wide vertical 9:16 lifestyle scene of {product_name} placed aesthetically in a modern designer room with sunlight streaming through window, plant shadows, cozy stylish interior, 8k.",
        "motion_prompt": "Slow upward tilt camera motion revealing {product_name} sitting peacefully in a sunlit room, gentle curtain fluttering in breeze, warm cinematic atmosphere.",
        "sample_script": "เปลี่ยนชีวิตประจำวันของคุณให้ง่ายและมั่นใจยิ่งขึ้น",
        "headline": "ลงตัวกับทุกไลฟ์สไตล์"
    },
    {
        "shot_number": 6,
        "title": "Call to Action / ปิดการขาย สั่งซื้อตอนนี้",
        "role": "Outro & CTA",
        "environment": "ฉากสรุปโฆษณาทางการ พร้อมสปอตไลต์และแบนเนอร์สั่งซื้อ",
        "camera_motion": "hero_pull_back",
        "image_prompt": "Hero final commercial outro packshot vertical 9:16 of {product_name}, surrounded by radiant glowing backdrop, promotional badge aesthetic, brand commercial broadcast quality, 8k.",
        "motion_prompt": "Confident pull-back camera motion centering {product_name} with radiant light flares expanding outward, ending with steady iconic hero frame.",
        "sample_script": "โปรโมชั่นพิเศษวันนี้ คลิกสั่งซื้อด่วน สินค้ามีจำกัด!",
        "headline": "สั่งซื้อเลย คลิกที่นี่!"
    }
]


SHOTS_9_TEMPLATES = [
    {
        "shot_number": 1,
        "title": "Hook / เปิดตัวดึงดูดสายตา",
        "role": "Dramatic Hook",
        "environment": "สตูดิโอแสงสปอตไลต์จัดจ้าน ดึงดูดสายตา",
        "camera_motion": "dynamic_push_in",
        "image_prompt": "Cinematic vertical 9:16 advertising shot of {product_name}, intense studio spotlight with volumetric god rays, dark backdrop, water droplets shimmer, 8k.",
        "motion_prompt": "Fast dynamic push-in toward {product_name}, dramatic light beam sweep, airborne dust motes glistening.",
        "sample_script": "เบื่อไหมกับปัญหาเดิมๆ? พบกับ {product_name}",
        "headline": "สัมผัสความต่างที่เหนือกว่า"
    },
    {
        "shot_number": 2,
        "title": "Reveal / เปิดตัวสินค้าบนแท่น",
        "role": "Product Reveal",
        "environment": "แท่นหินอ่อนพรีเมียม แสงนุ่มนวล",
        "camera_motion": "slow_pan_orbit",
        "image_prompt": "Beauty reveal shot of {product_name} on a circular marble pedestal, soft ambient reflections, clean luxury aesthetic, 9:16 vertical 8k.",
        "motion_prompt": "Smooth 360 orbit around {product_name} on marble pedestal, soft sheen reflections.",
        "sample_script": "ดีไซน์พรีเมียม ตอบโจทย์ทุกไลฟ์สไตล์",
        "headline": "เปิดตัวนวัตกรรมล่าสุด"
    },
    {
        "shot_number": 3,
        "title": "Feature 1 / จุดเด่นหลักที่ 1",
        "role": "Key Selling Point #1",
        "environment": "โคลสอัปเน้นส่วนผสมและเทคโนโลยี",
        "camera_motion": "macro_glide",
        "image_prompt": "Macro close-up vertical 9:16 of {product_name}, highlighting key active ingredients, droplet ripples, crisp packaging details, 8k.",
        "motion_prompt": "Macro camera glide across {product_name}, sparkling droplets sliding gently.",
        "sample_script": "โดดเด่นด้วย {highlight}",
        "headline": "คุณภาพระดับท็อป"
    },
    {
        "shot_number": 4,
        "title": "Problem-Solving / สาธิตการแก้ปัญหา",
        "role": "Solution Demonstration",
        "environment": "ฉากเปรียบเทียบหรือสาธิตประสิทธิภาพ",
        "camera_motion": "zoom_out",
        "image_prompt": "Demonstration vertical 9:16 visual of {product_name} in action, showcasing effortless performance, bright energetic lighting, 8k.",
        "motion_prompt": "Smooth zoom out revealing {product_name} solving daily challenges effortlessly.",
        "sample_script": "แก้ปัญหาได้จริง เห็นผลลัพธ์ชัดเจน",
        "headline": "ตอบโจทย์ตรงจุด"
    },
    {
        "shot_number": 5,
        "title": "Feature 2 & Detail / ดีเทลและเนื้อสัมผัส",
        "role": "Key Selling Point #2",
        "environment": "ซูมเจาะเนื้อสัมผัสและความประณีต",
        "camera_motion": "macro_glide",
        "image_prompt": "Detailed texture and craftsmanship shot vertical 9:16 of {product_name}, luxury aesthetic reflections, silky fluid textures, 8k.",
        "motion_prompt": "Slow camera drift across fine texture and label of {product_name}, premium shimmer.",
        "sample_script": "ใส่ใจในทุกรายละเอียด ซึมไว สบายผิว",
        "headline": "ประณีตทุกสัมผัส"
    },
    {
        "shot_number": 6,
        "title": "In-Hand Usage / คนถือใช้งานจริง",
        "role": "Human Interaction",
        "environment": "คนถือสินค้าใช้งานจริง แสงธรรมชาติ",
        "camera_motion": "natural_handheld",
        "image_prompt": "Close-up vertical 9:16 photo of a stylish person holding and using {product_name}, warm natural morning light, soft bokeh, 8k.",
        "motion_prompt": "Natural hand movement presenting {product_name} to camera, smooth and authentic.",
        "sample_script": "ใช้งานง่าย พกพาสะดวก ตอบโจทย์ทุกวัน",
        "headline": "ใช้งานง่ายในมือคุณ"
    },
    {
        "shot_number": 7,
        "title": "Lifestyle Scene / สภาพแวดล้อมใช้งานจริง",
        "role": "Real-World Environment",
        "environment": "ห้องนั่งเล่นหรือโต๊ะเครื่องแป้งสไตล์โมเดิร์น",
        "camera_motion": "slow_reveal_tilt",
        "image_prompt": "Aesthetic real-world setting vertical 9:16 with {product_name} in an elegant modern sunlit room, stylish interior, 8k.",
        "motion_prompt": "Slow upward tilt showing {product_name} in a sunlit room, gentle breeze moving curtains.",
        "sample_script": "เพิ่มความมั่นใจในทุกช่วงเวลาของวัน",
        "headline": "ลงตัวกับทุกวันของคุณ"
    },
    {
        "shot_number": 8,
        "title": "Special Offer / โปรโมชั่นสุดคุ้ม",
        "role": "Special Promo & Trust",
        "environment": "ฉากโปรโมชั่นพร้อมกล่องของขวัญและป้ายพิเศษ",
        "camera_motion": "dynamic_push_in",
        "image_prompt": "Exciting commercial spotlight vertical 9:16 on {product_name}, special seasonal gift set arrangement, vibrant celebration ambiance, 8k.",
        "motion_prompt": "Dynamic push-in with gentle sparkle lighting reflecting off {product_name}.",
        "sample_script": "รับข้อเสนอพิเศษเฉพาะช่วงเปิดตัวเท่านั้น",
        "headline": "โปรสุดคุ้มจำกัดเวลา"
    },
    {
        "shot_number": 9,
        "title": "Call to Action / สั่งซื้อตอนนี้",
        "role": "Hero Outro & CTA",
        "environment": "ฉากปิดการขายทางการ โลโก้และสินค้าเด่นชัด",
        "camera_motion": "hero_pull_back",
        "image_prompt": "Final iconic product shot vertical 9:16 with radiant glowing background, official branding aesthetic, 8k.",
        "motion_prompt": "Confident pull-back camera motion centering {product_name} with light flares.",
        "sample_script": "คลิกลิงก์สั่งซื้อด่วน สินค้ามีจำนวนจำกัด!",
        "headline": "สั่งซื้อเลยที่นี่"
    }
]


def calculate_durations(num_shots: int, total_duration: int) -> List[float]:
    """Calculate shot durations smoothly."""
    dur = round(total_duration / num_shots, 2)
    durations = [dur] * (num_shots - 1)
    durations.append(round(total_duration - sum(durations), 2))
    return durations


def generate_fallback_storyboard(
    product_name: str,
    highlights: str,
    style: str,
    mood_tone: str,
    total_duration: int,
    num_shots: int = 6
) -> Dict[str, Any]:
    """Generate high-quality fallback storyboard with distinct scene environments."""
    templates = SHOTS_6_TEMPLATES if num_shots == 6 else SHOTS_9_TEMPLATES
    durations = calculate_durations(len(templates), total_duration)
    clean_hl = highlights.strip() if highlights.strip() else "นวัตกรรมพรีเมียม ตอบโจทย์ทุกไลฟ์สไตล์"

    shots = []
    for i, tpl in enumerate(templates):
        img_p = tpl["image_prompt"].replace("{product_name}", product_name).replace("{highlight}", clean_hl)
        mot_p = tpl["motion_prompt"].replace("{product_name}", product_name)
        script = tpl["sample_script"].replace("{product_name}", product_name).replace("{highlight}", clean_hl)

        shots.append({
            "shot_number": i + 1,
            "title": tpl["title"],
            "role": tpl["role"],
            "environment": tpl["environment"],
            "duration_seconds": durations[i],
            "camera_motion": tpl["camera_motion"],
            "image_prompt": f"{img_p}, style: {style}, mood: {mood_tone}",
            "i2v_motion_prompt": f"{mot_p}, smooth vertical 9:16 camera motion, cinematic 60fps",
            "thai_voiceover": script,
            "headline": tpl["headline"]
        })

    return {
        "product_name": product_name,
        "style": style,
        "mood_tone": mood_tone,
        "total_duration": total_duration,
        "num_shots": len(templates),
        "concept_summary": f"คลิปโฆษณา {len(templates)} ช็อตเคลื่อนไหวจริง (I2V) สำหรับ '{product_name}' ในสไตล์ {style} โทน {mood_tone}",
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
    num_shots: int = 6,
    api_key: str = ""
) -> Dict[str, Any]:
    """Call Google Gemini API to analyze product and design distinct scene environments for I2V."""
    if not HAS_GENAI or not api_key:
        return generate_fallback_storyboard(product_name, highlights, style, mood_tone, total_duration, num_shots)

    client = genai.Client(api_key=api_key)
    durations = calculate_durations(num_shots, total_duration)

    system_instruction = (
        "คุณคือ Commercial Video Director และ AI Video Engineer ผู้เชี่ยวชาญด้าน Image-to-Video (I2V) โฆษณาสินค้าแนวตั้ง 9:16. "
        f"หน้าที่ของคุณคือ วิเคราะห์รูปภาพสินค้า และออกแบบ Storyboard {num_shots} ช็อต โดยห้ามใช้ฉากซ้ำกันเด็ดขาด! "
        "ทุกช็อตต้องมีมุมมองและสภาพแวดล้อมที่แตกต่างกันอย่างสิ้นเชิง เช่น ซูมกล้อง, แท่นโชว์สตูดิโอ, ซูมเจาะเนื้อสัมผัสมาโคร, "
        "คนถือใช้งานจริงในมือ, และสภาพแวดล้อมใช้งานจริงในชีวิตประจำวัน ตอบกลับเป็นโครงสร้าง JSON เท่านั้น"
    )

    prompt = f"""
วิเคราะห์รูปภาพสินค้านี้และสร้าง Storyboard โฆษณา {num_shots} ช็อต สำหรับแปลงเป็นวิดีโอเคลื่อนไหวจริง (Image-to-Video: I2V 9:16):

ข้อมูลสินค้า:
- ชื่อสินค้า: {product_name or 'สินค้าพรีเมียม'}
- จุดเด่นที่ต้องการเน้น: {highlights or 'คุณภาพดี ดีไซน์ทันสมัย คุ้มค่า'}
- สไตล์วิดีโอ: {style}
- Mood & Tone: {mood_tone or 'พรีเมียม น่าดึงดูดใจ'}
- ความยาววิดีโอรวม: {total_duration} วินาที (ช็อตละประมาณ {durations[0]} วินาที)

เงื่อนไขสำคัญมาก:
1. ทุกช็อตต้องมี 'environment' (สภาพแวดล้อม) และ 'image_prompt' สำหรับเจนภาพใหม่ที่ต่างกันอย่างสิ้นเชิง:
   - ช็อต 1: แสงสตูดิโอจัดจ้าน เปิดตัวดึงดูดสายตา (Dramatic Studio Hook)
   - ช็อต 2: แท่นวางสินค้าหินอ่อน/กระจกพรีเมียม (Pedestal Reveal)
   - ช็อต 3: โคลสอัปแบบมาโคร เจาะลึกเนื้อสัมผัส ละอองน้ำ หรือดีเทล (Macro Details)
   - ช็อต 4: คนถือใช้งานจริงในมือ แสงธรรมชาติ (Human In-Hand Interaction)
   - ช็อต 5: สภาพแวดล้อมใช้งานจริงในชีวิตประจำวัน เช่น ห้องนั่งเล่น ห้องน้ำ หรือโต๊ะทำงาน (Real-World Setting)
   - ช็อตสุดท้าย: ปิดการขาย ช็อต Hero Shot พร้อมแสงเปล่งประกาย (Hero CTA Outro)
2. เขียน 'image_prompt' ภาษาอังกฤษอย่างละเอียด สำหรับใช้กับ AI Image Generator (Flux / Midjourney) สัดส่วนแนวตั้ง 9:16 โดยอ้างอิงดีไซน์ของสินค้าชิ้นนี้
3. เขียน 'i2v_motion_prompt' ภาษาอังกฤษ สำหรับสั่งให้ Image-to-Video AI (Kling / Luma / Runway) ขยับมุมกล้องและสภาพแวดล้อมให้สมจริง (3-4 วินาที)
4. เขียน 'thai_voiceover' บทพากย์ภาษาไทยที่กระชับและจบพอดีในเวลาของช็อต

รูปแบบ JSON ที่ต้องส่งกลับ:
{{
  "product_name": "{product_name}",
  "style": "{style}",
  "mood_tone": "{mood_tone}",
  "total_duration": {total_duration},
  "num_shots": {num_shots},
  "concept_summary": "สรุปแนวคิดโฆษณา 2 บรรทัด",
  "shots": [
    {{
      "shot_number": 1,
      "title": "ชื่อช็อตภาษาไทย",
      "role": "...",
      "environment": "สภาพแวดล้อมของฉากนี้",
      "duration_seconds": {durations[0]},
      "camera_motion": "dynamic_push_in",
      "image_prompt": "Cinematic vertical 9:16 product photography of {product_name}, ...",
      "i2v_motion_prompt": "Smooth camera push-in, subtle light rays shimmering, 4k 60fps...",
      "thai_voiceover": "บทพากย์ไทย...",
      "headline": "ข้อความพาดหัวสั้นๆ"
    }}
  ]
}}
"""

    contents = []
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=image_mime))
    contents.append(prompt)

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest"
    ]

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

            data = json.loads(raw_text)
            if "shots" in data and len(data["shots"]) >= num_shots:
                return data
        except Exception as e:
            continue

    return generate_fallback_storyboard(product_name, highlights, style, mood_tone, total_duration, num_shots)
