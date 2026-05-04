import numpy as np
import pandas as pd
import streamlit as st
from utils.app_state import init_state, refresh_plan, export_workbook
from utils.checklist_engine import generate_checklist_requirements, compare_required_vs_achieved
from utils.ui import inject_css, sidebar_brand, header, render_planning_kpis, fig_allocation, fig_activity_alloc, note

st.set_page_config(page_title="RAMTrack v3 | Generate Monitoring Plan", page_icon="⚙", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Generate dynamic 70/30 monitoring plan using monthly assistance priorities and TPM availability", export_bytes=export_workbook(), export_name="RAMTrack_Dynamic_Monitoring_Plan.xlsx")

fdp = st.session_state["fdp_master"]
activity_options = ["All Activities"] + sorted(fdp["Activity"].dropna().unique().tolist())

c = st.columns([1.1,1.2,.8,.9,1.0,1.0,1.0,1.2])
with c[0]:
    month = st.selectbox("Reporting Month", ["May 2025","January 2026","February 2026","March 2026"], index=0)
with c[1]:
    activity = st.selectbox("Activity", activity_options)
with c[2]:
    tpm_target = st.selectbox("TPM Target", [0.60,0.65,0.70,0.75,0.80], index=2, format_func=lambda x: f"{x:.0%}")
with c[3]:
    large_threshold = st.number_input("Large Woreda Threshold", min_value=1, max_value=100, value=35)
with c[4]:
    split_large = st.selectbox("Split Large Woredas", [True, False], format_func=lambda x: "Enabled" if x else "Disabled")
with c[5]:
    priority_to_wfp = st.selectbox("Priority Sites to WFP", [True, False], format_func=lambda x: "Enabled" if x else "Disabled")
with c[6]:
    run = st.button("Generate Dynamic Plan", type="primary", use_container_width=True)
with c[7]:
    st.download_button("Export Plan", data=export_workbook(), file_name="RAMTrack_Dynamic_Monitoring_Plan.xlsx", use_container_width=True)

if run:
    refresh_plan(month=month, activity=activity, tpm_target=float(tpm_target), large_threshold=int(large_threshold), split_large=bool(split_large), priority_to_wfp=bool(priority_to_wfp))
    st.success("Dynamic monitoring plan generated.")

plan = st.session_state["monitoring_plan"]
rva = st.session_state["rva"]
render_planning_kpis(plan, rva)

c1, c2, c3 = st.columns([1,1,1])
with c1:
    st.plotly_chart(fig_allocation(plan), use_container_width=True)
with c2:
    st.plotly_chart(fig_activity_alloc(plan), use_container_width=True)
with c3:
    st.markdown("<div class='panel-title'>Planning Rules Applied</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='rule-box'>
      <div>1. Exclude FDPs/sites not prioritized for assistance this month.</div>
      <div>2. Prefer TPM where JarCo monitors are assigned and available.</div>
      <div>3. Assign WFP where no TPM is assigned or high-priority assurance is required.</div>
      <div>4. Flag JarCo reassignment where possible and needed.</div>
      <div>5. Rebalance toward 70/30 only where operationally feasible.</div>
    </div>
    """, unsafe_allow_html=True)

override_count = int((plan.get("Manual Override Entity", pd.Series(dtype=str)).astype(str).str.len() > 0).sum()) if not plan.empty else 0
req_count = int(st.session_state["checklist_requirements"]["Required Count"].sum()) if not st.session_state["checklist_requirements"].empty else 0
st.markdown(f"<div class='plan-topbar'><span>Manual Override: {override_count}</span><span>Checklist Requirements Auto-generated: {req_count:,}</span></div>", unsafe_allow_html=True)

edited = st.data_editor(
    plan,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "Manual Override Entity": st.column_config.SelectboxColumn("Manual Override Entity", options=["","WFP","TPM"]),
        "Final Entity": st.column_config.SelectboxColumn("Final Entity", options=["WFP","TPM"]),
        "Reassignment Status": st.column_config.SelectboxColumn("Reassignment Status", options=["","Pending JarCo confirmation","Agreed","Not feasible"]),
    }
)
if st.button("Apply Manual Overrides and Recalculate Requirements"):
    if "Manual Override Entity" in edited.columns:
        edited["Final Entity"] = np.where(edited["Manual Override Entity"].astype(str).str.len() > 0, edited["Manual Override Entity"], edited["Planned Entity"])
    st.session_state["monitoring_plan"] = edited
    st.session_state["checklist_requirements"] = generate_checklist_requirements(edited, st.session_state["requirement_matrix"])
    st.session_state["rva"] = compare_required_vs_achieved(st.session_state["checklist_requirements"], st.session_state["moda_submissions"])
    st.success("Overrides applied and checklist requirements recalculated.")