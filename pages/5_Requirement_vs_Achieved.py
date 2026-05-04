import pandas as pd
import streamlit as st
from utils.app_state import init_state, refresh_rva, export_workbook
from utils.ui import inject_css, sidebar_brand, header, render_planning_kpis, fig_req_achieved, fig_heatmap

st.set_page_config(page_title="RAMTrack v3 | Requirement vs Achieved", page_icon="📈", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Checklist requirement versus achieved MoDA submissions by activity, entity, month, woreda and FDP", export_bytes=export_workbook(), export_name="RAMTrack_Requirement_vs_Achieved.xlsx")

rva = st.session_state["rva"]
render_planning_kpis(st.session_state["monitoring_plan"], rva)

if rva.empty:
    st.info("No requirement-vs-achieved data available.")
else:
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        acts = st.multiselect("Activity", sorted(rva["Activity"].dropna().unique()), default=sorted(rva["Activity"].dropna().unique()))
    with f2:
        ents = st.multiselect("Entity", sorted(rva["Entity"].dropna().unique()), default=sorted(rva["Entity"].dropna().unique()))
    with f3:
        stats = st.multiselect("Status", sorted(rva["Status"].dropna().unique()), default=sorted(rva["Status"].dropna().unique()))
    with f4:
        woredas = st.multiselect("Woreda", sorted(rva["Woreda"].dropna().unique()), default=sorted(rva["Woreda"].dropna().unique())[:10])
    filtered = rva[rva["Activity"].isin(acts) & rva["Entity"].isin(ents) & rva["Status"].isin(stats) & rva["Woreda"].isin(woredas)].copy()
    c1, c2 = st.columns([1,1.2])
    with c1:
        st.plotly_chart(fig_req_achieved(filtered), use_container_width=True)
    with c2:
        st.plotly_chart(fig_heatmap(filtered), use_container_width=True)
    show = filtered.copy()
    show["Completion %"] = show["Completion %"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
    st.markdown("<div class='panel-title'>Requirement vs Achieved Detail</div>", unsafe_allow_html=True)
    st.dataframe(show, use_container_width=True, hide_index=True)