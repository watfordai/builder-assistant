# === builder-assistant/ocr.py ===

import pdfplumber
from PIL import Image, ImageEnhance, ImageFilter
import io
import pytesseract
import streamlit as st  # For debugging in Streamlit UI

def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_text_from_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))

    # Optional pre-processing to improve OCR accuracy
    image = image.convert("L")  # Grayscale
    image = image.filter(ImageFilter.MedianFilter())
    image = ImageEnhance.Contrast(image).enhance(2)
    image = image.point(lambda x: 0 if x < 140 else 255, '1')

    raw_text = pytesseract.image_to_string(image)

    # Debug output: show raw OCR text to user for verification
    st.expander("🔍 Raw OCR Output").code(raw_text)

    return raw_text

def extract_text(file_bytes, file_type):
    if file_type.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif file_type.endswith((".png", ".jpg", ".jpeg")):
        return extract_text_from_image(file_bytes)
    else:
        return "Unsupported file type"
