# 🎬 AI Product Commercial Studio (Real Image-to-Video Engine)

เว็บแอปพลิเคชันด้วย **Streamlit** สำหรับสร้างคลิปวิดีโอโฆษณาสินค้าแนวตั้ง 9:16 ด้วยระบบ **Image-to-Video (I2V) เคลื่อนไหวจริง** โดยมีกระบวนการ:
1. **ออกแบบฉากเฉพาะแยกทุกช็อต (Scene Variations):** ใช้ Google Gemini ออกแบบสภาพแวดล้อมที่แตกต่างกันโดยสิ้นเชิง (แสงสตูดิโอ, แท่นโชว์, ซูมเจาะเนื้อสัมผัสมาโคร, คนถือใช้งานจริงในมือ, สภาพแวดล้อมใช้งานจริง, Hero Outro)
2. **สร้างภาพฉากใหม่โดยอ้างอิงสินค้า (Product Reference Scene Generation):** เจนภาพฉากใหม่ขึ้นมาเฉพาะในแต่ละช็อต โดยใช้สินค้าจริงเป็น Reference
3. **แปลงภาพเป็นวิดีโอเคลื่อนไหวจริง (I2V Generation):** ผ่าน Video Generation API จริง เช่น **Fal.ai (Kling / Luma / Minimax)**, **Luma Dream Machine**, **Runway Gen-3**, **ComfyUI**, หรือ **Free AI Video**
4. **FFmpeg Assembly & Thai TTS:** มิกซ์เสียงบรรยายภาษาไทย และเพลงคลอ (BGM) พร้อม Audio Ducking ประกอบเป็นไฟล์ `final_video.mp4`

---

## 🔑 การตั้งค่า API Keys (.env หรือ st.secrets)

กำหนดค่าใน Streamlit Cloud **Secrets** หรือไฟล์ `.streamlit/secrets.toml`:

```toml
# 1. Google Gemini API (วิเคราะห์ภาพสินค้าและวางโครงฉาก)
GEMINI_API_KEY = "your-gemini-api-key-here"

# 2. Image-to-Video API (เลือกใช้อย่างน้อย 1 ตัว หรือใช้โหมด Free)
FAL_KEY = ""           # รองรับ Kling 1.5, Luma, Minimax ผ่าน Fal.ai (แนะนำ)
LUMA_API_KEY = ""      # Luma Dream Machine API
RUNWAY_API_KEY = ""    # Runway Gen-3 Alpha API
COMFYUI_URL = ""       # เช่น http://127.0.0.1:8188 (สำหรับ ComfyUI ในเครื่อง)
```

*(หมายเหตุ: หากไม่มีคีย์วิดีโอภายนอก สามารถเลือกโหมด **"Free AI Video"** ในเมนูตั้งค่าด้านซ้ายเพื่อทดสอบการทำงานได้ทันทีโดยไม่มีค่าใช้จ่าย)*

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
├── app.py                      # โค้ดหลัก Streamlit Web Application
├── streamlit_app.py            # Entrypoint สำหรับ Streamlit Cloud
├── gemini_pipeline.py          # AI ออกแบบฉากและ Storyboard เฉพาะแต่ละช็อต
├── i2v_engine.py               # Image-to-Video Engine (Kling, Luma, Runway, Fal, ComfyUI)
├── video_engine.py             # TTS ภาษาไทย, กราฟิกซับไตเติล, และ FFmpeg Assembly
├── requirements.txt            # Python Libraries ที่จำเป็น
├── packages.txt                # แพ็กเกจระบบ Debian (ffmpeg, fonts-thai-tlwg)
├── assets/
│   ├── fonts/NotoSansThai.ttf  # ฟอนต์ภาษาไทยคมชัดสูง
│   └── bgm/*.mp3               # เพลงประกอบคลอสตูดิโอ 4 แนว
└── .streamlit/
    ├── config.toml             # ตั้งค่าธีม Dark Mode
    └── secrets.toml.example    # ตัวอย่างการตั้งค่า API Keys
```
