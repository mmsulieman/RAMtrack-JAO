from pathlib import Path
from io import BytesIO
import json
import math
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

def _safe_sheet_name(name: str, used_names: set) -> str:
    """Excel sheet names must be unique and <=31 characters."""
    base = str(name)[:31] or "Sheet"
    safe = base
    i = 1
    while safe in used_names:
        suffix = f"_{i}"
        safe = base[:31 - len(suffix)] + suffix
        i += 1
    used_names.add(safe)
    return safe

def _safe_column_width(df: pd.DataFrame, col_index: int, col_name: str) -> int:
    """Robust width calculation that handles empty sheets, duplicate columns and all-null columns."""
    base_width = len(str(col_name)) + 2
    if df is None or df.empty:
        return max(12, min(36, base_width))

    try:
        # Use iloc, not df[col_name], because duplicate column names can return a DataFrame.
        series = df.iloc[:, col_index].astype(str)
        series = series.replace({"nan": "", "NaT": "", "None": ""})
        lengths = series.map(len)
        q = lengths.quantile(0.85) if not lengths.empty else 12
        if pd.isna(q) or not math.isfinite(float(q)):
            q = 12
        width = int(max(base_width, float(q) + 2))
    except Exception:
        width = max(12, base_width)

    return max(12, min(36, width))

def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """Create an Excel workbook safely for Streamlit download buttons.

    This version avoids the Streamlit Cloud ValueError that can occur when
    converting NaN/non-finite width estimates to int during column auto-sizing.
    """
    output = BytesIO()
    used_sheet_names = set()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for sheet_name, df in sheets.items():
            if df is None:
                df = pd.DataFrame()
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)

            safe = _safe_sheet_name(sheet_name, used_sheet_names)
            df.to_excel(writer, sheet_name=safe, index=False)

            workbook = writer.book
            worksheet = writer.sheets[safe]
            header = workbook.add_format({
                "bold": True,
                "bg_color": "#005EB8",
                "font_color": "white",
                "border": 1,
                "text_wrap": True,
            })

            for i, col in enumerate(df.columns):
                worksheet.write(0, i, str(col), header)
                width = _safe_column_width(df, i, col)
                worksheet.set_column(i, i, width)

            worksheet.freeze_panes(1, 0)

    return output.getvalue()
