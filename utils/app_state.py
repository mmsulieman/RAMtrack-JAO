import streamlit as st
import pandas as pd
from .data_io import load_csv, load_geojson, to_excel_bytes
from .planning_engine import generate_dynamic_monitoring_plan
from .checklist_engine import generate_checklist_requirements, compare_required_vs_achieved, generate_dummy_moda_submissions

def init_state():
    if "fdp_master" not in st.session_state:
        st.session_state["fdp_master"] = load_csv("fdp_master_sample.csv")
    if "assistance_plan" not in st.session_state:
        st.session_state["assistance_plan"] = load_csv("monthly_assistance_plan_sample.csv")
    if "tpm_assignment" not in st.session_state:
        st.session_state["tpm_assignment"] = load_csv("tpm_monitor_assignment_sample.csv")
    if "requirement_matrix" not in st.session_state:
        st.session_state["requirement_matrix"] = load_csv("checklist_requirement_matrix.csv")
    if "boundary_geojson" not in st.session_state:
        st.session_state["boundary_geojson"] = load_geojson()
    if "monitoring_plan" not in st.session_state:
        refresh_plan()
    if "moda_submissions" not in st.session_state:
        st.session_state["moda_submissions"] = generate_dummy_moda_submissions(st.session_state["checklist_requirements"])
        st.session_state["rva"] = compare_required_vs_achieved(st.session_state["checklist_requirements"], st.session_state["moda_submissions"])

def refresh_plan(month="May 2025", activity="All Activities", tpm_target=.70, large_threshold=35, split_large=True, priority_to_wfp=True):
    plan = generate_dynamic_monitoring_plan(
        st.session_state["fdp_master"],
        st.session_state["assistance_plan"],
        st.session_state["tpm_assignment"],
        month=month,
        activity=activity,
        tpm_target=tpm_target,
        large_threshold=large_threshold,
        split_large_woredas=split_large,
        priority_to_wfp=priority_to_wfp,
    )
    st.session_state["monitoring_plan"] = plan
    st.session_state["checklist_requirements"] = generate_checklist_requirements(plan, st.session_state["requirement_matrix"])
    if "moda_submissions" in st.session_state:
        st.session_state["rva"] = compare_required_vs_achieved(st.session_state["checklist_requirements"], st.session_state["moda_submissions"])

def refresh_rva():
    st.session_state["rva"] = compare_required_vs_achieved(st.session_state["checklist_requirements"], st.session_state["moda_submissions"])

def export_workbook():
    sheets = {
        "FDP Master": st.session_state.get("fdp_master", pd.DataFrame()),
        "Monthly Assistance Plan": st.session_state.get("assistance_plan", pd.DataFrame()),
        "TPM Assignment": st.session_state.get("tpm_assignment", pd.DataFrame()),
        "Monitoring Plan": st.session_state.get("monitoring_plan", pd.DataFrame()),
        "Checklist Requirements": st.session_state.get("checklist_requirements", pd.DataFrame()),
        "MoDA Submissions": st.session_state.get("moda_submissions", pd.DataFrame()),
        "Requirement vs Achieved": st.session_state.get("rva", pd.DataFrame()),
    }
    return to_excel_bytes(sheets)