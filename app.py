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
rewire_required = st.sidebar.checkbox("Rewire each room? (£40/m²)", value=False)
light_switch_type = st.sidebar.selectbox("Choose light switch type", [
    "None",
    "Single Switch (£4)",
    "Double Switch (£6)",
    "Single Dimmer (£8)",
    "Double Dimmer (£10)"
])
num_double_sockets = st.sidebar.selectbox("Number of double sockets per room", list(range(0, 11)))

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
rewire_cost_per_m2 = 40.0
light_switch_cost = 5.0
double_socket_cost = 8.0

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

    with st.spinner("🔍 Builder Assistant is reviewing the floor plan..."):
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
        st.session_state["room_table"] = combined_df
        st.dataframe(combined_df, use_container_width=True)

        st.subheader("💰 Cost Estimates")

        # Apply chosen material costs only
        df["Flooring Cost (£)"] = df["Floor Area (m²)"] * flooring_prices[flooring_type]

        if wall_finish == "Paint":
            wall_label = f"Paint ({paint_type}) (£)"
            df[wall_label] = df["Wall Area (m²)"] * paint_prices[paint_type]
        else:
            wall_label = "Wallpaper (£)"
            df[wall_label] = df["Wall Area (m²)"] * wallpaper_price_per_m2

        if radiator_required:
            df["Radiator Cost (£)"] = radiator_cost_per_room
        else:
            df["Radiator Cost (£)"] = 0

        if rewire_required:
            df["Rewire Cost (£)"] = df["Floor Area (m²)"] * rewire_cost_per_m2
        else:
            df["Rewire Cost (£)"] = 0

        switch_costs = {
    "None": 0,
    "Single Switch (£4)": 4,
    "Double Switch (£6)": 6,
    "Single Dimmer (£8)": 8,
    "Double Dimmer (£10)": 10
}
df["Light Switches (£)"] = switch_costs[light_switch_type]
        df["Double Sockets (£)"] = num_double_sockets * double_socket_cost

        # Final cost breakdown
        display_cols = [
            "Room Name", "Floor Area (m²)", "Wall Area (m²)", "Flooring Cost (£)", wall_label,
            "Radiator Cost (£)", "Rewire Cost (£)", "Light Switches (£)", "Double Sockets (£)"
        ]
        cost_df = df[display_cols].copy()

        # Add totals row
        numeric_cols = [col for col in cost_df.columns if "(£)" in col or "Area" in col]
        total_cost_row = pd.DataFrame(cost_df[numeric_cols].sum()).T
        total_cost_row.insert(0, "Room Name", "TOTAL")

        for col in cost_df.columns:
            if col not in total_cost_row.columns:
                total_cost_row[col] = ""

        combined_cost_df = pd.concat([cost_df, total_cost_row], ignore_index=True)
        st.session_state["cost_table"] = combined_cost_df
        st.dataframe(combined_cost_df, use_container_width=True)

        st.markdown("### 🧾 Total Summary")
        total_cost = combined_cost_df[numeric_cols].sum().sum()
        st.metric("Estimated Project Total (£)", f"£{total_cost:,.2f}")

        # Store session state for Q&A context
        st.session_state["context_table"] = df.to_markdown(index=False)

# --- Question & Answer ---
if "context_table" in st.session_state:
    st.markdown("---")
    st.subheader("💬 Ask the Builder Assistant")
    user_q = st.text_input("What would you like to ask about the plan?")
    if st.button("Ask the Builder Assistant") and user_q.strip():
        with st.spinner("Builder Assistant is reviewing your request..."):
            answer = ask_question(user_q, st.session_state["context_table"])
            st.markdown("### 💬 Assistant's Answer")
            st.write(answer)

        st.subheader("📋 Current Room Table")
        if "room_table" in st.session_state:
            st.dataframe(st.session_state["room_table"], use_container_width=True)

        st.subheader("💰 Current Cost Estimates")
        if "cost_table" in st.session_state:
            st.dataframe(st.session_state["cost_table"], use_container_width=True)
