import streamlit as st
from utils.app_state import init_state, refresh_plan, export_workbook
from utils.ui import inject_css, sidebar_brand, header, note

st.set_page_config(page_title="RAMTrack v3 | TPM Assignment", page_icon="👥", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="TPM Field Monitor Assignment Matrix: reflect JarCo monitor coverage and reassignment readiness", export_bytes=export_workbook(), export_name="RAMTrack_TPM_Assignment.xlsx")

note("Use this page to record which woredas have assigned JarCo TPM field monitors, where no TPM is assigned, and where reassignment is possible if WFP shares priority information early.")

tpm = st.session_state["tpm_assignment"]
edited = st.data_editor(
    tpm,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "TPM Assigned to Woreda": st.column_config.SelectboxColumn("TPM Assigned to Woreda", options=["Yes","No"]),
        "TPM Available This Month": st.column_config.SelectboxColumn("TPM Available This Month", options=["Yes","No"]),
        "Reassignment Possible": st.column_config.SelectboxColumn("Reassignment Possible", options=["Yes","No"]),
    }
)
if st.button("Save TPM Assignment and Refresh Plan", type="primary"):
    st.session_state["tpm_assignment"] = edited
    refresh_plan()
    st.success("TPM assignment matrix saved and monitoring plan refreshed.")

st.markdown("<div class='panel-title'>TPM Coverage Matrix Summary</div>", unsafe_allow_html=True)
summary = edited.groupby(["Month","Sub-office","Zone","TPM Assigned to Woreda","TPM Available This Month","Reassignment Possible"])["Woreda"].nunique().reset_index(name="Woredas")
st.dataframe(summary, use_container_width=True, hide_index=True)