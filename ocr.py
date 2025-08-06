# === builder-assistant/ocr.py ===

import pdfplumber
from PIL import Image
import io
import base64
import paddleocr
import tempfile
import streamlit as st  # For debugging in Streamlit UI

ocr_engine = paddleocr.OCR(use_angle_cls=True, lang='en')


def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text_from_image(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    ocr_results = ocr_engine.ocr(tmp_path, cls=True)
    lines = []
    for block in ocr_results[0]:
        text = block[1][0]
        lines.append(text)

    # Debug output: show raw OCR text to user for verification
    raw_ocr_text = "\n".join(lines)
    st.expander("🔍 Raw OCR Output").code(raw_ocr_text)

    return raw_ocr_text


def extract_text(file_bytes, file_type):
    if file_type.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif file_type.endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_bytes)
    else:
        return "Unsupported file type"
