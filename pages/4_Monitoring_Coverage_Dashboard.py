
import pandas as pd
import streamlit as st
from utils.app_state import init_state, export_workbook
from utils.ui import (
    inject_css, sidebar_brand, header, render_planning_kpis,
    fig_gauge, fig_coverage_planned_visited, fig_entity_contribution,
    fig_monthly_coverage_trend, fig_woreda_coverage_bar
)
from utils.coverage_engine import (
    build_site_coverage_table, summarize_coverage, coverage_metrics, auto_insights
)

st.set_page_config(page_title="RAMTrack v3 | Monitoring Coverage Dashboard", page_icon="📍", layout="wide")
inject_css(); sidebar_brand(); init_state()

header(
    subtitle="Monitoring visit coverage by activity, entity, month, location and checklist completion status",
    export_bytes=export_workbook(),
    export_name="RAMTrack_Monitoring_Coverage_Dashboard.xlsx"
)

plan = st.session_state["monitoring_plan"]
rva = st.session_state["rva"]
site_cov = build_site_coverage_table(plan, rva)

if site_cov.empty:
    st.info("No monitoring plan data is available. Generate a monitoring plan first.")
    st.stop()

st.markdown("<div class='panel-title'>Coverage Filters</div>", unsafe_allow_html=True)
f1, f2, f3, f4, f5 = st.columns(5)
with f1:
    months = st.multiselect("Month", sorted(site_cov["Month"].dropna().unique()), default=sorted(site_cov["Month"].dropna().unique()))
with f2:
    activities = st.multiselect("Activity", sorted(site_cov["Activity"].dropna().unique()), default=sorted(site_cov["Activity"].dropna().unique()))
with f3:
    entities = st.multiselect("Entity", sorted(site_cov["Entity"].dropna().unique()), default=sorted(site_cov["Entity"].dropna().unique()))
with f4:
    suboffices = st.multiselect("Sub-office", sorted(site_cov["Sub-office"].dropna().unique()), default=sorted(site_cov["Sub-office"].dropna().unique()))
with f5:
    visited_status = st.multiselect("Visited Status", sorted(site_cov["Visited Status"].dropna().unique()), default=sorted(site_cov["Visited Status"].dropna().unique()))

f6, f7, f8, f9 = st.columns(4)
with f6:
    zones = st.multiselect("Zone", sorted(site_cov["Zone"].dropna().unique()), default=sorted(site_cov["Zone"].dropna().unique()))
with f7:
    woredas = st.multiselect("Woreda", sorted(site_cov["Woreda"].dropna().unique()), default=sorted(site_cov["Woreda"].dropna().unique()))
with f8:
    priorities = st.multiselect("Priority Level", sorted(site_cov["Monthly Priority Level"].dropna().unique()), default=sorted(site_cov["Monthly Priority Level"].dropna().unique()))
with f9:
    checklist_status = st.multiselect("Checklist Status", sorted(site_cov["Checklist Status"].dropna().unique()), default=sorted(site_cov["Checklist Status"].dropna().unique()))

filtered = site_cov[
    site_cov["Month"].isin(months) &
    site_cov["Activity"].isin(activities) &
    site_cov["Entity"].isin(entities) &
    site_cov["Sub-office"].isin(suboffices) &
    site_cov["Visited Status"].isin(visited_status) &
    site_cov["Zone"].isin(zones) &
    site_cov["Woreda"].isin(woredas) &
    site_cov["Monthly Priority Level"].isin(priorities) &
    site_cov["Checklist Status"].isin(checklist_status)
].copy()

m = coverage_metrics(filtered)

# KPI row tailored to visit coverage
k1, k2, k3, k4, k5, k6, k7, k8, k9 = st.columns(9)
k1.metric("Planned Sites", f"{m['planned']:,}")
k2.metric("Visited Sites", f"{m['visited']:,}")
k3.metric("Overall Coverage", f"{m['coverage']:.0%}")
k4.metric("WFP Covered", f"{m['wfp_visited']:,}")
k5.metric("TPM Covered", f"{m['tpm_visited']:,}")
k6.metric("WFP Share", f"{m['wfp_share']:.0%}")
k7.metric("TPM Share", f"{m['tpm_share']:.0%}")
k8.metric("Unvisited Priority", f"{m['priority_unvisited']:,}")
k9.metric("70/30 Deviation", f"WFP {m['wfp_deviation']:+.0%}")

st.markdown("<div class='panel-title'>Gauge View: Overall and Activity-Specific Coverage</div>", unsafe_allow_html=True)

# Overall gauge and activity gauges
overall_wfp_share = m["wfp_share"]
overall_tpm_share = m["tpm_share"]
gcols = st.columns(4)
with gcols[0]:
    st.plotly_chart(fig_gauge("Overall Coverage", m["coverage"], overall_wfp_share, overall_tpm_share, m["planned"], m["visited"]), use_container_width=True)

for idx, activity_name in enumerate(["Activity 1 Relief", "Activity 2 Nutrition", "Activity 3 Refugee Operations"], start=1):
    sub = filtered[filtered["Activity"].eq(activity_name)]
    am = coverage_metrics(sub)
    with gcols[idx]:
        label = activity_name.replace("Activity 1 ", "A1 ").replace("Activity 2 ", "A2 ").replace("Activity 3 ", "A3 ")
        st.plotly_chart(fig_gauge(label, am["coverage"], am["wfp_share"], am["tpm_share"], am["planned"], am["visited"]), use_container_width=True)

st.markdown("<div class='panel-title'>Supporting Coverage Insights</div>", unsafe_allow_html=True)
summary_activity = summarize_coverage(filtered, by=["Activity"])
c1, c2, c3 = st.columns([1,1,1])
with c1:
    st.plotly_chart(fig_coverage_planned_visited(summary_activity), use_container_width=True)
with c2:
    st.plotly_chart(fig_entity_contribution(filtered), use_container_width=True)
with c3:
    st.plotly_chart(fig_monthly_coverage_trend(filtered), use_container_width=True)

c4, c5 = st.columns([1.1, .9])
with c4:
    st.plotly_chart(fig_woreda_coverage_bar(filtered), use_container_width=True)
with c5:
    st.markdown("<div class='panel-title'>Management Insights</div>", unsafe_allow_html=True)
    for insight in auto_insights(filtered):
        st.markdown(f"- {insight}")

st.markdown("<div class='panel-title'>Operational Follow-up: Unvisited and Incomplete Sites</div>", unsafe_allow_html=True)
gap_sites = filtered[filtered["Coverage Status"].isin(["Planned but not visited", "Visited but checklist incomplete"])].copy()
gap_sites = gap_sites.sort_values(["Coverage Status", "Monthly Priority Level", "Activity", "Woreda"])
display_cols = [
    "Month", "Activity", "Entity", "Zone", "Woreda", "FDP/Site Name",
    "Monthly Priority Level", "TPM Assigned to Woreda", "Reassignment Needed",
    "Required", "Achieved", "Checklist Completion %", "Coverage Status"
]
show = gap_sites[[c for c in display_cols if c in gap_sites.columns]].copy()
if "Checklist Completion %" in show.columns:
    show["Checklist Completion %"] = show["Checklist Completion %"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
st.dataframe(show, use_container_width=True, hide_index=True)

data = filtered.copy()
data["Coverage %"] = data["Coverage %"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
data["Checklist Completion %"] = data["Checklist Completion %"].map(lambda x: f"{x:.0%}" if pd.notna(x) else "")
st.download_button(
    "Download filtered coverage table",
    data=data.to_csv(index=False).encode("utf-8"),
    file_name="RAMTrack_Filtered_Monitoring_Coverage_Table.csv",
    mime="text/csv"
)
