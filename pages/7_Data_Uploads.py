import streamlit as st
from utils.app_state import init_state, refresh_plan, refresh_rva, export_workbook
from utils.data_io import read_uploaded_table
from utils.planning_engine import REQUIRED_FDP_COLUMNS
from utils.ui import inject_css, sidebar_brand, header, note

st.set_page_config(page_title="RAMTrack v3 | Data Uploads", page_icon="⬆", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Upload operational planning files: FDP master, monthly assistance plan, TPM assignment, requirements and MoDA exports", export_bytes=export_workbook(), export_name="RAMTrack_Data_Uploads.xlsx")

note("For best results, include stable FDP_ID in all files. If you do not have FDP_ID yet, create one from activity, woreda and FDP/site name before uploading.")

c1, c2 = st.columns(2)
with c1:
    fdp_file = st.file_uploader("Upload FDP master list", type=["csv","xlsx","xls"])
    assist_file = st.file_uploader("Upload monthly assistance prioritization plan", type=["csv","xlsx","xls"])
    tpm_file = st.file_uploader("Upload TPM field monitor assignment matrix", type=["csv","xlsx","xls"])
with c2:
    req_file = st.file_uploader("Upload checklist requirement matrix", type=["csv","xlsx","xls"])
    moda_file = st.file_uploader("Upload MoDA submissions export", type=["csv","xlsx","xls"])

if st.button("Load Uploaded Data and Refresh App", type="primary"):
    fdp = read_uploaded_table(fdp_file, st.session_state["fdp_master"])
    missing = [c for c in REQUIRED_FDP_COLUMNS if c not in fdp.columns]
    if missing:
        st.error(f"FDP master list missing required columns: {missing}")
    else:
        st.session_state["fdp_master"] = fdp
        st.session_state["assistance_plan"] = read_uploaded_table(assist_file, st.session_state["assistance_plan"])
        st.session_state["tpm_assignment"] = read_uploaded_table(tpm_file, st.session_state["tpm_assignment"])
        st.session_state["requirement_matrix"] = read_uploaded_table(req_file, st.session_state["requirement_matrix"])
        st.session_state["moda_submissions"] = read_uploaded_table(moda_file, st.session_state["moda_submissions"])
        refresh_plan()
        refresh_rva()
        st.success("Uploaded data loaded and plan/RVA refreshed.")

tabs = st.tabs(["FDP Master", "Monthly Assistance Plan", "TPM Assignment", "Requirement Matrix", "MoDA Submissions"])
with tabs[0]:
    st.dataframe(st.session_state["fdp_master"], use_container_width=True, hide_index=True)
with tabs[1]:
    st.dataframe(st.session_state["assistance_plan"], use_container_width=True, hide_index=True)
with tabs[2]:
    st.dataframe(st.session_state["tpm_assignment"], use_container_width=True, hide_index=True)
with tabs[3]:
    st.dataframe(st.session_state["requirement_matrix"], use_container_width=True, hide_index=True)
with tabs[4]:
    st.dataframe(st.session_state["moda_submissions"], use_container_width=True, hide_index=True)