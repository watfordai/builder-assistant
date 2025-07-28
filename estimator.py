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

        return df
    except Exception as e:
        print("Error parsing table:", e)
        return pd.DataFrame()


def estimate_costs(df):
    results = []

    for _, row in df.iterrows():
        room = row.get("Room Name", "Unknown")
        floor_area = row.get("Floor Area (m²)", 0) or 0
        wall_area = row.get("Wall Area (m²)", 0) or 0

        # Material costs
        paint_cost = wall_area * materials.get("paint_per_m2", 0)
        tile_cost = floor_area * materials.get("tile_per_m2", 0)
        carpet_cost = floor_area * materials.get("carpet_per_m2", 0)
        laminate_cost = floor_area * materials.get("laminate_per_m2", 0)

        # Labour costs
        paint_labour = wall_area * labour.get("paint_per_m2", 0)
        tile_labour = floor_area * labour.get("tile_per_m2", 0)
        carpet_labour = floor_area * labour.get("carpet_per_m2", 0)
        laminate_labour = floor_area * labour.get("laminate_per_m2", 0)

        results.append({
            "Room": room,
            "Floor Area (m²)": floor_area,
            "Wall Area (m²)": wall_area,
            "Paint £": paint_cost,
            "Paint Labour £": paint_labour,
            "Tile £": tile_cost,
            "Tile Labour £": tile_labour,
            "Carpet £": carpet_cost,
            "Carpet Labour £": carpet_labour,
            "Laminate £": laminate_cost,
            "Laminate Labour £": laminate_labour,
        })

    return pd.DataFrame(results)


def total_summary(cost_df):
    if cost_df.empty:
        return {}
    totals = cost_df.drop(columns=["Room"]).sum(numeric_only=True)
    return totals.to_dict()
