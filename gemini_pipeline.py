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


def detect_product_category(product_name: str, highlights: str = "") -> str:
    """Detect whether product is tech, food/drink, or beauty."""
    text = f"{product_name} {highlights}".lower()
    tech_keywords = [
        "phone", "iphone", "ipad", "android", "samsung", "tech", "gadget",
        "คอม", "มือถือ", "สมาร์ทโฟน", "หูฟัง", "ชิป", "กล้อง", "app", "pro",
        "laptop", "watch", "tablet", "ไอโฟน", "โทรศัพท์", "อิเล็กทรอนิกส์", "device"
    ]
    drink_keywords = [
        "กาแฟ", "coffee", "ชา", "tea", "drink", "เครื่องดื่ม", "น้ำ",
        "collagen", "วิตามิน", "อาหาร", "snack", "juice", "energy"
    ]
    if any(k in text for k in tech_keywords):
        return "tech"
    if any(k in text for k in drink_keywords):
        return "food_drink"
    return "beauty"


SHOTS_9_BEAUTY_TEMPLATES = [
    {
        "shot_number": 1,
        "title": "ACT 1: ปัญหาในชีวิตจริง (The Problem)",
        "role": "ตื่นนอน เผชิญปัญหา",
        "scene_type": "INT. BATHROOM MIRROR - MORNING",
        "environment": "ส่องกระจกตอนเช้า แสงสลัว ใบหน้าหมองคล้ำ ขาดความมั่นใจ",
        "camera_motion": "slow_push_in",
        "image_prompt": "Cinematic visual storytelling, tired person looking into bathroom mirror in dim morning light, touching face with concern, moody cinematic atmosphere, shallow depth of field, 8k.",
        "i2v_motion_prompt": "Slow emotional camera push-in toward mirror reflection, character sighing gently, soft natural morning shadows.",
        "sample_script": "ตื่นเช้ามาทีไร ส่องกระจกแล้วหมดความมั่นใจทุกที...",
        "headline": "ผิวหมองคล้ำ ขาดความสดใส",
        "action_note": "ตัวละครยืนหน้ากระจก ลูบใบหน้าด้วยความกังวลใจ"
    },
    {
        "shot_number": 2,
        "title": "ACT 2: ความกังวลใจ (Frustration)",
        "role": "ลองมาเยอะแต่ไม่ได้ผล",
        "scene_type": "INT. BEDROOM VANITY - WORRY",
        "environment": "โต๊ะเครื่องแป้งรก มีครีมและผลิตภัณฑ์หลายชิ้นวางเกลื่อนแต่ไม่ได้ผล",
        "camera_motion": "handheld_close_up",
        "image_prompt": "Dramatic scene of a frustrated character sitting at a cluttered dressing table filled with unused skincare bottles, holding head in hand with disappointment, soft moody lighting, 8k.",
        "i2v_motion_prompt": "Subtle handheld camera drift capturing clutter of bottles then focusing on character troubled expression.",
        "sample_script": "ลองมาสารพัดวิธี เสียทั้งเงินทั้งเวลา แต่ผลลัพธ์ก็ยังเหมือนเดิม...",
        "headline": "ลองมาสารพัด ก็ยังไม่ตอบโจทย์",
        "action_note": "นั่งกุมขมับหน้าโต๊ะเครื่องแป้ง ถอนหายใจกับครีมเก่าๆ"
    },
    {
        "shot_number": 3,
        "title": "ACT 3: ค้นพบทางออก (The Discovery)",
        "role": "จุดเปลี่ยนพบสินค้าตัวช่วย",
        "scene_type": "INT. HOPEFUL DISCOVERY - WARMTH",
        "environment": "แสงอบอุ่นส่องลงมาที่ตัวสินค้าอย่างมีความหวัง ตัวละครมองด้วยความตื่นเต้น",
        "camera_motion": "dramatic_reveal",
        "image_prompt": "Warm hopeful golden sunbeam breaking into room and illuminating {product_name} on clean pedestal, character hand reaching toward it with curiosity, cinematic rim lighting, 8k.",
        "i2v_motion_prompt": "Dynamic downward camera sweep revealing {product_name} bathed in radiant golden morning beam.",
        "sample_script": "จนได้มาเจอกับ {product_name} ตัวช่วยใหม่ที่เปลี่ยนทุกอย่าง!",
        "headline": "จนได้มาเจอกับ {product_name}",
        "action_note": "แสงอบอุ่นส่องต้องขวดสินค้า หยิบขึ้นมาดูด้วยความหวัง"
    },
    {
        "shot_number": 4,
        "title": "ACT 4: เจาะลึกเนื้อสัมผัส (Texture & Macro)",
        "role": "นวัตกรรมและสารสกัดเข้มข้น",
        "scene_type": "MACRO TEXTURE & DROPLET",
        "environment": "ซูมมาโครหัวดรอปเปอร์ หยดเซรั่มประกายทอง ละอองน้ำแตกตัว สารสกัดเข้มข้น",
        "camera_motion": "macro_glide",
        "image_prompt": "Extreme macro close-up of {product_name} dropper releasing a pristine glowing active droplet, micro ripples, glistening serum texture, luxury lighting, 8k.",
        "i2v_motion_prompt": "Slow-motion macro camera track following droplet falling and creating smooth ripple waves, golden sparkles.",
        "sample_script": "สัมผัสแรกคือเนื้อบางเบา ซึมลึก อุดมด้วย {highlight}",
        "headline": "เนื้อสัมผัสเข้มข้น ซึมลึกบางเบา",
        "action_note": "ดรอปเปอร์หยดเนื้อเซรั่มลงมา ละอองประกายทองแตกตัว"
    },
    {
        "shot_number": 5,
        "title": "ACT 5: สัมผัสการใช้จริง (Gentle Application)",
        "role": "ปรนนิบัติบำรุงอย่างนุ่มนวล",
        "scene_type": "CLOSE-UP FACE APPLICATION",
        "environment": "ปลายนิ้วแตะเนื้อสัมผัสเกลี่ยลงบนพวงแก้ม แสงธรรมชาตินุ่มนวล ผ่อนคลาย",
        "camera_motion": "soft_focus_pan",
        "image_prompt": "Intimate close-up of gentle fingers patting and smoothing hydrating serum onto glowing cheek, peaceful relaxed expression, soft clean skincare aesthetic, 8k.",
        "i2v_motion_prompt": "Smooth gliding camera pan across cheek as serum absorbs instantaneously, soothing skin motion.",
        "sample_script": "เกลี่ยง่าย ซึมไว ไม่เหนอะหนะ รู้สึกสบายผิวทันทีที่ทา",
        "headline": "ทาบำรุงนุ่มนวล สบายผิวทันที",
        "action_note": "ปลายนิ้วเกลี่ยเนื้อเซรั่มลงบนแก้ม รอยยิ้มผ่อนคลายสบายใจ"
    },
    {
        "shot_number": 6,
        "title": "ACT 6: ผลลัพธ์เปลี่ยนไปทันตา (Transformation)",
        "role": "ผิวฉ่ำวาว อิ่มน้ำ ออร่าพุ่ง",
        "scene_type": "INT. RADIANT MIRROR GLOW",
        "environment": "ส่องกระจกอีกครั้ง ผิวหน้าเปล่งประกายออร่า ชุ่มชื้น ฉ่ำโกลว์ รอยยิ้มกว้างสดใส",
        "camera_motion": "radiant_orbit",
        "image_prompt": "Glowing radiant portrait of happy person looking into mirror with luminous glass skin, sparkle reflections, bright genuine smile, beauty commercial glow, 8k.",
        "i2v_motion_prompt": "Soft camera orbit around radiant face, natural skin glow catching light highlights, character smiling happily.",
        "sample_script": "ผิวดูฉ่ำวาว อิ่มน้ำ ออร่าพุ่งทันที สัมผัสได้ถึงความเปลี่ยนแปลง!",
        "headline": "ผิวฉ่ำโกลว์ ออร่าพุ่งทันที",
        "action_note": "ส่องกระจกด้วยรอยยิ้มสดใส ผิวหน้าเปล่งประกายออร่า"
    },
    {
        "shot_number": 7,
        "title": "ACT 7: ก้าวสู่วันใหม่อย่างมั่นใจ (Confident Lifestyle)",
        "role": "ชีวิตประจำวันมั่นใจเต็มร้อย",
        "scene_type": "EXT. SUNLIT CITY STREET",
        "environment": "เดินก้าวออกจากตึกท่ามกลางแสงแดดสดใส เมืองโมเดิร์น ยิ้มแย้มมั่นใจท้าแดด",
        "camera_motion": "tracking_walk",
        "image_prompt": "Dynamic lifestyle shot of a confident, stylish person walking on a sunny modern city street, warm sun rays, joyful expression, cinematic depth, 8k.",
        "i2v_motion_prompt": "Low-angle smooth tracking shot moving backward as character walks forward confidently, hair swaying in breeze.",
        "sample_script": "พร้อมออกไปลุยทุกกิจกรรมอย่างมั่นใจ ไม่ว่าจะแดดแรงแค่ไหนก็เอาอยู่",
        "headline": "มั่นใจเต็มร้อย ท้าแดดท้าลม",
        "action_note": "เดินก้าวออกมาอย่างสง่างาม ท้าทายแสงแดด มั่นใจเต็มร้อย"
    },
    {
        "shot_number": 8,
        "title": "ACT 8: ทุกคนทักชม (Social Admiration)",
        "role": "เพื่อนและคนรอบข้างทักชม",
        "scene_type": "INT. CAFE SOCIAL MEETING",
        "environment": "ร้านกาแฟชิคๆ เพื่อนๆ หันมามองด้วยความทึ่งและเอ่ยปากชมในความเปลี่ยนแปลง",
        "camera_motion": "over_shoulder_reaction",
        "image_prompt": "Cozy aesthetic cafe table with friends admiring the main character radiant skin, thumbs up and smiling compliments, bright sociable atmosphere, 8k.",
        "i2v_motion_prompt": "Gentle zoom in on group table as friend leans in smiling with admiration, joyous natural reactions.",
        "sample_script": "จนเพื่อนๆ ในออฟฟิศต้องทักว่า 'ไปทำอะไรมา ทำไมหน้าใสขนาดนี้!'",
        "headline": "ทุกคนทักเป็นเสียงเดียวกัน",
        "action_note": "เพื่อนๆ ในคาเฟ่หันมาทักชมด้วยความทึ่ง ยกนิ้วโป้งให้"
    },
    {
        "shot_number": 9,
        "title": "ACT 9: คืนความมั่นใจ สั่งซื้อเลย (Call to Action)",
        "role": "ถือสินค้าคู่รอยยิ้ม ปิดการขาย",
        "scene_type": "STUDIO HERO PACKSHOT & CTA",
        "environment": "สปอตไลต์ฉลองความสำเร็จ ตัวละครถือสินค้าคู่รอยยิ้ม รีวิว 5 ดาว พร้อมปุ่มสั่งซื้อด่วน",
        "camera_motion": "hero_pull_back",
        "image_prompt": "Iconic commercial final hero shot, character smiling proudly holding {product_name}, 5-star rating graphic badge, premium promotional aesthetic, 8k broadcast quality.",
        "i2v_motion_prompt": "Confident pull-back camera motion centering {product_name} with vibrant celebratory light flares.",
        "sample_script": "คืนความมั่นใจให้ตัวคุณ สั่งซื้อ {product_name} วันนี้ พร้อมโปรโมชั่นสุดพิเศษ!",
        "headline": "สั่งซื้อเลย! เพื่อผิวสวยที่คุณคู่ควร",
        "action_note": "ถือสินค้าคู่รอยยิ้มแห่งความสำเร็จ พร้อมป้ายสั่งซื้อด่วน"
    }
]


SHOTS_9_TECH_TEMPLATES = [
    {
        "shot_number": 1,
        "title": "ACT 1: ปัญหาเครื่องเดิม (The Problem)",
        "role": "เครื่องค้าง แบตหมดไว",
        "scene_type": "INT. WORK DESK - FRUSTRATION",
        "environment": "โต๊ะทำงานแสงสลัว มือถือเครื่องเก่าค้าง แบตเตอรี่เตือนสีแดง 1% โหลดช้า",
        "camera_motion": "slow_push_in",
        "image_prompt": "Cinematic shot of a frustrated user looking at a freezing smartphone with red low battery alert and loading icon, dark moody desk lighting, shallow depth of field, 8k.",
        "i2v_motion_prompt": "Slow camera push-in toward character staring in frustration at frozen loading screen.",
        "sample_script": "เจอบ่อยไหมกับมือถือเครื่องเดิม โหลดช้า แบตหมดไว ทำงานไม่ทันใจ...",
        "headline": "เครื่องค้าง แบตหมด ช้าไม่ทันใจ",
        "action_note": "ตัวละครจ้องมองหน้าจอที่ค้าง สัญลักษณ์โหลดหมุนติ้ว ถอนหายใจ"
    },
    {
        "shot_number": 2,
        "title": "ACT 2: ความหงุดหงิดใจ (Frustration)",
        "role": "สายพะรุงพะรัง พลาดโอกาส",
        "scene_type": "INT. CLUTTERED DESK - PAIN POINT",
        "environment": "โต๊ะรกด้วยสายชาร์จพันกัน พาวเวอร์แบงค์หนักอึ้ง เครื่องร้อน เสียโอกาสสำคัญ",
        "camera_motion": "handheld_close_up",
        "image_prompt": "Dramatic close-up of a messy desk with tangled mess of charging cables and heavy power bank, stressed character holding head in exasperation, 8k.",
        "i2v_motion_prompt": "Subtle handheld drift across tangled charging wires then panning to user troubled expression.",
        "sample_script": "พกพาวเวอร์แบงค์จนหนักกระเป๋า สายพันกันวุ่นวาย พลาดโมเมนต์สำคัญ...",
        "headline": "สายระโยงระยาง เสียโอกาสสำคัญ",
        "action_note": "โต๊ะเต็มไปด้วยสายชาร์จพันกัน มือถือเก่าร้อน กุมขมับ"
    },
    {
        "shot_number": 3,
        "title": "ACT 3: ค้นพบเทคโนโลยีใหม่ (The Discovery)",
        "role": "พบกับอุปกรณ์ระดับแฟลกชิป",
        "scene_type": "INT. HERO SPOTLIGHT - DISCOVERY",
        "environment": "ลำแสงสปอตไลต์นีออนสีฟ้า-ทองส่องลงมาที่ตัวเครื่องอย่างอลังการ ตัวละครมองด้วยความทึ่ง",
        "camera_motion": "dramatic_reveal",
        "image_prompt": "Futuristic cinematic reveal shot of {product_name} resting on high-tech illuminated pedestal, glowing metallic rim, volumetric blue studio light beams, 8k.",
        "i2v_motion_prompt": "Dynamic downward camera sweep revealing {product_name} bathed in radiant neon highlights.",
        "sample_script": "จนได้มาเจอกับ {product_name} นิยามใหม่ของความเร็วแรงและพรีเมียม!",
        "headline": "จนได้มาสัมผัสกับ {product_name}",
        "action_note": "ลำแสงสปอตไลต์ส่องต้องขอบไทเทเนียมและตัวเครื่อง หยิบขึ้นมาดูด้วยความตื่นเต้น"
    },
    {
        "shot_number": 4,
        "title": "ACT 4: เจาะลึกเลนส์และชิปเซ็ต (Macro Innovation)",
        "role": "กล้องโปร & ขุมพลังชิป",
        "scene_type": "MACRO LENS & TITANIUM EDGE",
        "environment": "ซูมมาโครชุดโมดูลเลนส์กล้องระดับโปร แสงสะท้อนกระจกเลนส์คริสตัล วงแหวนสะท้อนแสงหรูหรา",
        "camera_motion": "macro_glide",
        "image_prompt": "Extreme macro close-up of {product_name} camera module with multi-lens optics, anti-reflective purple coating glints, sleek titanium frame craftsmanship, 8k.",
        "i2v_motion_prompt": "Smooth macro glide tracking across glass camera lenses and gleaming metallic edges.",
        "sample_script": "ซูมลึกชุดเลนส์ระดับโปร พร้อมชิปเซ็ตอัจฉริยะ {highlight}",
        "headline": "กล้องโปรระดับท็อป ชิปเร็วแรง",
        "action_note": "กล้องซูมเจาะโมดูลเลนส์ แสงสะท้อนกระจกเลนส์คริสตัล วงแหวนสะท้อนแสงหรูหรา"
    },
    {
        "shot_number": 5,
        "title": "ACT 5: สัมผัสความลื่นไหลในมือ (Hands-on Usage)",
        "role": "ทัชลื่นติดนิ้ว ตอบสนองไว",
        "scene_type": "CLOSE-UP HANDHELD EXPERIENCE",
        "environment": "สองมือถือเครื่องอย่างกระชับ ปลายนิ้วปัดหน้าจอสีสดใส ลื่นไหล ไร้รอยต่อ ไร้ดีเลย์",
        "camera_motion": "soft_focus_pan",
        "image_prompt": "First-person close-up angle of hands effortlessly holding and swiping on the vibrant edge-to-edge display of {product_name}, ultra-smooth high refresh rate visual trail, 8k.",
        "i2v_motion_prompt": "Fluid camera motion tracking thumb sliding across borderless vibrant display, glowing reflections.",
        "sample_script": "สัมผัสในมือบางเบา หน้าจอแสดงผลสีสดใส ลื่นไหลไม่มีดีเลย์",
        "headline": "ทัชลื่นติดนิ้ว กราฟิกจัดเต็ม",
        "action_note": "นิ้วปัดหน้าจออย่างคล่องแคล่ว ภาพกราฟิกลื่นไหลตอบสนองทันที รอยยิ้มพอใจ"
    },
    {
        "shot_number": 6,
        "title": "ACT 6: พลังความเร็วเหนือระดับ (Transformation)",
        "role": "เร็วแรงเต็มสปีด ทรงพลัง",
        "scene_type": "HIGH-TECH RADIANT AURA",
        "environment": "ตัวละครยิ้มกว้าง แสงนีออนสปีดพุ่งทะลุหน้าจอ แบตอึดใช้งานได้ข้ามวัน ประมวลผลฉับไว",
        "camera_motion": "radiant_orbit",
        "image_prompt": "Cinematic portrait of amazed user smiling in awe while using {product_name}, bright neon light rays radiating from screen across face, technology breakthrough aura, 8k.",
        "i2v_motion_prompt": "Fast orbit around smiling character with vibrant dynamic motion lines symbolizing blazing speed.",
        "sample_script": "ทุกการทำงานและการเล่นเกมรวดเร็วฉับไว แบตเตอรี่อึดใช้งานได้ข้ามวัน!",
        "headline": "เร็วแรงเต็มสปีด ประสิทธิภาพล้นเหลือ",
        "action_note": "ตัวละครยิ้มกว้างด้วยความประทับใจ แสงสะท้อนบนใบหน้าจากหน้าจอที่สดใส"
    },
    {
        "shot_number": 7,
        "title": "ACT 7: ไลฟ์สไตล์คล่องตัวทุกที่ (Dynamic Lifestyle)",
        "role": "พร้อมลุยทุกกิจกรรม ถ่าย 4K",
        "scene_type": "EXT. CITY STREET - PHOTOGRAPHY",
        "environment": "เดินก้าวออกจากตึกกลางเมือง ยกเครื่องขึ้นมาถ่ายภาพวิวและวิดีโอ 4K แสงแดดสะท้อนหรูหรา",
        "camera_motion": "tracking_walk",
        "image_prompt": "Dynamic street shot of a stylish creator walking briskly in a sunny modern metropolis, capturing cinematic 4k photos with {product_name}, warm daylight lens flares, 8k.",
        "i2v_motion_prompt": "Tracking camera moving backwards as user walks confidently while framing a stunning city shot.",
        "sample_script": "พกไปลุยได้ทุกไลฟ์สไตล์ ถ่ายภาพและวิดีโอ 4K สวยคมชัดระดับภาพยนตร์",
        "headline": "พร้อมลุยทุกไลฟ์สไตล์ ถ่าย 4K ระดับโปร",
        "action_note": "เดินยกมือถือขึ้นมาถ่ายภาพเมืองในมุมมอง Cinematic แสงอาทิตย์สะท้อนสวยงาม"
    },
    {
        "shot_number": 8,
        "title": "ACT 8: ทุกคนตื่นเต้นทักชม (Social Admiration)",
        "role": "เพื่อนๆ ทึ่งในความแรงและรูปสวย",
        "scene_type": "INT. CAFE SOCIAL SHARING",
        "environment": "เพื่อนๆ ในคาเฟ่ชะโงกหน้ามาดูหน้าจอด้วยความทึ่ง ยกนิ้วโป้งให้ เอ่ยปากชมในความสวยคมชัด",
        "camera_motion": "over_shoulder_reaction",
        "image_prompt": "Modern coffee shop table where enthusiastic friends gather around, marveling in awe at the ultra-crisp photos shown on {product_name}, thumbs up and smiling, 8k.",
        "i2v_motion_prompt": "Gentle zoom into friend smiling widely and pointing at the phone screen in admiration.",
        "sample_script": "จนเพื่อนๆ ในกลุ่มเห็นรูปแล้วต้องทักว่า 'ใช้กล้องอะไรถ่าย ทำไมสวยคมชัดขนาดนี้!'",
        "headline": "เพื่อนๆ ทึ่งในความสวยและพลัง",
        "action_note": "เพื่อนๆ ในคาเฟ่ก้มมองดูภาพบนหน้าจอด้วยความทึ่ง ยกนิ้วให้"
    },
    {
        "shot_number": 9,
        "title": "ACT 9: คุ้มค่าที่สุด สั่งซื้อเลย (Hero CTA)",
        "role": "ถือสินค้าคู่รอยยิ้ม ปิดการขาย",
        "scene_type": "STUDIO HERO PACKSHOT & CTA",
        "environment": "สปอตไลต์ฉลองความสำเร็จ ตัวเครื่องเด่นสง่าคู่รอยยิ้ม รีวิว 5 ดาว พร้อมปุ่มสั่งซื้อด่วน",
        "camera_motion": "hero_pull_back",
        "image_prompt": "Official commercial broadcast outro packshot of {product_name}, 5-star rating badge, official sleek promotional badge aesthetic, 8k octane render.",
        "i2v_motion_prompt": "Confident pull-back camera motion centering {product_name} with brilliant celebratory lighting flares.",
        "sample_script": "อัปเกรดชีวิตคุณด้วย {product_name} สั่งซื้อวันนี้รับสิทธิ์พิเศษทันที!",
        "headline": "เป็นเจ้าของ {product_name} วันนี้!",
        "action_note": "ตัวเครื่องเด่นสง่าคู่รอยยิ้มความภูมิใจ รีวิว 5 ดาว พร้อมปุ่มสั่งซื้อด่วน"
    }
]

# Alias for backwards compatibility
SHOTS_9_TEMPLATES = SHOTS_9_BEAUTY_TEMPLATES


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
    num_shots: int = 9,
    category: str = ""
) -> Dict[str, Any]:
    """Generate high-quality fallback storyboard with 9 distinct narrative story scenes matching category."""
    clean_pname = product_name.strip() if product_name and product_name.strip() else "ผลิตภัณฑ์ของคุณ"
    clean_hl = highlights.strip() if highlights and highlights.strip() else "นวัตกรรมพรีเมียม ตอบโจทย์ทุกไลฟ์สไตล์"
    
    if not category:
        category = detect_product_category(clean_pname, clean_hl)

    templates = SHOTS_9_TECH_TEMPLATES if category == "tech" else SHOTS_9_BEAUTY_TEMPLATES
    if num_shots == 6:
        templates = SHOTS_6_TEMPLATES

    durations = calculate_durations(len(templates), total_duration)

    shots = []
    for i, tpl in enumerate(templates):
        img_p = tpl["image_prompt"].replace("{product_name}", clean_pname).replace("{highlight}", clean_hl)
        mot_p = tpl.get("motion_prompt", tpl.get("i2v_motion_prompt", "")).replace("{product_name}", clean_pname)
        script = tpl.get("sample_script", "").replace("{product_name}", clean_pname).replace("{highlight}", clean_hl)
        headline = tpl.get("headline", "").replace("{product_name}", clean_pname)

        shots.append({
            "shot_number": i + 1,
            "title": tpl["title"],
            "role": tpl["role"],
            "scene_type": tpl.get("scene_type", "INT. SCENE"),
            "environment": tpl.get("environment", ""),
            "action_note": tpl.get("action_note", tpl.get("environment", "")),
            "duration_seconds": durations[i],
            "camera_motion": tpl["camera_motion"],
            "image_prompt": f"{img_p}, style: {style}, mood: {mood_tone}",
            "i2v_motion_prompt": f"{mot_p}, smooth vertical camera motion, cinematic 60fps",
            "thai_voiceover": script,
            "headline": headline
        })

    return {
        "product_name": clean_pname,
        "category": category,
        "style": style,
        "mood_tone": mood_tone,
        "total_duration": total_duration,
        "num_shots": len(templates),
        "concept_summary": f"ภาพยนตร์โฆษณาเล่าเรื่อง 9 ตอน (9-Act Storyline) สำหรับ '{clean_pname}' ถ่ายทอดการแก้ปัญหาและตอบโจทย์ชีวิต",
        "shots": shots
    }


def generate_storyboard_with_gemini(
    image_bytes: Optional[bytes],
    image_mime: str,
    product_name: str,
    highlights: str,
    style: str,
    mood_tone: str,
    total_duration: int = 15,
    num_shots: int = 9,
    api_key: str = ""
) -> Dict[str, Any]:
    """Call Google Gemini API to analyze product and craft an authentic 9-Act Commercial Storyline."""
    clean_pname = product_name.strip() if product_name and product_name.strip() else "ผลิตภัณฑ์ของคุณ"
    clean_hl = highlights.strip() if highlights and highlights.strip() else "ตอบโจทย์ตรงจุด เห็นผลจริง คุณภาพพรีเมียม"
    detected_cat = detect_product_category(clean_pname, clean_hl)

    if not HAS_GENAI or not api_key:
        return generate_fallback_storyboard(clean_pname, clean_hl, style, mood_tone, total_duration, num_shots, category=detected_cat)

    client = genai.Client(api_key=api_key)
    durations = calculate_durations(num_shots, total_duration)

    system_instruction = (
        "คุณคือ Commercial Film Director และ Storyboard Master มืออาชีพ "
        "หน้าที่ของคุณคือ วิเคราะห์รูปภาพสินค้าที่ผู้ใช้อัปโหลดมาอย่างละเอียด เข้าใจประเภทสินค้า (เช่น สมาร์ทโฟน/เทคโนโลยี, สกินแคร์, เครื่องดื่ม, แฟชั่น ฯลฯ) "
        "แล้วเขียนบทภาพยนตร์โฆษณาแบบเล่าเรื่องราว (Narrative Storytelling) 9 ตอนจบในรูปเดียว ที่ตรงกับประเภทสินค้านั้นอย่างแท้จริง "
        "ตามสูตร 9-Act Commercial Storyline: "
        "1. Problem (ตัวละครเผชิญปัญหาในชีวิตประจำวัน เช่น มือถือเก่าค้างแบตหมด หรือผิวหมองคล้ำ หรือเหนื่อยล้าง่วงนอน) "
        "2. Frustration (ความกังวลใจ ลองมาหลายวิธีแต่ไม่เห็นผล ข้าวของเก่าๆ เต็มโต๊ะ) "
        "3. Discovery (จุดเปลี่ยน ค้นพบสินค้าตัวช่วยใหม่ แสงสว่างส่องลงมา) "
        "4. Feature / Tech / Texture (เจาะลึกฟังก์ชันเด่น ชิปเซ็ต เลนส์ หรือเนื้อสัมผัสเข้มข้น) "
        "5. Hands-on Usage (ทัชใช้งานจริง สัมผัสสบาย คล่องตัว) "
        "6. Instant Transformation (ผลลัพธ์ที่เปลี่ยนไปทันตา เร็วแรง หรือสดชื่น หรือผิวฉ่ำโกลว์ รอยยิ้มสดใส) "
        "7. Confident Lifestyle (ก้าวสู่วันใหม่อย่างมั่นใจ ถ่ายภาพ หรือลุยงาน หรือเที่ยว) "
        "8. Social Admiration (เพื่อนและคนรอบข้างทักชมในความเปลี่ยนแปลง) "
        "9. Hero Packshot & CTA (ถือสินค้าคู่รอยยิ้ม รีวิว 5 ดาว สั่งซื้อโปรโมชั่นด่วน) "
        "ห้ามนำรูปสินค้ามาวางตั้งโชว์ซ้ำๆ 9 ช่องเด็ดขาด! ทุกช่องต้องเป็นฉากเรื่องราวชีวิตและอารมณ์ของตัวละครที่สมจริง "
        "ตอบกลับเป็น JSON เท่านั้น โดยระบุ field 'category' ('tech', 'beauty', 'food_drink', หรือ 'lifestyle') ด้วย"
    )

    prompt = f"""
วิเคราะห์รูปภาพสินค้านี้ และสร้าง Storyboard โฆษณาแบบเล่าเรื่องราว 9 ช่อง (9-Act Commercial Narrative Storyboard) ให้ตรงกับประเภทของสินค้านี้:

ข้อมูลสินค้า:
- ชื่อสินค้า: {clean_pname}
- จุดเด่น: {clean_hl}
- หมวดหมู่เบื้องต้น: {detected_cat}
- สไตล์ภาพ: {style}
- Mood & Tone: {mood_tone or 'พรีเมียม สดใส มั่นใจ'}

กรุณาเขียนบทเรื่องราวทั้ง 9 ช่อง:
1. ACT 1 • THE PROBLEM (ปัญหา): ตัวละครเผชิญปัญหาที่เกี่ยวข้องกับสินค้านี้
2. ACT 2 • FRUSTRATION (กังวลใจ): ลองมาสารพัดอย่างแต่ไม่เห็นผล มีของเก่าๆ วางเต็มแต่แก้ไม่ได้
3. ACT 3 • DISCOVERY (พบตัวช่วย): ลำแสงแห่งความหวังส่องลงมาที่ {clean_pname} ตัวละครหยิบขึ้นมาดูด้วยความตื่นเต้น
4. ACT 4 • FEATURE & TECH (เจาะลึกจุดเด่น): ซูมเจาะลึกฟังก์ชันเด่น ชิปเซ็ต เลนส์ หรือเนื้อสัมผัส
5. ACT 5 • APPLICATION / USAGE (ใช้จริง): ตัวละครนำมาใช้งานจริงอย่างคล่องแคล่วและมีความสุข
6. ACT 6 • INSTANT RESULT (ผลลัพธ์): ผลลัพธ์เปลี่ยนไปทันตา เร็วแรง/สดชื่น/ผิวดีขึ้น รอยยิ้มสดใส
7. ACT 7 • CONFIDENT LIFESTYLE (ชีวิตใหม่): ก้าวออกไปใช้ชีวิตอย่างมั่นใจในที่สาธารณะ
8. ACT 8 • SOCIAL ADMIRATION (คนทักชม): เพื่อนๆ หันมาทักชมด้วยความทึ่ง
9. ACT 9 • HERO PACKSHOT & CTA (ชวนสั่งซื้อ): ถือสินค้าคู่รอยยิ้ม รีวิว 5 ดาว และข้อความชวนสั่งซื้อด่วน

ตอบกลับเป็นโครงสร้าง JSON ดังนี้:
{{
  "product_name": "{clean_pname}",
  "category": "{detected_cat}",
  "concept_summary": "สรุปแก่นของเรื่องราวโฆษณาชุดนี้ 1-2 ประโยค",
  "shots": [
    {{
      "shot_number": 1,
      "title": "ACT 1: ปัญหาในชีวิตจริง",
      "headline": "ข้อความพาดหัวสั้นๆ กระชับ",
      "scene_type": "INT. SCENE - MORNING",
      "camera_motion": "slow_push_in",
      "action_note": "การกระทำและอารมณ์ของตัวละครในฉากนี้",
      "thai_voiceover": "บทพูดหรือเสียงพากย์ภาษาไทยเล่าเรื่องช็อตนี้",
      "duration_seconds": 2.0
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
        "gemini-3.5-flash",
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
            raw_shots = data.get("shots") or data.get("storyboard") or data.get("scenes") or []
            if isinstance(raw_shots, list) and len(raw_shots) >= 9:
                normalized_shots = []
                for i, s in enumerate(raw_shots[:9]):
                    normalized_shots.append({
                        "shot_number": i + 1,
                        "title": s.get("title") or s.get("act_title") or f"ACT {i+1}",
                        "role": s.get("role", ""),
                        "headline": s.get("headline") or s.get("title") or f"ฉากที่ {i+1}",
                        "scene_type": s.get("scene_type") or s.get("environment") or "INT. SCENE",
                        "environment": s.get("environment") or s.get("scene_type") or "",
                        "camera_motion": s.get("camera_motion", "slow_push_in"),
                        "action_note": s.get("action_note") or s.get("character_action") or s.get("environment", ""),
                        "thai_voiceover": s.get("thai_voiceover") or s.get("voiceover") or s.get("script") or "",
                        "duration_seconds": s.get("duration_seconds", durations[i]),
                        "image_prompt": s.get("image_prompt", "")
                    })
                data["shots"] = normalized_shots
                
                # Normalize category
                cat = str(data.get("category") or detected_cat or "").lower()
                pname = str(data.get("product_name") or clean_pname).lower()
                combined_text = f"{cat} {pname}"
                if any(k in combined_text for k in ["tech", "phone", "iphone", "gadget", "mobile", "electronic", "computer", "laptop", "smart"]):
                    data["category"] = "tech"
                elif any(k in combined_text for k in ["drink", "food", "beverage", "tea", "coffee"]):
                    data["category"] = "food_drink"
                elif any(k in combined_text for k in ["beauty", "skin", "serum", "cream", "cosmetic"]):
                    data["category"] = "beauty"
                else:
                    data["category"] = detected_cat

                if not data.get("product_name") or data.get("product_name") == "ผลิตภัณฑ์ของคุณ":
                    if clean_pname != "ผลิตภัณฑ์ของคุณ":
                        data["product_name"] = clean_pname

                return data
        except Exception:
            continue

    return generate_fallback_storyboard(clean_pname, clean_hl, style, mood_tone, total_duration, num_shots, category=detected_cat)

