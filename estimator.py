# === builder-assistant/estimator.py ===

import pandas as pd
import json

# Load material and labour pricing
with open("prices.json") as f:
    prices = json.load(f)

materials = prices["materials"]
labour = prices["labour"]


def parse_markdown_table(markdown):
    try:
        # Read markdown table into pandas
        table_lines = markdown.strip().splitlines()
        data = [line.strip('|').split('|') for line in table_lines if '|' in line and not line.strip().startswith('|---')]
        headers = [h.strip() for h in data[0]]
        rows = [[cell.strip() for cell in row] for row in data[1:]]
        df = pd.DataFrame(rows, columns=headers)

        # Convert numeric columns to float where possible
        for col in ['Length (m)', 'Width (m)', 'Height (m)', 'Floor Area (m²)', 'Wall Area (m²)']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle missing or assumed values
        df['Height (m)'] = df['Height (m)'].fillna(2.4)

        # Recalculate missing floor or wall area
        df['Floor Area (m²)'] = df['Floor Area (m²)'].fillna(df['Length (m)'] * df['Width (m)'])
        df['Wall Area (m²)'] = df['Wall Area (m²)'].fillna(
            2 * (df['Length (m)'] + df['Width (m)']) * df['Height (m)'])

        return df
    except Exception as e:
        print("Error parsing table:", e)
        return pd.DataFrame()


def estimate_costs(df, flooring_type, paint_type, wall_finish, radiator_required,
                   rewire_required, light_switch_type, num_double_sockets):
    results = []

    for _, row in df.iterrows():
        room = row.get("Room Name", "Unknown")
        floor_area = row.get("Floor Area (m²)", 0) or 0
        wall_area = row.get("Wall Area (m²)", 0) or 0

        paint_cost = wall_area * materials.get(paint_type.lower().replace(" ", "_") + "_per_m2", 0)
        wall_finish_cost = wall_area * (materials.get("wallpaper_per_m2", 0) if wall_finish == "Wallpaper" else 0)
        flooring_cost = floor_area * materials.get(flooring_type.lower() + "_per_m2", 0)

        # Labour costs
        paint_labour = wall_area * labour.get("paint_per_m2", 0)
        flooring_labour = floor_area * labour.get(flooring_type.lower() + "_per_m2", 0)

        radiator_cost = radiator_required * 150
        rewire_cost = floor_area * 40 if rewire_required else 0

        switch_cost_map = {
            "None": 0,
            "Single Switch (£4)": 4,
            "Double Switch (£6)": 6,
            "Single Dimmer (£8)": 8,
            "Double Dimmer (£10)": 10
        }
        switch_cost = switch_cost_map.get(light_switch_type, 0)
        socket_cost = num_double_sockets * 8

        total = paint_cost + wall_finish_cost + flooring_cost + paint_labour + flooring_labour + radiator_cost + rewire_cost + switch_cost + socket_cost

        results.append({
            "Room": room,
            "Floor Area (m²)": round(floor_area, 2),
            "Wall Area (m²)": round(wall_area, 2),
            "Paint £": round(paint_cost, 2),
            "Wall Finish £": round(wall_finish_cost, 2),
            "Flooring £": round(flooring_cost, 2),
            "Paint Labour £": round(paint_labour, 2),
            "Flooring Labour £": round(flooring_labour, 2),
            "Radiator £": radiator_cost,
            "Rewiring £": round(rewire_cost, 2),
            "Light Switch £": switch_cost,
            "Double Sockets (£)": socket_cost,
            "Total (£)": round(total, 2)
        })

    return pd.DataFrame(results)


def total_summary(cost_df):
    if cost_df.empty:
        return {}
    totals = cost_df.drop(columns=["Room"]).sum(numeric_only=True)
    return totals.to_dict()
