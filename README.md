# 🎬 AI Storyboard Generator (9 ช่อง รูปเดียว จากสินค้าที่แนบ)

เว็บแอปพลิเคชันด้วย **Streamlit** สำหรับสร้าง **ภาพ Storyboard โฆษณา 9 ช่อง (3x3 Grid) รวมในรูปเดียว** จากรูปสินค้าที่แนบอย่างเดียว โดยใช้ **Google Gemini API** 

---

## 🌟 จุดเด่นของระบบ
- **Input เรียบง่าย:** แนบรูปภาพสินค้าแค่รูปเดียว (PNG/JPG)
- **Gemini AI Multimodal:** วิเคราะห์สินค้าและวางโครงสร้างโฆษณา 9 ช็อตตามสูตรจิตวิทยาการขาย (Hook $\rightarrow$ Reveal $\rightarrow$ Feature $\rightarrow$ Problem-Solving $\rightarrow$ Texture $\rightarrow$ Lifestyle $\rightarrow$ Environment $\rightarrow$ Offer $\rightarrow$ CTA)
- **สร้างภาพ Storyboard 9 ช่อง รูปเดียว:** เรนเดอร์เป็นภาพมาสเตอร์ชีตความละเอียดสูง (2000x2360 px) รวม 9 ช่องพร้อมมุมกล้อง ข้อความพาดหัว และบทพากย์
- **ดาวน์โหลดง่าย:** คลิกปุ่มเดียวได้ไฟล์ภาพ PNG ความคมชัดสูงทันที

---

## 🔑 การตั้งค่า Gemini API Key
ใส่ค่าใน Streamlit Cloud **Secrets** หรือไฟล์ `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-gemini-api-key-here"
```
*(รับ API Key ฟรีได้จาก https://aistudio.google.com/)*
