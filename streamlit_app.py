# -*- coding: utf-8 -*-
"""
app.py - Advanced AI Product Commercial Studio (Image-to-Video Engine).
Generates unique scene variations and real moving video clips via Kling, Luma, Runway, Fal.ai, ComfyUI, or Free AI Video.
"""

import os
import io
import time
import streamlit as st
from PIL import Image

import gemini_pipeline
import video_engine
import i2v_engine

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Commercial Studio (I2V Motion)",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F6B 50%, #FFA07A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #A0AEC0;
        margin-bottom: 1.8rem;
    }
    .shot-card {
        background: rgba(25, 30, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .shot-badge {
        display: inline-block;
        background: #FF4B4B;
        color: white;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .env-tag {
        display: inline-block;
        background: rgba(0, 240, 255, 0.15);
        color: #00F0FF;
        border: 1px solid rgba(0, 240, 255, 0.4);
        padding: 2px 8px;
        border-radius: 8px;
        font-size: 0.78rem;
        margin-bottom: 8px;
    }
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# --- Initialize Session State ---
if "storyboard" not in st.session_state:
    st.session_state.storyboard = None
if "final_video_path" not in st.session_state:
    st.session_state.final_video_path = None
if "scene_images" not in st.session_state:
    st.session_state.scene_images = []
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_mime" not in st.session_state:
    st.session_state.uploaded_image_mime = None
if "uploaded_image_pil" not in st.session_state:
    st.session_state.uploaded_image_pil = None


# --- Helper: Safe Secret Getter ---
def get_secret(key_name: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return default


# --- Sidebar Settings ---
with st.sidebar:
    st.title("🎬 ตั้งค่าระบบ AI & API")

    # 1. Gemini API
    st.subheader("🔑 Google Gemini API")
    default_gemini = get_secret("GEMINI_API_KEY", "")
    if default_gemini:
        gemini_api_key = default_gemini
        st.success("✅ โหลด GEMINI_API_KEY จาก secrets สำเร็จ")
    else:
        gemini_api_key = st.text_input(
            "Gemini API Key:",
            value="",
            type="password",
            help="รับฟรีได้ที่ https://aistudio.google.com/"
        )

    st.divider()

    # 2. Image-to-Video (I2V) Provider Selection
    st.subheader("🎥 บริการ Image-to-Video (I2V)")
    i2v_options = {
        "free": "🆓 Free AI Video (Pollinations / Fluid Motion) [ฟรี ไม่ต้องใช้คีย์]",
        "fal": "🌟 Fal.ai (Kling 1.5 / Luma / Minimax) [แนะนำความเร็วสูง]",
        "luma": "🎬 Luma Dream Machine API",
        "runway": "✨ Runway Gen-3 Alpha API",
        "comfyui": "🖥️ ComfyUI (Local / Remote API)"
    }
    selected_i2v = st.selectbox(
        "เลือก Video Generation API:",
        options=list(i2v_options.keys()),
        format_func=lambda x: i2v_options[x]
    )

    api_keys = {
        "FAL_KEY": get_secret("FAL_KEY", ""),
        "LUMA_API_KEY": get_secret("LUMA_API_KEY", ""),
        "RUNWAY_API_KEY": get_secret("RUNWAY_API_KEY", ""),
        "COMFYUI_URL": get_secret("COMFYUI_URL", "http://127.0.0.1:8188")
    }

    if selected_i2v == "fal":
        api_keys["FAL_KEY"] = st.text_input(
            "Fal.ai API Key (FAL_KEY):",
            value=api_keys["FAL_KEY"],
            type="password",
            help="รับ Key ได้ที่ https://fal.ai/"
        )
    elif selected_i2v == "luma":
        api_keys["LUMA_API_KEY"] = st.text_input(
            "Luma API Key (LUMA_API_KEY):",
            value=api_keys["LUMA_API_KEY"],
            type="password",
            help="รับ Key ได้ที่ https://lumalabs.ai/dream-machine/api"
        )
    elif selected_i2v == "runway":
        api_keys["RUNWAY_API_KEY"] = st.text_input(
            "Runway API Key (RUNWAY_API_KEY):",
            value=api_keys["RUNWAY_API_KEY"],
            type="password",
            help="รับ Key ได้ที่ https://runwayml.com/"
        )
    elif selected_i2v == "comfyui":
        api_keys["COMFYUI_URL"] = st.text_input(
            "ComfyUI Endpoint URL:",
            value=api_keys["COMFYUI_URL"],
            help="เช่น http://127.0.0.1:8188 หรือ URL เซิร์ฟเวอร์ ComfyUI"
        )

    st.divider()

    # 3. Voice Settings
    st.subheader("🎙️ เสียงพากย์ไทย (TTS)")
    voice_options = {
        "th-TH-PremwadeeNeural": "พรีมวดี (ผู้หญิง - เสียงละมุนเป็นธรรมชาติ)",
        "th-TH-NiwatNeural": "นิวัฒน์ (ผู้ชาย - เสียงหนักแน่นน่าเชื่อถือ)"
    }
    selected_voice = st.selectbox(
        "เลือกเสียงผู้บรรยาย:",
        options=list(voice_options.keys()),
        format_func=lambda x: voice_options[x]
    )

    # 4. BGM Settings
    st.subheader("🎵 เพลงประกอบ (BGM)")
    bgm_choices = {
        "auto": "อัตโนมัติตามสไตล์วิดีโอ (Auto)",
        "minimal_clean": "Minimal Clean (โปร่ง สบาย ผ่อนคลาย)",
        "studio_luxury": "Studio Luxury (หรูหรา นุ่มลึก พรีเมียม)",
        "bright_summer": "Bright Summer (สดใส ร่าเริง มีพลัง)",
        "futuristic": "Futuristic (โมเดิร์น ไซเบอร์ ซินธ์)",
        "none": "ปิดเสียงเพลง (No BGM)"
    }
    selected_bgm = st.selectbox(
        "เลือกแนวเพลงคลอ:",
        options=list(bgm_choices.keys()),
        format_func=lambda x: bgm_choices[x]
    )
    bgm_volume = st.slider("ระดับเสียงเพลงคลอ (BGM Volume):", min_value=0.05, max_value=0.40, value=0.18, step=0.01)

    show_subtitles = st.checkbox("แสดงซับไตเติลภาษาไทยบนคลิป (Show Thai Subtitles)", value=True)

    st.divider()
    st.caption("🎬 Real Motion Image-to-Video Studio • 9:16 Commercial Generator")


# --- Main Header ---
st.markdown('<div class="main-title">🎬 AI Product Commercial Studio (Real I2V Motion)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">เจนภาพใหม่แยกทุกฉากตามสภาพแวดล้อม + แปลงเป็นวิดีโอเคลื่อนไหวจริง (I2V) + พากย์ไทย & มิกซ์เสียงสมบูรณ์แบบ</div>', unsafe_allow_html=True)


# --- Step 1: Input Product Details ---
with st.container():
    st.markdown("### 📦 1. ข้อมูลสินค้าและการกำหนดฉาก")
    
    col_input_left, col_input_right = st.columns([1, 1.2], gap="large")

    with col_input_left:
        uploaded_file = st.file_uploader(
            "📸 อัปโหลดรูปภาพสินค้าอ้างอิง (PNG หรือ JPG):",
            type=["png", "jpg", "jpeg"],
            help="รูปสินค้านี้จะถูกนำไปใช้วิเคราะห์และใช้เป็นภาพ Reference ในการเจนฉากใหม่ทุกฉาก"
        )
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            st.session_state.uploaded_image_bytes = image_bytes
            st.session_state.uploaded_image_mime = uploaded_file.type
            pil_img = Image.open(io.BytesIO(image_bytes))
            st.session_state.uploaded_image_pil = pil_img
            st.image(pil_img, caption="รูปภาพสินค้าต้นฉบับ (Reference)", use_container_width=True)
        else:
            st.info("📌 กรุณาอัปโหลดรูปภาพสินค้าเพื่อเริ่มวางโครงสร้างฉากใหม่")

    with col_input_right:
        product_name = st.text_input(
            "ชื่อสินค้า (Product Name):",
            value="Gluta Glow White Serum",
            placeholder="เช่น เซรั่มหน้าใส Gluta Glow, หูฟังไร้สาย Aura Sound"
        )

        highlights = st.text_area(
            "จุดเด่นที่ต้องการเน้น (Key Features / Highlights):",
            value="ผิวกระจ่างใสใน 7 วัน, ซึมไว ไม่เหนียวเหนอะหนะ, สารสกัดนำเข้าจากญี่ปุ่น",
            placeholder="ระบุจุดเด่น ส่วนผสม หรือฟังก์ชันหลักที่ต้องการให้เน้นในคลิป",
            height=70
        )

        col_shots, col_style, col_dur = st.columns(3)
        with col_shots:
            num_shots_choice = st.selectbox(
                "🎬 จำนวนช็อต:",
                options=[6, 9],
                index=0,
                format_func=lambda x: f"{x} ช็อต ({'แนะนำสำหรับ I2V' if x == 6 else 'สูตรเต็ม'})"
            )
        with col_style:
            style_options = ["Studio Luxury", "Minimal Clean", "Bright Summer", "Futuristic"]
            selected_style = st.selectbox(
                "🎨 สไตล์วิดีโอ:",
                options=style_options,
                index=0
            )
        with col_dur:
            duration_options = [15, 30] if num_shots_choice == 6 else [15, 30]
            selected_duration = st.selectbox(
                "⏱️ ความยาวคลิปรวม:",
                options=duration_options,
                index=0,
                format_func=lambda x: f"{x} วินาที (~{round(x/num_shots_choice, 1)}s/ช็อต)"
            )

        mood_tone = st.text_input(
            "ระบุ Mood & Tone เพิ่มเติม:",
            value="พรีเมียม หรูหรา น่าเชื่อถือ เข้าถึงง่าย",
            placeholder="เช่น สนุกสนาน คึกคัก, อบอุ่น เป็นกันเอง, ไฮเทค ล้ำสมัย"
        )

    st.write("")
    btn_generate_sb = st.button(
        "✨ 1. สร้าง Storyboard & ออกแบบฉากใหม่ทุกช็อต (Generate Storyboard)",
        type="primary",
        use_container_width=True
    )


# --- Action 1: Generate Storyboard ---
if btn_generate_sb:
    if st.session_state.uploaded_image_bytes is None:
        st.warning("⚠️ กรุณาอัปโหลดรูปภาพสินค้าก่อนกดสร้าง Storyboard")
    else:
        with st.spinner("🤖 กำลังให้ Gemini วิเคราะห์ภาพ และออกแบบสภาพแวดล้อมฉากใหม่แยกทุกช็อต..."):
            storyboard = gemini_pipeline.generate_storyboard_with_gemini(
                image_bytes=st.session_state.uploaded_image_bytes,
                image_mime=st.session_state.uploaded_image_mime,
                product_name=product_name,
                highlights=highlights,
                style=selected_style,
                mood_tone=mood_tone,
                total_duration=selected_duration,
                num_shots=num_shots_choice,
                api_key=gemini_api_key or ""
            )
            st.session_state.storyboard = storyboard
            st.session_state.final_video_path = None
            st.session_state.scene_images = []
            st.success(f"🎉 สร้าง Storyboard {num_shots_choice} ช็อตสำเร็จ! แต่ละช็อตมีสภาพแวดล้อมและมุมมองที่แตกต่างกันอย่างสิ้นเชิง ตรวจทานได้ด้านล่าง")


# --- Step 2: Storyboard Review & Editing ---
if st.session_state.storyboard is not None:
    sb = st.session_state.storyboard
    st.divider()
    st.markdown("### 📋 2. ตรวจทานสภาพแวดล้อมฉากและบทพากย์ (Review & Edit Scenes)")
    
    concept = sb.get("concept_summary", "")
    if concept:
        st.info(f"💡 **แนวคิดโฆษณา:** {concept}")

    shots = sb.get("shots", [])
    updated_shots = []

    num_cols = 3
    rows = (len(shots) + num_cols - 1) // num_cols

    for r in range(rows):
        cols = st.columns(num_cols)
        for c in range(num_cols):
            shot_idx = r * num_cols + c
            if shot_idx < len(shots):
                shot = shots[shot_idx]
                with cols[c]:
                    st.markdown(f"""
                    <div class="shot-card">
                        <span class="shot-badge">ช็อตที่ {shot['shot_number']} • {shot.get('role', 'Shot')}</span>
                        <div class="env-tag">🌍 {shot.get('environment', 'ฉากเฉพาะ')}</div>
                        <div style="font-weight: 700; font-size: 1rem; color: #FFFFFF; margin-bottom: 6px;">
                            {shot.get('title', '')} ({shot.get('duration_seconds', 3.0)}s)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    new_headline = st.text_input(
                        f"พาดหัว (ช็อต {shot['shot_number']}):",
                        value=shot.get("headline", ""),
                        key=f"headline_{shot_idx}"
                    )
                    
                    new_script = st.text_area(
                        f"บทพากย์ไทย (ช็อต {shot['shot_number']}):",
                        value=shot.get("thai_voiceover", ""),
                        key=f"script_{shot_idx}",
                        height=70
                    )

                    with st.expander(f"Prompt เจนภาพฉากใหม่ (ช็อต {shot['shot_number']})"):
                        new_img_prompt = st.text_area(
                            "Scene Image Prompt (Flux/Midjourney):",
                            value=shot.get("image_prompt", ""),
                            key=f"img_prompt_{shot_idx}",
                            height=80
                        )

                    with st.expander(f"Prompt คำสั่ง I2V ขยับวิดีโอ (ช็อต {shot['shot_number']})"):
                        new_motion_prompt = st.text_area(
                            "I2V Motion Prompt (Kling/Luma/Runway):",
                            value=shot.get("i2v_motion_prompt", ""),
                            key=f"motion_prompt_{shot_idx}",
                            height=80
                        )

                    # Quick Voice Preview button
                    if st.button(f"🔊 ฟังเสียงช็อต {shot['shot_number']}", key=f"preview_voice_{shot_idx}"):
                        with st.spinner("กำลังสังเคราะห์เสียง..."):
                            preview_audio_file = f"temp/preview_shot_{shot_idx}.mp3"
                            video_engine.generate_thai_tts(
                                text=new_script,
                                output_path=preview_audio_file,
                                voice=selected_voice
                            )
                            if os.path.exists(preview_audio_file):
                                st.audio(preview_audio_file, format="audio/mp3")

                    shot_copy = dict(shot)
                    shot_copy["headline"] = new_headline
                    shot_copy["thai_voiceover"] = new_script
                    shot_copy["image_prompt"] = new_img_prompt
                    shot_copy["i2v_motion_prompt"] = new_motion_prompt
                    updated_shots.append(shot_copy)

    sb["shots"] = updated_shots
    st.session_state.storyboard = sb

    st.write("")
    st.divider()

    # --- Step 3: Render Real I2V Video & Assemble ---
    st.markdown("### 🚀 3. เจนภาพฉากใหม่ + แปลงเป็นวิดีโอเคลื่อนไหวจริง (I2V) + ประกอบคลิป")
    
    st.write(f"ระบบจะใช้ **{i2v_options[selected_i2v]}** ในการสร้างคลิปวิดีโอเคลื่อนไหวจริง (.mp4) สำหรับทุกช็อต และร้อยต่อด้วย FFmpeg")

    btn_render = st.button(
        "🎬 2. เริ่มต้นกระบวนการ Image-to-Video & ประกอบคลิป (Start I2V & Assembly)",
        type="primary",
        use_container_width=True
    )

    if btn_render:
        if st.session_state.uploaded_image_pil is None:
            st.error("ไม่พบรูปภาพสินค้า กรุณาอัปโหลดรูปภาพสินค้าก่อน")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            prod_pil = st.session_state.uploaded_image_pil
            output_dir = "output"
            temp_dir = "temp"
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(temp_dir, exist_ok=True)

            shots = sb.get("shots", [])
            total_shots = len(shots)
            raw_video_clips = []
            normalized_clips = []
            scene_images = []

            # Total steps: N shots (Image Gen) + N shots (I2V Gen) + N shots (Audio & Subtitle) + 1 Concat
            total_steps = (total_shots * 3) + 1
            current_step = 0

            # -----------------------------------------------------------------
            # Phase 1: Generate unique scene variation image for each shot
            # -----------------------------------------------------------------
            status_text.markdown("🎨 **กำลังสร้างภาพฉากใหม่แยกทุกช็อต (Scene Variations with Product Reference)...**")
            for idx, shot in enumerate(shots):
                current_step += 1
                progress_bar.progress(int((current_step / total_steps) * 100))
                status_text.markdown(f"🖼️ **สร้างภาพฉากที่ {idx+1}/{total_shots}:** *{shot.get('environment', '')}*...")

                scene_img_path = os.path.join(temp_dir, f"scene_{idx+1}.jpg")
                i2v_engine.generate_scene_variation_image(
                    shot_data=shot,
                    product_img=prod_pil,
                    output_path=scene_img_path,
                    fal_key=api_keys.get("FAL_KEY")
                )
                scene_images.append(scene_img_path)

            st.session_state.scene_images = scene_images

            # -----------------------------------------------------------------
            # Phase 2: Convert each scene image into moving .mp4 video (I2V)
            # -----------------------------------------------------------------
            status_text.markdown("🎥 **กำลังส่งภาพเข้า Video Generation API เพื่อสร้างวิดีโอเคลื่อนไหวจริง (I2V)...**")
            for idx, shot in enumerate(shots):
                current_step += 1
                progress_bar.progress(int((current_step / total_steps) * 100))
                status_text.markdown(f"⚡ **กำลังสร้างคลิปวิดีโอเคลื่อนไหวช็อตที่ {idx+1}/{total_shots}** ผ่าน {selected_i2v.upper()}...")

                scene_img_path = scene_images[idx]
                raw_vid_path = os.path.join(temp_dir, f"raw_i2v_shot_{idx+1}.mp4")

                i2v_engine.render_i2v_shot_to_video(
                    scene_image_path=scene_img_path,
                    shot_data=shot,
                    output_video_path=raw_vid_path,
                    provider=selected_i2v,
                    api_keys=api_keys,
                    duration_sec=float(shot.get("duration_seconds", 3.0))
                )
                raw_video_clips.append(raw_vid_path)

            # -----------------------------------------------------------------
            # Phase 3: Synthesize Thai TTS and normalize each video clip
            # -----------------------------------------------------------------
            status_text.markdown("🎙️ **กำลังสังเคราะห์เสียงบรรยายภาษาไทย และซิงค์จังหวะคลิป...**")
            for idx, shot in enumerate(shots):
                current_step += 1
                progress_bar.progress(int((current_step / total_steps) * 100))
                status_text.markdown(f"🎙️ **มิกซ์เสียงพากย์และซับไตเติลช็อตที่ {idx+1}/{total_shots}...**")

                shot_audio_path = os.path.join(temp_dir, f"tts_shot_{idx+1}.mp3")
                video_engine.generate_thai_tts(
                    text=shot.get("thai_voiceover", ""),
                    output_path=shot_audio_path,
                    voice=selected_voice
                )

                norm_clip_path = os.path.join(temp_dir, f"norm_shot_{idx+1}.mp4")
                video_engine.normalize_i2v_clip_with_audio(
                    raw_video_path=raw_video_clips[idx],
                    audio_path=shot_audio_path,
                    shot_data=shot,
                    output_clip_path=norm_clip_path,
                    overlay_subtitles=show_subtitles
                )
                normalized_clips.append(norm_clip_path)

            # -----------------------------------------------------------------
            # Phase 4: Final FFmpeg Assembly & BGM Mixing
            # -----------------------------------------------------------------
            current_step += 1
            progress_bar.progress(95)
            status_text.markdown("🎶 **กำลังประกอบคลิปวิดีโอจริงทั้งชุด และมิกซ์เพลงคลอ (FFmpeg Final Assembly)...**")

            if selected_bgm == "auto":
                bgm_track_name = selected_style
            elif selected_bgm == "none":
                bgm_track_name = "none"
            else:
                bgm_track_name = selected_bgm

            timestamp_str = int(time.time())
            final_output_file = os.path.join(output_dir, f"final_commercial_i2v_{timestamp_str}.mp4")

            video_engine.assemble_9shot_commercial(
                shot_video_paths=normalized_clips,
                bgm_name=bgm_track_name,
                bgm_volume=bgm_volume if selected_bgm != "none" else 0.0,
                output_final_path=final_output_file
            )

            progress_bar.progress(100)
            status_text.markdown("✅ **สร้างและประกอบคลิปโฆษณาเคลื่อนไหวจริงเสร็จสมบูรณ์ 100%!**")
            st.session_state.final_video_path = final_output_file


# --- Step 4: Display Finished Video & Export ---
if st.session_state.final_video_path is not None and os.path.exists(st.session_state.final_video_path):
    st.divider()
    st.markdown("### 🏆 ผลลัพธ์วิดีโอโฆษณาเคลื่อนไหวจริง (Real I2V Motion Commercial)")

    col_vid, col_meta = st.columns([1, 1], gap="large")

    with col_vid:
        st.video(st.session_state.final_video_path)

        with open(st.session_state.final_video_path, "rb") as f:
            video_bytes = f.read()

        clean_pname = "".join([c if c.isalnum() else "_" for c in product_name])
        st.download_button(
            label="📥 ดาวน์โหลดวิดีโอโฆษณา (MP4 - Real Motion Video)",
            data=video_bytes,
            file_name=f"{clean_pname}_real_i2v_commercial.mp4",
            mime="video/mp4",
            type="primary",
            use_container_width=True
        )

    with col_meta:
        st.markdown(f"""
        #### 📊 ข้อมูลคลิปวิดีโอจริง:
        - **ชื่อสินค้า:** {product_name}
        - **ระบบวิดีโอ:** Image-to-Video (I2V Real Motion Clips)
        - **บริการ I2V:** {i2v_options.get(selected_i2v)}
        - **จำนวนช็อตเคลื่อนไหว:** {len(sb.get('shots', []))} ช็อต (ฉากสภาพแวดล้อมไม่ซ้ำกัน)
        - **สัดส่วน:** 9:16 (แนวตั้งคมชัดสำหรับ TikTok / Reels / Shorts)
        - **เสียงบรรยาย:** {voice_options.get(selected_voice)}
        - **เพลงประกอบ:** {bgm_choices.get(selected_bgm)}
        """)

        # Display generated scene variation images
        if st.session_state.scene_images:
            with st.expander("🖼️ ดูภาพฉากเฉพาะของแต่ละช็อต (Generated Scene Variations)"):
                img_cols = st.columns(len(st.session_state.scene_images))
                for i_idx, s_path in enumerate(st.session_state.scene_images):
                    if os.path.exists(s_path):
                        with img_cols[i_idx]:
                            st.image(s_path, caption=f"ช็อต {i_idx+1}")

        st.write("")
        with st.expander("📋 คัดลอก Prompt สำหรับ AI Video Generator ทั้งหมด"):
            all_prompts = ""
            for s in sb.get("shots", []):
                all_prompts += f"=== SHOT {s['shot_number']}: {s.get('role', '')} ===\n"
                all_prompts += f"Environment: {s.get('environment', '')}\n"
                all_prompts += f"Image Prompt: {s.get('image_prompt', '')}\n"
                all_prompts += f"I2V Motion Prompt: {s.get('i2v_motion_prompt', '')}\n\n"
            st.text_area("All Shot Prompts:", value=all_prompts, height=220)
