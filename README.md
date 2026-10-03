# 🎬 AI Product Commercial Studio (9-Shot Formula)

เว็บแอปพลิเคชันด้วย **Streamlit** สำหรับสร้างคลิปวิดีโอโฆษณาสินค้าแนวตั้ง 9:16 ด้วยสูตร **9 ช็อตมาตรฐานสากล** พร้อมวิเคราะห์รูปภาพสินค้าด้วย **Google Gemini API**, สังเคราะห์เสียงพากย์ภาษาไทย (**Edge-TTS / gTTS**), มิกซ์เสียงเพลงประกอบ (BGM) และประกอบคลิปแนวตั้งด้วย **FFmpeg** 

โปรเจกต์นี้พร้อมสำหรับการ Deploy ขึ้น **GitHub** และ **Streamlit Community Cloud** ทันที 🚀

---

## 🌟 จุดเด่นของระบบ (Features)

1. **Input สินค้าครบวงจร:**
   - อัปโหลดรูปภาพสินค้า (PNG/JPG) พร้อมพรีวิวแบบเรียลไทม์
   - ระบุชื่อสินค้า และจุดเด่น/ฟังก์ชันที่ต้องการเน้น
2. **สไตล์วิดีโอระดับสตูดิโอ (4 Presets + Custom):**
   - **Minimal Clean:** คลีน สว่าง เรียบหรูสไตล์สแกนดิเนเวียน
   - **Studio Luxury:** สตูดิโอหรูหรา โทนออบซิเดียนตัดทองคำ แสงสปอตไลต์
   - **Bright Summer:** ซันเดรนช์ คอรัลและสีเหลืองอบอุ่น มีพลัง
   - **Futuristic:** นีออนไซเบอร์ เส้นกริดไฮเทค ล้ำยุค
   - ช่องระบุ **Mood & Tone เพิ่มเติม** ตามต้องการ
3. **การเกลี่ยเวลา 9 ช็อตอัตโนมัติ (10s, 15s, 30s):**
   - **10 วินาที:** เฉลี่ย ~1.1s ต่อช็อต (บทพากย์คำสั้น กระชับ 3-5 คำ)
   - **15 วินาที:** เฉลี่ย ~1.6-1.7s ต่อช็อต (บทพากย์ 6-10 คำ เข้าใจง่าย)
   - **30 วินาที:** เฉลี่ย ~3.3-3.4s ต่อช็อต (บทพากย์เล่าเรื่องครบถ้วน 12-18 คำ)
4. **โครงสร้างโฆษณา 9 ช็อต (9-Shot Commercial Formula):**
   - **Shot 1:** Hook / เปิดตัวดึงดูดสายตา & ชี้ปัญหา
   - **Shot 2:** Product Reveal / เปิดตัวสินค้า ดีไซน์หรู
   - **Shot 3:** Key Feature #1 / จุดเด่นหลักที่ 1
   - **Shot 4:** Problem-Solving / การแก้ปัญหาตรงจุด
   - **Shot 5:** Feature #2 & Details / สัมผัส เนื้อสัมผัส ความประณีต
   - **Shot 6:** Lifestyle & Usage / การใช้งานจริงในชีวิตประจำวัน
   - **Shot 7:** Social Proof & Benefits / ความพึงพอใจและผลลัพธ์
   - **Shot 8:** Special Offer / ข้อเสนอและโปรโมชั่นสุดคุ้ม
   - **Shot 9:** Call to Action & Outro / ปิดการขาย สั่งซื้อตอนนี้
5. **Storyboard & Script Editor:**
   - แสดงการ์ด 9 ช็อต พร้อมช่องแก้ไขข้อความพาดหัว, บทพากย์ และมุมกล้องได้ก่อนเรนเดอร์
   - ปุ่มกดทดลองฟังเสียงพากย์รายช็อตทันที
   - คัดลอก Prompt ภาษาอังกฤษความละเอียดสูง สำหรับนำไปสร้างต่อใน Runway Gen-3 / Kling / Luma ได้ทันที
6. **Video Rendering & FFmpeg Assembly:**
   - เรนเดอร์คลิปแนวตั้ง 9:16 ด้วย Cinematic Camera Motion (Zoom In, Zoom Out, Pan Up/Down, Macro Zoom, Float)
   - เสียงพากย์ไทยด้วย Neural Voice (Premwadee / Niwat) 
   - ระบบปรับความยาววิดีโอตามเสียงพากย์อัตโนมัติ ไม่ตัดคำ
   - มิกซ์เพลงคลอ (BGM) พร้อม Audio Ducking (ลดเสียงเพลงลงอัตโนมัติเพื่อให้เสียงพูดชัดเจน)
   - พรีวิวผ่านเว็บและปุ่มกดดาวน์โหลดไฟล์ MP4 ทันที

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
├── app.py                      # โค้ดหลัก Streamlit Web Application
├── gemini_pipeline.py          # การเชื่อมต่อ Google Gemini วิเคราะห์ภาพและสร้าง Storyboard 9 ช็อต
├── video_engine.py             # เอนจินเรนเดอร์วิดีโอ 9:16, TTS ภาษาไทย, และ FFmpeg Assembly
├── requirements.txt            # Python Libraries ที่จำเป็นสำหรับ Streamlit Cloud
├── packages.txt                # รายชื่อแพ็กเกจระบบ Debian (ffmpeg, fonts-thai-tlwg)
├── assets/
│   ├── fonts/
│   │   └── NotoSansThai.ttf   # ฟอนต์ภาษาไทยคมชัดสูง
│   └── bgm/
│       ├── minimal_clean.mp3   # เพลงคลอสไตล์ Minimal Clean
│       ├── studio_luxury.mp3   # เพลงคลอสไตล์ Studio Luxury
│       ├── bright_summer.mp3   # เพลงคลอสไตล์ Bright Summer
│       └── futuristic.mp3      # เพลงคลอสไตล์ Futuristic
├── .streamlit/
│   ├── config.toml             # ตั้งค่าธีม Streamlit Dark Mode
│   └── secrets.toml.example    # ตัวอย่างไฟล์ระบุ API Keys
├── .gitignore                  # ซ่อนไฟล์ temp และ secrets
└── README.md                   # คู่มือการใช้งานและ Deploy
```

---

## 💻 วิธีการรันในเครื่อง (Local Setup)

### 1. โคลนโปรเจกต์หรือสร้าง Virtual Environment
```bash
python -m venv venv
# สำหรับ Windows:
.\venv\Scripts\activate
# สำหรับ Mac/Linux:
source venv/bin/activate
```

### 2. ติดตั้ง Python Libraries
```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Gemini API Key (ฟรี)
1. ไปที่ [Google AI Studio](https://aistudio.google.com/) แล้วกดปุ่ม **"Get API key"**
2. สร้างไฟล์ `.streamlit/secrets.toml` (คัดลอกจาก `.streamlit/secrets.toml.example`)
```toml
GEMINI_API_KEY = "AIzaSy..."
```
*(หมายเหตุ: หากไม่ใส่ API Key ในไฟล์ ระบบจะมีช่องให้กรอกบนหน้าเว็บ หรือจะใช้ Smart Offline Template ในการทดสอบก็ได้เช่นกัน)*

### 4. สั่งรันแอปพลิเคชัน
```bash
streamlit run app.py
```
เปิดเบราว์เซอร์ที่ `http://localhost:8501`

---

## ☁️ วิธีการ Deploy ขึ้น GitHub และ Streamlit Cloud

### ขั้นตอนที่ 1: นำโค้ดขึ้น GitHub
1. สร้าง New Repository บน [GitHub](https://github.com/new)
2. อัปโหลดไฟล์ทั้งหมดขึ้น Repository:
```bash
git init
git add .
git commit -m "Initial commit: 9-shot commercial studio"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### ขั้นตอนที่ 2: Deploy บน Streamlit Community Cloud
1. ไปที่ [share.streamlit.io](https://share.streamlit.io/) แล้วล็อกอินด้วย GitHub
2. กดปุ่ม **"Create app"**
3. เลือก Repository, Branch (`main`), และระบุ Main file path เป็น `app.py`
4. คลิก **"Advanced settings..."** -> ไปที่แท็บ **Secrets**
5. วาง API Key ของคุณลงในช่อง:
```toml
GEMINI_API_KEY = "AIzaSy..."
```
6. กดปุ่ม **"Deploy!"**
   - Streamlit Cloud จะอ่านไฟล์ `packages.txt` และติดตั้ง `ffmpeg` อัตโนมัติ
   - ติดตั้ง Python packages จาก `requirements.txt`
   - ระบบพร้อมใช้งานและแชร์ลิงก์ให้ทีมงานหรือลูกค้าได้ทันที! 🎉

---

## 🛠️ รายละเอียดเทคโนโลยีที่ใช้
- **Streamlit (v1.35+)**: Web Interface ที่ลื่นไหลและ Responsive
- **Google GenAI SDK**: เชื่อมต่อ Gemini 2.5/1.5 Flash วิเคราะห์ภาพสินค้าและเขียนบทพากย์
- **Edge-TTS & gTTS**: สังเคราะห์เสียงพูดภาษาไทย Neural อัตโนมัติ (ไม่ต้องเสียค่า API เสียงเพิ่ม)
- **FFmpeg & ImageIO**: ประมวลผลวิดีโอแนวตั้ง 9:16 ด้วยกล้องแอนิเมชัน และระบบมิกซ์เพลงคลอ
- **Pillow (PIL)**: จัดองค์ประกอบภาพ ออกแบบการ์ดสินค้า และทำไตเติลกราฟิก
