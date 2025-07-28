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
        st.dataframe(df, use_container_width=True)

        st.subheader("💰 Cost Estimates")
        cost_df = estimate_costs(df)
        st.dataframe(cost_df, use_container_width=True)

        st.markdown("### 🧾 Total Summary")
        totals = total_summary(cost_df)
        if totals:
            summary_df = pd.DataFrame(totals.items(), columns=["Category", "Value"])
            summary_df["Value"] = summary_df["Value"].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)
            st.table(summary_df)
        else:
            st.info("No costs to summarize.")

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
