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
import json
st.sidebar.header("📂 Session Management")

session_name = st.sidebar.text_input("Session name (for saving/loading)")
if st.sidebar.button("💾 Save Session"):
    if session_name:
        session_data = {
            "room_table": st.session_state.get("room_table", pd.DataFrame()).to_dict(),
            "cost_table": st.session_state.get("cost_table", pd.DataFrame()).to_dict()
        }
        with open(f"{session_name}.json", "w") as f:
            json.dump(session_data, f)
        st.sidebar.success("✅ Session saved successfully.")
    else:
        st.sidebar.warning("⚠️ Please enter a session name to save.")

existing_sessions = [f for f in os.listdir() if f.endswith(".json")]
if existing_sessions:
    selected_session = st.sidebar.selectbox("Select a session to load", existing_sessions)
    if st.sidebar.button("📂 Load Selected Session"):
        with open(selected_session, "r") as f:
            session_data = json.load(f)
            st.session_state["room_table"] = pd.DataFrame(session_data["room_table"])
            st.session_state["cost_table"] = pd.DataFrame(session_data["cost_table"])
            st.session_state["context_table"] = st.session_state["room_table"].to_markdown(index=False)
        st.sidebar.success(f"✅ Loaded session: {selected_session}")
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
room_height = st.sidebar.number_input("Ceiling height (m)", min_value=2.0, max_value=4.0, value=2.4, step=0.1)
measurement_unit = st.sidebar.selectbox("Are the dimensions in:", ["Metric (m)", "Imperial (ft)"])

# Conversion factor
ft_to_m = 0.3048
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


if process_button:
    # Placeholder: insert processing logic here once integrated
    pass

# --- Restore Previous Session if Loaded ---
if "room_table" in st.session_state and "cost_table" in st.session_state and not process_button:
    # Display tables after loading session
    st.subheader("📋 Extracted Room Table")
    st.dataframe(st.session_state["room_table"], use_container_width=True)

    st.subheader("💰 Cost Estimates")
    st.dataframe(st.session_state["cost_table"], use_container_width=True)

    st.markdown("### 🧾 Total Summary")
    summary_numeric_cols = [col for col in st.session_state["cost_table"].columns if "(£)" in col or "Area" in col]
    total_cost = st.session_state["cost_table"][summary_numeric_cols].sum().sum()
    st.metric("Estimated Project Total (£)", f"£{total_cost:,.2f}")
