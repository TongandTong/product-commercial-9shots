# -*- coding: utf-8 -*-
"""
app.py - AI Product Storyboard Generator (9-Grid Master Sheet).
Generates a single, high-resolution 9-panel storyboard image from the uploaded product image using Google Gemini API.
"""

import os
import io
import time
import streamlit as st
from PIL import Image

import gemini_pipeline
import storyboard_renderer

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Storyboard 9-Grid Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling ---
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F6B 50%, #FFA07A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-align: center;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #A0AEC0;
        margin-bottom: 2rem;
        text-align: center;
    }
    .card-box {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        font-size: 1.05rem;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper: Safe Secret Getter ---
def get_secret(key_name: str, default: str = "") -> str:
    try:
        if hasattr(st, "secrets") and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return default


gemini_api_key = get_secret("GEMINI_API_KEY", "")


# --- Initialize Session State ---
if "storyboard_image_path" not in st.session_state:
    st.session_state.storyboard_image_path = None
if "storyboard_data" not in st.session_state:
    st.session_state.storyboard_data = None


# --- Header ---
st.markdown('<div class="main-title">🎬 AI Storyboard Generator (9 ช่อง รูปเดียว)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">สร้างภาพ Storyboard โฆษณา 9 ช่องในรูปเดียว จากสินค้าที่แนบ ด้วย Google Gemini API</div>', unsafe_allow_html=True)


# --- Main Layout ---
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.markdown("### 📸 1. แนบรูปภาพสินค้า")
    uploaded_file = st.file_uploader(
        "อัปโหลดรูปภาพสินค้า (PNG หรือ JPG):",
        type=["png", "jpg", "jpeg"],
        help="อัปโหลดรูปสินค้าที่ต้องการทำ Storyboard"
    )

    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("current_file_id") != file_id:
            st.session_state.current_file_id = file_id
            st.session_state.storyboard_image_path = None
            st.session_state.storyboard_data = None
        image_bytes = uploaded_file.getvalue()
        image_mime = uploaded_file.type
        prod_pil = Image.open(io.BytesIO(image_bytes))
        st.image(prod_pil, caption="รูปภาพสินค้าที่แนบ", use_container_width=True)
    else:
        image_bytes = None
        image_mime = None
        prod_pil = None
        st.info("👈 กรุณาแนบรูปภาพสินค้า เพื่อให้ระบบวิเคราะห์และสร้าง Storyboard 9 ช่อง")

with col_right:
    st.markdown("### ⚙️ 2. ข้อมูลสินค้าและสไตล์ (ไม่ระบุก็ได้ AI สแกนให้)")
    
    product_name = st.text_input(
        "ชื่อสินค้า (Product Name):",
        value="",
        placeholder="เช่น iPhone 18 Pro Max หรือ เซรั่มหน้าใส (เว้นว่างไว้ให้ AI สแกนจากภาพเองได้)"
    )

    highlights = st.text_area(
        "จุดเด่นที่ต้องการเน้น (Key Highlights):",
        value="",
        placeholder="เช่น ชิปแรง กล้อง 4K หรือ บำรุงผิวล้ำลึก (เว้นว่างไว้ให้ AI ดึงจุดเด่นให้อัตโนมัติ)",
        height=75
    )

    col_style, col_dur = st.columns(2)
    with col_style:
        style_options = ["Studio Luxury", "Minimal Clean", "Bright Summer", "Futuristic"]
        selected_style = st.selectbox(
            "สไตล์ภาพ (Visual Style):",
            options=style_options,
            index=0
        )
    with col_dur:
        mood_tone = st.text_input(
            "Mood & Tone:",
            value="พรีเมียม สดใส น่าตื่นเต้น"
        )

    # API Key override if not in secrets
    if not gemini_api_key:
        gemini_api_key = st.text_input(
            "Gemini API Key:",
            type="password",
            help="รับ API Key ฟรีได้ที่ https://aistudio.google.com/"
        )

    st.write("")
    btn_generate = st.button(
        "🚀 สร้าง Storyboard 9 ช่อง (รูปเดียว) จากสินค้า",
        type="primary",
        use_container_width=True
    )


# --- Action: Generate Storyboard 9-Grid Image ---
if btn_generate:
    if prod_pil is None or image_bytes is None:
        st.warning("⚠️ กรุณาแนบรูปภาพสินค้าก่อนกดสร้าง Storyboard")
    else:
        with st.spinner("🤖 กำลังให้ Google Gemini API วิเคราะห์ภาพสินค้า และออกแบบ Storyboard 9 ช่อง..."):
            # 1. Gemini analyzes image and writes 9-shot storyboard
            sb_data = gemini_pipeline.generate_storyboard_with_gemini(
                image_bytes=image_bytes,
                image_mime=image_mime,
                product_name=product_name,
                highlights=highlights,
                style=selected_style,
                mood_tone=mood_tone,
                total_duration=15,
                num_shots=9,
                api_key=gemini_api_key or ""
            )

            # 2. Render master 9-grid image sheet (รูปเดียว 9 ช่อง)
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            timestamp_str = int(time.time())
            master_image_path = os.path.join(output_dir, f"storyboard_9grid_{timestamp_str}.png")

            storyboard_renderer.render_9grid_storyboard_image(
                product_img=prod_pil,
                storyboard_data=sb_data,
                output_path=master_image_path
            )

            st.session_state.storyboard_data = sb_data
            st.session_state.storyboard_image_path = master_image_path
            st.success("🎉 สร้างภาพ Storyboard 9 ช่อง (รูปเดียว) เสร็จสมบูรณ์แล้ว!")


# --- Display Output ---
if st.session_state.storyboard_image_path and os.path.exists(st.session_state.storyboard_image_path):
    st.divider()
    st.markdown("### 🖼️ ภาพ Storyboard 9 ช่อง (รูปเดียว จากสินค้าที่แนบ)")
    
    # Master Storyboard Image Display
    st.image(
        st.session_state.storyboard_image_path,
        caption="Master Storyboard Sheet (9 ช่อง ในภาพเดียว)",
        use_container_width=True
    )

    # Download Button
    with open(st.session_state.storyboard_image_path, "rb") as f:
        img_bytes = f.read()

    clean_name = "".join([c if c.isalnum() else "_" for c in product_name])
    st.download_button(
        label="📥 ดาวน์โหลดภาพ Storyboard 9 ช่อง (PNG - High Resolution)",
        data=img_bytes,
        file_name=f"{clean_name}_storyboard_9grid.png",
        mime="image/png",
        type="primary",
        use_container_width=True
    )

    # Detailed Shots Breakdown
    sb = st.session_state.storyboard_data
    if sb and "shots" in sb:
        st.write("")
        with st.expander("📋 รายละเอียดสคริปต์และมุมกล้องของทั้ง 9 ช่อง"):
            concept = sb.get("concept_summary", "")
            if concept:
                st.info(f"💡 **แนวคิดโฆษณา:** {concept}")

            shots = sb.get("shots", [])
            for s in shots:
                st.markdown(f"""
                **ช่องที่ {s['shot_number']}: {s.get('title', '')}** ({s.get('role', '')})
                - 🎥 **มุมกล้อง:** {s.get('camera_motion', '').replace('_', ' ').title()}
                - 📌 **พาดหัว:** {s.get('headline', '')}
                - 🗣️ **บทพากย์:** {s.get('thai_voiceover', '')}
                - 📝 **Visual Prompt:** `{s.get('image_prompt', '')}`
                ---
                """)
