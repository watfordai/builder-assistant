# === builder-assistant/gpt.py ===

import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prompt template for room extraction
def build_room_extraction_prompt(extracted_text):
    return f"""
You are a smart assistant for builders. From the following architectural notes or floorplan text, extract a table of rooms with their dimensions if available.

Return the output as a markdown table with this format:

Room Name | Length (m) | Width (m) | Height (m) | Floor Area (m²) | Wall Area (m²)

- If any dimension is missing, leave it blank.
- Estimate Floor Area using Length × Width.
- Estimate Wall Area using 2×(L+W)×H if Length, Width, and Height are available.
- If no rooms are found, still return an empty table header (do NOT apologize).

TEXT:
---
{extracted_text}
---
"""


def call_gpt(prompt, model="gpt-4", temperature=0.3):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for construction and architecture."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def extract_rooms_from_text(text):
    prompt = build_room_extraction_prompt(text)
    return call_gpt(prompt)


# Prompt template for Q&A

def build_qa_prompt(question, context):
    return f"""
You are a helpful assistant. Based on the context below, answer the user's question. If you can extract more information, update the table with any new insights.

CONTEXT:
{context}

QUESTION:
{question}

Answer and update only if confident. Return your output in markdown.
"""

def ask_question(question, context):
    prompt = build_qa_prompt(question, context)
    return call_gpt(prompt)
