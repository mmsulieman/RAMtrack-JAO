import streamlit as st
from utils.app_state import init_state, export_workbook
from utils.ui import inject_css, sidebar_brand, header, render_planning_kpis, fig_allocation, fig_activity_alloc, fig_req_achieved, fig_heatmap, fig_readiness, note

st.set_page_config(page_title="RAMTrack v3 | Executive Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()
sidebar_brand()
init_state()

header(export_bytes=export_workbook(), export_name="RAMTrack_v3_Workbook.xlsx")
note("RAMTrack v3 is designed as a dynamic monthly planning tool: it first filters assistance-prioritized FDPs/sites, checks JarCo TPM monitor availability by woreda, applies practical 70/30 WFP–TPM allocation, flags reassignment needs, and then compares required checklists against MoDA submissions.")

plan = st.session_state["monitoring_plan"]
rva = st.session_state["rva"]

render_planning_kpis(plan, rva)

c1, c2, c3 = st.columns([1,1,1.2])
with c1:
    st.markdown("<div class='panel-title'>WFP vs TPM Planned Allocation</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_allocation(plan), use_container_width=True)
with c2:
    st.markdown("<div class='panel-title'>Allocation by Activity</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_activity_alloc(plan), use_container_width=True)
with c3:
    st.markdown("<div class='panel-title'>Checklist Completion Heatmap</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_heatmap(rva), use_container_width=True)

c4, c5 = st.columns([1,1])
with c4:
    st.markdown("<div class='panel-title'>Required vs Achieved Checklists</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_req_achieved(rva), use_container_width=True)
with c5:
    st.markdown("<div class='panel-title'>TPM Reassignment Need</div>", unsafe_allow_html=True)
    st.plotly_chart(fig_readiness(plan), use_container_width=True)

st.markdown("<div class='panel-title'>Priority Planning and Checklist Gaps</div>", unsafe_allow_html=True)
gaps = rva[rva["Status"].isin(["Critical Gap","Not Visited / Not Submitted","Moderate Gap"])].sort_values(["Status","Activity","Entity","Woreda"]).head(30)
st.dataframe(gaps[["Activity","Entity","Woreda","FDP/Site Name","Checklist Type","Required Count","Achieved","Gap","Status"]], use_container_width=True, hide_index=True)