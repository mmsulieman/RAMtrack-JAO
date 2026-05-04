import streamlit as st
from utils.app_state import init_state, refresh_plan, export_workbook
from utils.ui import inject_css, sidebar_brand, header, note

st.set_page_config(page_title="RAMTrack v3 | Assistance Prioritization", page_icon="🗓", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Monthly Assistance Prioritization: define which relief/nutrition/refugee FDPs are active this month", export_bytes=export_workbook(), export_name="RAMTrack_Assistance_Prioritization.xlsx")

note("For Activity 1 Relief, assistance is needs- and vulnerability-based. This page lets you define the woredas/FDPs prioritized for the month. The monitoring plan is generated only from sites where Assistance Planned = Yes.")

assist = st.session_state["assistance_plan"]
edited = st.data_editor(
    assist,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "Assistance Planned": st.column_config.SelectboxColumn("Assistance Planned", options=["Yes","No"]),
        "Monthly Priority Level": st.column_config.SelectboxColumn("Monthly Priority Level", options=["High","Medium","Low","Critical","Management Priority"]),
    }
)
if st.button("Save Assistance Prioritization and Refresh Plan", type="primary"):
    st.session_state["assistance_plan"] = edited
    refresh_plan()
    st.success("Monthly assistance prioritization saved and monitoring plan refreshed.")

st.markdown("<div class='panel-title'>Assistance Prioritization Summary</div>", unsafe_allow_html=True)
summary = edited.groupby(["Month","Activity","Assistance Planned"])["FDP_ID"].nunique().reset_index(name="FDPs/Sites")
st.dataframe(summary, use_container_width=True, hide_index=True)