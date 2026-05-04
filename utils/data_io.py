from pathlib import Path
from io import BytesIO
import json
import pandas as pd
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = APP_ROOT / "sample_data"
GEODATA_DIR = APP_ROOT / "geodata"

def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DIR / name)

def load_geojson(name: str = "somali_woreda_boundaries_sample.geojson") -> dict:
    with open(GEODATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)

def read_uploaded_table(uploaded, default_df=None) -> pd.DataFrame:
    if uploaded is None:
        return default_df.copy() if default_df is not None else pd.DataFrame()
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded)
    st.error("Unsupported file type. Upload CSV or Excel.")
    return default_df.copy() if default_df is not None else pd.DataFrame()

def read_geojson_upload(uploaded, default_geojson=None):
    if uploaded is None:
        return default_geojson
    try:
        return json.load(uploaded)
    except Exception as e:
        st.error(f"Could not read GeoJSON: {e}")
        return default_geojson

def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, df in sheets.items():
            safe = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe, index=False)
            workbook = writer.book
            worksheet = writer.sheets[safe]
            header = workbook.add_format({"bold": True, "bg_color": "#005EB8", "font_color": "white", "border": 1, "text_wrap": True})
            for i, col in enumerate(df.columns):
                worksheet.write(0, i, col, header)
                width = max(12, min(36, max(len(str(col)), int(df[col].astype(str).str.len().quantile(0.85)) if not df.empty else 12)))
                worksheet.set_column(i, i, width)
            worksheet.freeze_panes(1, 0)
    return output.getvalue()