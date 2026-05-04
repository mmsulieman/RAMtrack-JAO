import json
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from utils.app_state import init_state, export_workbook
from utils.data_io import read_geojson_upload
from utils.mapping_engine import build_map, site_status_from_rva
from utils.ui import inject_css, sidebar_brand, header, note

st.set_page_config(page_title="RAMTrack v3 | Map and Gaps", page_icon="🗺", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Custom Somali Region map layer with visited, non-visited and incomplete monitoring status", export_bytes=export_workbook(), export_name="RAMTrack_Map_and_Gaps.xlsx")

note("The app includes a sample GeoJSON boundary layer for demonstration only. Replace it with your official Somali Region regional, zonal or woreda GeoJSON boundary file. The site markers use green for complete, orange for partial/moderate gap and red for not visited/critical gaps.")

uploaded_geo = st.file_uploader("Upload custom Somali Region / zone / woreda boundary GeoJSON", type=["geojson","json"])
if uploaded_geo is not None:
    st.session_state["boundary_geojson"] = read_geojson_upload(uploaded_geo, st.session_state["boundary_geojson"])
    st.success("Custom boundary layer loaded for this session.")

rva = st.session_state["rva"]
m = build_map(rva, st.session_state.get("boundary_geojson"))
st_folium(m, width=None, height=620)

st.markdown("<div class='panel-title'>Map-ready Site Status Table</div>", unsafe_allow_html=True)
site = site_status_from_rva(rva)
if not site.empty:
    show = site.copy()
    show["Completion %"] = show["Completion %"].map(lambda x: f"{x:.0%}")
    st.dataframe(show, use_container_width=True, hide_index=True)