# -*- coding: utf-8 -*-
"""
app.py - Streamlit Web Application for 9-Shot Product Commercial Video Generator.
Deployable on Streamlit Community Cloud and Local Environments.
"""

import os
import io
import time
import streamlit as st
from PIL import Image

import gemini_pipeline
import video_engine

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Commercial Studio 9-Shots",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* Global Styles */
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
    .step-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
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
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "uploaded_image_mime" not in st.session_state:
    st.session_state.uploaded_image_mime = None
if "uploaded_image_pil" not in st.session_state:
    st.session_state.uploaded_image_pil = None


# --- Sidebar Settings ---
with st.sidebar:
    st.title("🎬 ตั้งค่าระบบ")

    # API Key Configuration
    st.subheader("🔑 Google Gemini API")
    secret_key = None
    try:
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
            secret_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    if secret_key:
        api_key = secret_key
        st.success("✅ เชื่อมต่อ Gemini API จาก st.secrets สำเร็จ")
    else:
        api_key = st.text_input(
            "Gemini API Key:",
            type="password",
            help="รับ API Key ฟรีได้ที่ https://aistudio.google.com/"
        )
        if not api_key:
            st.info("💡 ใส่ API Key เพื่อการวิเคราะห์ภาพสินค้าขั้นสูง (หากไม่มี จะใช้ Smart Template อัตโนมัติ)")

    st.divider()

    # Voice Settings
    st.subheader("🎙️ เสียงพากย์ไทย (TTS)")
    voice_options = {
        "th-TH-PremwadeeNeural": "พรีมวดี (ผู้หญิง - เสียงธรรมชาติ ละมุน)",
        "th-TH-NiwatNeural": "นิวัฒน์ (ผู้ชาย - เสียงหนักแน่น น่าเชื่อถือ)"
    }
    selected_voice = st.selectbox(
        "เลือกเสียงผู้บรรยาย:",
        options=list(voice_options.keys()),
        format_func=lambda x: voice_options[x]
    )

    st.divider()

    # BGM Settings
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

    st.divider()
    st.caption("🎬 9-Shot Vertical Commercial Creator • Ready for Streamlit Cloud & GitHub")


# --- Main Header ---
st.markdown('<div class="main-title">🎬 AI Product Commercial Studio (9-Shot)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">เครื่องมือสร้างคลิปโฆษณาสินค้าแนวตั้ง 9:16 ด้วยสูตร 9 ช็อตมาตรฐานสากล พร้อมเสียงพากย์ไทยและ BGM</div>', unsafe_allow_html=True)


# --- Step 1: Product Input & Style Selection ---
with st.container():
    st.markdown("### 📦 1. ข้อมูลสินค้าและการกำหนดสไตล์")
    
    col_input_left, col_input_right = st.columns([1, 1.2], gap="large")

    with col_input_left:
        uploaded_file = st.file_uploader(
            "📸 อัปโหลดรูปภาพสินค้า (PNG หรือ JPG):",
            type=["png", "jpg", "jpeg"],
            help="ควรอัปโหลดภาพสินค้าที่คมชัด พื้นหลังสะอาด หรือภาพแพ็กเกจจิ้ง"
        )
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            st.session_state.uploaded_image_bytes = image_bytes
            st.session_state.uploaded_image_mime = uploaded_file.type
            pil_img = Image.open(io.BytesIO(image_bytes))
            st.session_state.uploaded_image_pil = pil_img
            st.image(pil_img, caption="ตัวอย่างรูปภาพสินค้าที่อัปโหลด", use_container_width=True)
        else:
            # Default placeholder image if none uploaded yet
            st.info("📌 กรุณาอัปโหลดรูปภาพสินค้า เพื่อให้ Gemini วิเคราะห์องค์ประกอบและสร้างช็อต")

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

        col_style_1, col_style_2 = st.columns(2)
        with col_style_1:
            style_options = ["Minimal Clean", "Studio Luxury", "Bright Summer", "Futuristic"]
            selected_style = st.selectbox(
                "🎨 สไตล์วิดีโอ (Video Style):",
                options=style_options,
                index=1
            )
        with col_style_2:
            duration_options = [10, 15, 30]
            selected_duration = st.selectbox(
                "⏱️ ความยาวคลิป (Duration):",
                options=duration_options,
                index=1,
                format_func=lambda x: f"{x} วินาที (9 ช็อต)"
            )

        mood_tone = st.text_input(
            "ระบุ Mood & Tone เพิ่มเติม (Custom Tone):",
            value="พรีเมียม หรูหรา น่าเชื่อถือ เข้าถึงง่าย",
            placeholder="เช่น สนุกสนาน คึกคัก, อบอุ่น เป็นกันเอง, ไฮเทค ล้ำสมัย"
        )

    st.write("")
    btn_generate_sb = st.button(
        "✨ 1. สร้าง Storyboard & สคริปต์ (Generate 9-Shot Storyboard)",
        type="primary",
        use_container_width=True
    )


# --- Action 1: Generate Storyboard ---
if btn_generate_sb:
    if st.session_state.uploaded_image_bytes is None:
        st.warning("⚠️ กรุณาอัปโหลดรูปภาพสินค้าก่อนกดสร้าง Storyboard")
    else:
        with st.spinner("🤖 กำลังให้ Gemini วิเคราะห์ภาพสินค้า และวางโครงสร้าง 9 ช็อตตามสูตรโฆษณา..."):
            storyboard = gemini_pipeline.generate_storyboard_with_gemini(
                image_bytes=st.session_state.uploaded_image_bytes,
                image_mime=st.session_state.uploaded_image_mime,
                product_name=product_name,
                highlights=highlights,
                style=selected_style,
                mood_tone=mood_tone,
                total_duration=selected_duration,
                api_key=api_key or ""
            )
            st.session_state.storyboard = storyboard
            st.session_state.final_video_path = None
            st.success("🎉 สร้าง Storyboard & สคริปต์โฆษณา 9 ช็อตสำเร็จ! คุณสามารถตรวจทานและแก้ไขได้ด้านล่าง")


# --- Step 2: Storyboard Review & Editing ---
if st.session_state.storyboard is not None:
    sb = st.session_state.storyboard
    st.divider()
    st.markdown("### 📋 2. ตรวจทานและปรับแต่ง Storyboard 9 ช็อต (Review & Edit)")
    
    concept = sb.get("concept_summary", "")
    if concept:
        st.info(f"💡 **แนวคิดโฆษณา:** {concept}")

    st.write("คุณสามารถปรับแต่งบทพากย์, ข้อความพาดหัว, และมุมกล้องของแต่ละช็อตได้ก่อนกดเรนเดอร์:")

    motion_choices = ["zoom_in", "zoom_out", "pan_up", "pan_down", "float", "macro_zoom", "slow_push"]
    motion_labels = {
        "zoom_in": "🔍 ซูมเข้า (Zoom In)",
        "zoom_out": "🔎 ซูมออก (Zoom Out)",
        "pan_up": "⬆️ แพนกล้องขึ้น (Pan Up)",
        "pan_down": "⬇️ แพนกล้องลง (Pan Down)",
        "float": "🌊 ลอยนิ่งสง่างาม (Float)",
        "macro_zoom": "🔬 ซูมเจาะดีเทล (Macro Zoom)",
        "slow_push": "🎬 ผลักกล้องช้าๆ (Slow Push)"
    }

    # Render 9 Shots in 3x3 Grid
    shots = sb.get("shots", [])
    updated_shots = []

    for row in range(3):
        cols = st.columns(3)
        for col_idx in range(3):
            shot_idx = row * 3 + col_idx
            if shot_idx < len(shots):
                shot = shots[shot_idx]
                with cols[col_idx]:
                    st.markdown(f"""
                    <div class="shot-card">
                        <span class="shot-badge">ช็อตที่ {shot['shot_number']}/9 • {shot.get('role', 'Shot')}</span>
                        <div style="font-weight: 700; font-size: 1rem; color: #FFFFFF; margin-bottom: 6px;">
                            {shot.get('title', '')} ({shot.get('duration_seconds', 1.5)}s)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Editable fields
                    new_headline = st.text_input(
                        f"ข้อความพาดหัว (ช็อต {shot['shot_number']}):",
                        value=shot.get("headline", ""),
                        key=f"headline_{shot_idx}"
                    )
                    
                    new_script = st.text_area(
                        f"บทพากย์ไทย (ช็อต {shot['shot_number']}):",
                        value=shot.get("thai_voiceover", ""),
                        key=f"script_{shot_idx}",
                        height=70
                    )

                    cur_motion = shot.get("camera_motion", "zoom_in")
                    motion_index = motion_choices.index(cur_motion) if cur_motion in motion_choices else 0
                    new_motion = st.selectbox(
                        f"มุมกล้อง (ช็อต {shot['shot_number']}):",
                        options=motion_choices,
                        index=motion_index,
                        format_func=lambda x: motion_labels.get(x, x),
                        key=f"motion_{shot_idx}"
                    )

                    with st.expander(f"Prompt สำหรับ AI Video (ช็อต {shot['shot_number']})"):
                        new_prompt = st.text_area(
                            "AI Video Prompt (English):",
                            value=shot.get("ai_video_prompt", ""),
                            key=f"prompt_{shot_idx}",
                            height=90
                        )

                    # Quick Voice Preview button
                    if st.button(f"🔊 ฟังเสียงช็อต {shot['shot_number']}", key=f"preview_voice_{shot_idx}"):
                        with st.spinner("กำลังสังเคราะห์เสียง..."):
                            preview_audio_file = f"temp/preview_shot_{shot_idx}.mp3"
                            success, _ = video_engine.generate_thai_tts(
                                text=new_script,
                                output_path=preview_audio_file,
                                voice=selected_voice
                            )
                            if os.path.exists(preview_audio_file):
                                st.audio(preview_audio_file, format="audio/mp3")

                    # Update shot data
                    shot_copy = dict(shot)
                    shot_copy["headline"] = new_headline
                    shot_copy["thai_voiceover"] = new_script
                    shot_copy["camera_motion"] = new_motion
                    shot_copy["ai_video_prompt"] = new_prompt
                    updated_shots.append(shot_copy)

    sb["shots"] = updated_shots
    st.session_state.storyboard = sb

    st.write("")
    st.divider()

    # --- Step 3: Render & Assemble Video ---
    st.markdown("### 🚀 3. เรนเดอร์และประกอบคลิปวิดีโอ (Render & Assemble)")
    
    btn_render = st.button(
        "🎬 2. เรนเดอร์และประกอบคลิป (Render & Assemble 9:16 Video)",
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

            shot_video_paths = []
            shots = sb.get("shots", [])

            total_steps = len(shots) + 2
            current_step = 0

            # 1. Process each shot
            for idx, shot in enumerate(shots):
                current_step += 1
                progress = int((current_step / total_steps) * 100)
                progress_bar.progress(progress)
                status_text.markdown(f"⏳ **กำลังเรนเดอร์ช็อตที่ {idx + 1}/9:** *{shot.get('title', '')}* (สังเคราะห์เสียง & แอนิเมชัน 9:16)...")

                shot_audio_path = os.path.join(temp_dir, f"shot_{idx + 1}_tts.mp3")
                shot_video_path = os.path.join(temp_dir, f"shot_{idx + 1}_video.mp4")

                # Generate TTS
                video_engine.generate_thai_tts(
                    text=shot.get("thai_voiceover", ""),
                    output_path=shot_audio_path,
                    voice=selected_voice
                )

                # Render Canvas Frame
                canvas = video_engine.render_shot_canvas(
                    product_img=prod_pil,
                    shot_data=shot,
                    style=selected_style,
                    product_name=product_name
                )

                # Render Shot Video with Camera Motion & TTS
                video_engine.render_single_shot_video(
                    canvas_img=canvas,
                    audio_path=shot_audio_path,
                    shot_duration=float(shot.get("duration_seconds", 1.5)),
                    output_video_path=shot_video_path,
                    motion_type=shot.get("camera_motion", "zoom_in")
                )
                shot_video_paths.append(shot_video_path)

            # 2. Concat & Mix BGM
            current_step += 1
            progress_bar.progress(95)
            status_text.markdown("🎶 **กำลังรวม 9 คลิป มิกซ์เสียงพากย์และเพลงคลอ (FFmpeg BGM Mixing)...**")

            # Determine BGM track
            if selected_bgm == "auto":
                bgm_track_name = selected_style
            elif selected_bgm == "none":
                bgm_track_name = "none"
            else:
                bgm_track_name = selected_bgm

            timestamp_str = int(time.time())
            final_output_file = os.path.join(output_dir, f"commercial_9shot_{timestamp_str}.mp4")

            video_engine.assemble_9shot_commercial(
                shot_video_paths=shot_video_paths,
                bgm_name=bgm_track_name,
                bgm_volume=bgm_volume if selected_bgm != "none" else 0.0,
                output_final_path=final_output_file
            )

            progress_bar.progress(100)
            status_text.markdown("✅ **เรนเดอร์และประกอบคลิปโฆษณาเสร็จสมบูรณ์ 100%!**")
            st.session_state.final_video_path = final_output_file


# --- Step 4: Display Finished Video & Export ---
if st.session_state.final_video_path is not None and os.path.exists(st.session_state.final_video_path):
    st.divider()
    st.markdown("### 🏆 ผลลัพธ์วิดีโอโฆษณา 9 ช็อต (Ready to Export)")

    col_vid, col_meta = st.columns([1, 1], gap="large")

    with col_vid:
        st.video(st.session_state.final_video_path)

        with open(st.session_state.final_video_path, "rb") as f:
            video_bytes = f.read()

        clean_pname = "".join([c if c.isalnum() else "_" for c in product_name])
        st.download_button(
            label="📥 ดาวน์โหลดวิดีโอโฆษณา (MP4 - 9:16 Vertical)",
            data=video_bytes,
            file_name=f"{clean_pname}_commercial_9shots.mp4",
            mime="video/mp4",
            type="primary",
            use_container_width=True
        )

    with col_meta:
        st.markdown(f"""
        #### 📊 ข้อมูลคลิปวิดีโอ:
        - **ชื่อสินค้า:** {product_name}
        - **สไตล์วิดีโอ:** {selected_style}
        - **สัดส่วน:** 9:16 (แนวตั้งสำหรับ TikTok / Reels / Shorts)
        - **จำนวนช็อต:** 9 ช็อตสมบูรณ์แบบ
        - **เสียงบรรยาย:** {voice_options.get(selected_voice)}
        - **เพลงประกอบ:** {bgm_choices.get(selected_bgm)}
        """)

        st.write("")
        with st.expander("📋 คัดลอก Prompt สำหรับ AI Video Generator ทั้ง 9 ช็อต (Runway / Kling / Luma)"):
            all_prompts = ""
            for s in sb.get("shots", []):
                all_prompts += f"--- SHOT {s['shot_number']}: {s.get('role', '')} ({s.get('duration_seconds', '')}s) ---\n"
                all_prompts += f"{s.get('ai_video_prompt', '')}\n\n"
            st.text_area("All 9 Prompts:", value=all_prompts, height=220)
