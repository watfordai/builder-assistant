# === builder-assistant/app.py ===

import streamlit as st
import os
from ocr import extract_text
from gpt import extract_rooms_from_text, ask_question
from estimator import parse_markdown_table, estimate_costs, total_summary
import pandas as pd

st.set_page_config(page_title="Builder Assistant", layout="wide")
st.title("🏗️ Builder Assistant MVP")

# --- Sidebar ---
st.sidebar.header("Upload a file")
uploaded_file = st.sidebar.file_uploader("Choose a PDF, DOCX or image", type=["pdf", "png", "jpg", "jpeg"])

st.sidebar.markdown("---")
manual_input = st.sidebar.text_area("Or paste architectural notes here:")

# Material selectors
st.sidebar.markdown("---")
flooring_type = st.sidebar.selectbox("Choose flooring type", ["Laminate", "Tile", "Carpet", "Vinyl"])
paint_type = st.sidebar.selectbox("Choose paint type", ["Standard Emulsion", "Premium Emulsion", "Gloss"])
wall_finish = st.sidebar.selectbox("Choose wall finish", ["Paint", "Wallpaper"])
radiator_required = st.sidebar.checkbox("Include radiators in each room?", value=True)

# --- Pricing logic ---
flooring_prices = {
    "Laminate": 20.0,
    "Tile": 30.0,
    "Carpet": 15.0,
    "Vinyl": 18.0
}

paint_prices = {
    "Standard Emulsion": 1.2,
    "Premium Emulsion": 2.0,
    "Gloss": 1.8
}

wallpaper_price_per_m2 = 3.5
radiator_cost_per_room = 150

process_button = st.sidebar.button("📄 Process Document")

# --- Main Output ---
if process_button:
    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        raw_text = extract_text(file_bytes, file_name)
    elif manual_input.strip():
        raw_text = manual_input.strip()
    else:
        st.warning("Please upload a file or paste some text.")
        st.stop()

    with st.spinner("Extracting room info using GPT-4..."):
        gpt_table_markdown = extract_rooms_from_text(raw_text)

        df = parse_markdown_table(gpt_table_markdown)
        if df.empty or df.columns[0] != "Room Name":
            st.warning("❌ We couldn't detect any room data. Try uploading a clearer image or more complete floorplan.")
            st.stop()

        # Assume default height of 2.4m if missing or blank
        df["Height (m)"] = pd.to_numeric(df["Height (m)"], errors='coerce')
        df.loc[df["Height (m)"].isna() | (df["Height (m)"] == 0), "Height (m)"] = 2.4

        # Calculate wall area: 2 × (L + W) × H
        df["Length (m)"] = pd.to_numeric(df["Length (m)"], errors='coerce')
        df["Width (m)"] = pd.to_numeric(df["Width (m)"], errors='coerce')
        df["Wall Area (m²)"] = 2 * (df["Length (m)"] + df["Width (m)"]) * df["Height (m)"]
        df["Wall Area (m²)"] = df["Wall Area (m²)"].round(2)

        st.subheader("📋 Extracted Room Table")
        total_row = df[["Floor Area (m²)", "Wall Area (m²)"]].sum().to_frame().T
        total_row.insert(0, "Room Name", "TOTAL")
        combined_df = pd.concat([df, total_row], ignore_index=True)
        st.dataframe(combined_df, use_container_width=True)

        st.subheader("💰 Cost Estimates")

        # Apply chosen material costs only
        df["Flooring Cost (£)"] = df["Floor Area (m²)"] * flooring_prices[flooring_type]

        if wall_finish == "Paint":
            df["Wall Finish"] = paint_type
            df["Wall Finish Cost (£)"] = df["Wall Area (m²)"] * paint_prices[paint_type]
        else:
            df["Wall Finish"] = "Wallpaper"
            df["Wall Finish Cost (£)"] = df["Wall Area (m²)"] * wallpaper_price_per_m2

        if radiator_required:
            df["Radiator Cost (£)"] = radiator_cost_per_room
        else:
            df["Radiator Cost (£)"] = 0

        # Final cost breakdown
        cost_df = df[["Room Name", "Floor Area (m²)", "Wall Area (m²)", "Flooring Cost (£)", "Wall Finish", "Wall Finish Cost (£)", "Radiator Cost (£)"]].copy()

        # Add totals row
        numeric_cols = ["Floor Area (m²)", "Wall Area (m²)", "Flooring Cost (£)", "Wall Finish Cost (£)", "Radiator Cost (£)"]
        total_cost_row = pd.DataFrame(cost_df[numeric_cols].sum()).T
        total_cost_row.insert(0, "Room Name", "TOTAL")
        total_cost_row["Wall Finish"] = ""

        combined_cost_df = pd.concat([cost_df, total_cost_row], ignore_index=True)
        st.dataframe(combined_cost_df, use_container_width=True)

        st.markdown("### 🧾 Total Summary")
        total_cost = combined_cost_df[numeric_cols].sum().sum()
        st.metric("Estimated Project Total (£)", f"£{total_cost:,.2f}")

        # Store session state for Q&A
        st.session_state["context_table"] = df.to_markdown(index=False)

# --- Question & Answer ---
if "context_table" in st.session_state:
    st.markdown("---")
    st.subheader("🤔 Ask a question")
    user_q = st.text_input("What would you like to ask about the plan?")
    if st.button("Ask GPT") and user_q.strip():
        with st.spinner("Thinking..."):
            answer = ask_question(user_q, st.session_state["context_table"])
            st.markdown("### 💬 GPT Answer")
            st.write(answer)
