# === builder-assistant/ocr.py ===

import easyocr
from PIL import Image
import io
import tempfile
import pdfplumber

reader = easyocr.Reader(['en'], gpu=False)


def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text_from_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name)
        results = reader.readtext(tmp.name, detail=0)
    return "\n".join(results)


def extract_text(file_bytes, file_type):
    if file_type.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif file_type.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file_bytes)
    else:
        return "Unsupported file type"
