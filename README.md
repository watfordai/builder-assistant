# 🏗️ Builder Assistant MVP

An AI-powered tool for builders to extract structured room data and cost estimates from floorplans, architectural notes, PDFs, or images — all through a slick Streamlit interface.

---

## ✅ Features

- Upload a **PDF**, **image** (PNG, JPG), or **text notes**
- Auto-detect:
  - Room names
  - Dimensions (Length, Width, Height)
  - Floor and Wall areas
- Estimate costs for:
  - Paint
  - Tile / Carpet / Laminate
  - Radiators
  - Light switches & plug sockets
  - Underfloor heating
- Material and labour costs included
- Ask GPT-4 follow-up questions
- Real-time summary table

---

## 🧱 File Structure

```
builder-assistant/
├── app.py             # Streamlit UI
├── gpt.py             # GPT-4 prompts and response parsing
├── ocr.py             # OCR logic for PDF/image
├── estimator.py       # Cost calculations
├── prices.json        # Pricing definitions
├── requirements.txt   # Python dependencies
└── README.md          # Project guide (this file)
```

---

## ⚙️ Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/builder-assistant.git
cd builder-assistant
```

### 2. Install requirements
```bash
pip install -r requirements.txt
```

### 3. Add your OpenAI API key
Either:
```bash
export OPENAI_API_KEY=sk-xxxxxxxx
```
Or inside `app.py` (not recommended for production):
```python
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxx"
```

### 4. Run it
```bash
streamlit run app.py
```

Visit: [http://localhost:8501](http://localhost:8501)

---

## ☁️ Deploy to Streamlit Cloud

1. Sign into [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub repo
3. Choose `app.py` as the entry point
4. Set your OpenAI key under **Secrets**:
   ```
   OPENAI_API_KEY=sk-xxxxxxxx
   ```
5. Deploy! 🎉

You'll get a link like:
```
https://your-builder-app.streamlit.app/
```

---

## 💰 Customize Pricing

Edit `prices.json` to define your own material and labour pricing for each room-related element.