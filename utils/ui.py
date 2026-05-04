import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from .checklist_engine import summarize_rva
from .planning_engine import planning_readiness

WFP_BLUE = "#005EB8"
WFP_DARK = "#003A70"
TPM_TEAL = "#16B6A1"

def inject_css():
    st.markdown("""
    <style>
    :root {
        --wfp-blue: #005EB8;
        --wfp-blue-2: #0072CE;
        --wfp-dark: #003A70;
        --wfp-navy: #082F57;
        --surface: #FFFFFF;
        --page-bg: #F4F7FB;
        --border: #E5E7EB;
        --text: #0F172A;
        --muted: #64748B;
        --success: #16A34A;
        --warning: #F59E0B;
        --danger: #DC2626;
    }

    html, body, [class*="css"], [class*="st-emotion"] {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    body {
        background: var(--page-bg);
    }

    /* Use full viewport on desktop, with comfortable padding */
    .block-container {
        padding-top: 1.05rem !important;
        padding-left: 1.35rem !important;
        padding-right: 1.35rem !important;
        padding-bottom: 4.8rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    div[data-testid="stAppViewContainer"] > .main {
        background: var(--page-bg);
    }

    /* Sidebar: force readable white labels across Streamlit versions */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #005EB8 0%, #074B8F 60%, #083B72 100%) !important;
        color: #F8FAFC !important;
        min-width: 255px !important;
    }

    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] li {
        color: #F8FAFC !important;
        font-size: 0.98rem !important;
    }

    /* Streamlit multipage navigation */
    section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] p {
        color: #F8FAFC !important;
        font-weight: 650 !important;
        font-size: 0.96rem !important;
        line-height: 1.25 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] a {
        border-radius: 12px !important;
        padding: 0.58rem 0.72rem !important;
        margin: 0.16rem 0 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.14) !important;
    }

    /* Sidebar custom brand/help */
    .sidebar-logo {
        display: flex;
        gap: 12px;
        align-items: center;
        margin-bottom: 1rem;
        padding: .55rem 0 1rem 0;
        border-bottom: 1px solid rgba(255,255,255,.18);
    }

    .sidebar-logo-mark {
        min-width: 58px;
        width: 58px;
        height: 58px;
        border-radius: 14px;
        background: rgba(255,255,255,.14);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 850;
        letter-spacing: .5px;
        border: 1px solid rgba(255,255,255,.18);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,.05);
    }

    .sidebar-title {
        font-weight: 850 !important;
        font-size: 1.06rem !important;
        line-height: 1.12 !important;
        color: #FFFFFF !important;
    }

    .sidebar-sub {
        font-size: .86rem !important;
        opacity: .94;
        margin-top: 4px;
        color: #DBEAFE !important;
    }

    section[data-testid="stSidebar"] .stExpander {
        background: rgba(255,255,255,.08) !important;
        border: 1px solid rgba(255,255,255,.14) !important;
        border-radius: 13px !important;
        margin-bottom: .55rem !important;
    }

    section[data-testid="stSidebar"] .stExpander summary {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: .95rem !important;
    }

    section[data-testid="stSidebar"] .stWarning,
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        background: rgba(255,255,255,.12) !important;
        color: #FFFFFF !important;
        border-color: rgba(255,255,255,.18) !important;
    }

    /* Headers */
    .page-title {
        font-size: clamp(1.45rem, 2.2vw, 2.15rem);
        font-weight: 850;
        color: #0A4A8F;
        line-height: 1.12;
        letter-spacing: -0.02em;
    }

    .page-subtitle {
        font-size: clamp(.88rem, 1.2vw, 1.02rem);
        color: #667085;
        margin-top: .25rem;
        margin-bottom: .85rem;
        max-width: 84rem;
    }

    /* KPI cards */
    .metric-tile {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 15px 15px;
        display: flex;
        gap: 12px;
        align-items: center;
        min-height: 92px;
        height: 100%;
        box-shadow: 0 5px 16px rgba(16,24,40,.05);
        overflow: hidden;
    }

    .metric-icon {
        min-width: 48px;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.18rem;
        font-weight: 850;
    }

    .metric-label {
        font-size: .84rem;
        color: #475467;
        font-weight: 700;
        line-height: 1.18;
    }

    .metric-value {
        font-size: clamp(1.32rem, 2vw, 1.85rem);
        font-weight: 850;
        color: #0F172A;
        line-height: 1.12;
        word-break: break-word;
    }

    .panel-title {
        font-weight: 850;
        color: #0A4A8F;
        margin: 1rem 0 .35rem;
        font-size: 1.02rem;
        letter-spacing: -0.01em;
    }

    .rule-box,
    .note-box {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 14px 16px;
        line-height: 1.95;
        box-shadow: 0 5px 16px rgba(16,24,40,.05);
        overflow-wrap: anywhere;
    }

    .note-box {
        background: #F8FBFF;
        border-color: #D9E8F7;
        border-left: 5px solid #005EB8;
        color: #1F2937;
        margin: 8px 0;
    }

    .plan-topbar {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
        background: #FFF7E6;
        border: 1px solid #F1D5A8;
        color: #6B4E16;
        padding: 10px 14px;
        border-radius: 12px;
        margin: 10px 0 8px;
        font-weight: 700;
    }

    /* Cards around charts and tables */
    [data-testid="stPlotlyChart"],
    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"] {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 6px;
        box-shadow: 0 5px 16px rgba(16,24,40,.05);
        overflow-x: auto;
    }

    [data-testid="stDataFrame"] div,
    [data-testid="stDataEditor"] div {
        font-size: .86rem;
    }

    /* Inputs and buttons */
    .stButton button,
    div.stDownloadButton > button {
        background: #0B63CE;
        color: #FFFFFF !important;
        border: 1px solid #0B63CE;
        font-weight: 700;
        border-radius: 10px;
        min-height: 2.55rem;
        white-space: normal;
    }

    .stButton button:hover,
    div.stDownloadButton > button:hover {
        background: #094EA3;
        border-color: #094EA3;
        color: #FFFFFF !important;
    }

    [data-testid="stSelectbox"],
    [data-testid="stMultiSelect"],
    [data-testid="stTextInput"],
    [data-testid="stNumberInput"],
    [data-testid="stFileUploader"] {
        min-width: 0 !important;
    }

    label[data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] p {
        font-size: .82rem !important;
        font-weight: 650 !important;
        color: #344054 !important;
    }

    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #005EB8;
        color: #FFFFFF;
        text-align: center;
        padding: 8px 10px;
        font-size: .82rem;
        z-index: 999;
        box-shadow: 0 -2px 10px rgba(0,0,0,.08);
    }

    /* Better chart scaling */
    .js-plotly-plot, .plot-container {
        width: 100% !important;
    }

    /* Tablet layout improvements */
    @media (max-width: 1024px) {
        .block-container {
            padding-left: .9rem !important;
            padding-right: .9rem !important;
            padding-top: .8rem !important;
        }

        .page-title {
            font-size: 1.55rem !important;
        }

        .page-subtitle {
            font-size: .9rem !important;
        }

        .metric-tile {
            min-height: 82px;
            padding: 12px;
        }

        .metric-icon {
            min-width: 42px;
            width: 42px;
            height: 42px;
            font-size: 1rem;
        }

        .metric-label {
            font-size: .78rem;
        }

        .metric-value {
            font-size: 1.28rem;
        }

        section[data-testid="stSidebar"] {
            min-width: 230px !important;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] a {
            font-size: .92rem !important;
        }
    }

    /* Mobile layout improvements */
    @media (max-width: 760px) {
        .block-container {
            padding-left: .55rem !important;
            padding-right: .55rem !important;
            padding-top: .55rem !important;
            padding-bottom: 5.6rem !important;
        }

        .page-title {
            font-size: 1.28rem !important;
            line-height: 1.18 !important;
        }

        .page-subtitle {
            font-size: .82rem !important;
            margin-bottom: .55rem;
        }

        .metric-tile {
            min-height: 74px;
            padding: 10px;
            border-radius: 14px;
            gap: 9px;
        }

        .metric-icon {
            min-width: 36px;
            width: 36px;
            height: 36px;
            font-size: .9rem;
        }

        .metric-label {
            font-size: .72rem;
        }

        .metric-value {
            font-size: 1.12rem;
        }

        .panel-title {
            font-size: .92rem;
            margin-top: .75rem;
        }

        [data-testid="stPlotlyChart"] {
            padding: 2px;
            border-radius: 12px;
        }

        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"] {
            padding: 2px;
            border-radius: 12px;
        }

        [data-testid="stDataFrame"] div,
        [data-testid="stDataEditor"] div {
            font-size: .75rem !important;
        }

        .stButton button,
        div.stDownloadButton > button {
            width: 100%;
            min-height: 2.4rem;
            font-size: .82rem;
        }

        .footer {
            font-size: .68rem;
            padding: 7px 8px;
        }

        section[data-testid="stSidebar"] {
            min-width: 210px !important;
        }

        .sidebar-logo-mark {
            min-width: 44px;
            width: 44px;
            height: 44px;
            font-size: .8rem !important;
        }

        .sidebar-title {
            font-size: .9rem !important;
        }

        .sidebar-sub {
            font-size: .72rem !important;
        }

        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] a {
            font-size: .84rem !important;
        }
    }
    </style>
    <div class='footer'>Prepared for WFP Jijiga Area Office · RAM Unit · Dynamic Monitoring Planning and Checklist Compliance</div>
    """, unsafe_allow_html=True)


def sidebar_brand():
    with st.sidebar:
        st.markdown("""
        <div class='sidebar-logo'>
            <div class='sidebar-logo-mark'>WFP</div>
            <div>
                <div class='sidebar-title'>World Food Programme</div>
                <div class='sidebar-sub'>Jijiga Area Office · RAMTrack v3</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("What changed in v3?", expanded=False):
            st.write("Monthly assistance prioritization, TPM monitor assignment, dynamic 70/30 allocation, reassignment flags, and custom Somali Region map layer support.")
        with st.expander("Data protection note", expanded=False):
            st.warning("Use dummy/anonymized data for public deployments. Do not upload identifiable beneficiary data unless hosted in an approved environment.")

def header(title="WFP Jijiga Area Office | RAMTrack", subtitle="Dynamic Monthly Monitoring Planning, TPM Assignment, 70/30 Allocation and Checklist Compliance", export_bytes=None, export_name="RAMTrack_Export.xlsx"):
    left, right = st.columns([4, 2])
    with left:
        st.markdown(f"<div class='page-title'>{title}</div><div class='page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
    with right:
        c1, c2 = st.columns([1.1, 1])
        with c1:
            st.selectbox("Reporting Period", ["May 2025", "January 2026", "February 2026", "March 2026"], index=0)
        with c2:
            if export_bytes is not None:
                st.download_button("Export Workbook", data=export_bytes, file_name=export_name, use_container_width=True)

def metric_card(label, value, icon="•", accent="#005EB8"):
    st.markdown(f"""
    <div class='metric-tile'>
      <div class='metric-icon' style='background:{accent}1A;color:{accent}'>{icon}</div>
      <div><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>
    </div>
    """, unsafe_allow_html=True)

def render_planning_kpis(plan, rva=None):
    ready = planning_readiness(plan)
    required = int(rva["Required Count"].sum()) if rva is not None and not rva.empty and "Required Count" in rva else 0
    achieved = int(rva["Achieved"].sum()) if rva is not None and not rva.empty and "Achieved" in rva else 0
    completion = achieved / required if required else 0
    cols = st.columns(7)
    vals = [
        ("Prioritized FDPs", ready.get("Assistance-prioritized FDPs", 0), "🗓", "#005EB8"),
        ("WFP Planned", ready.get("WFP planned FDPs", 0), "W", "#0B63CE"),
        ("TPM Planned", ready.get("TPM planned FDPs", 0), "T", "#16B6A1"),
        ("TPM Share", f"{ready.get('TPM share', 0):.0%}", "70", "#16B6A1"),
        ("Reassignment Needed", ready.get("Reassignment required", 0), "↔", "#F39C12"),
        ("Required Checklists", f"{required:,}", "☑", "#6F42C1"),
        ("Completion", f"{completion:.0%}", "✓", "#28C76F"),
    ]
    for col, v in zip(cols, vals):
        with col:
            metric_card(*v)

def fig_allocation(plan):
    if plan.empty: return go.Figure()
    ent = "Final Entity" if "Final Entity" in plan.columns else "Planned Entity"
    s = plan.groupby(ent)["FDP_ID"].nunique().reset_index(name="FDPs/Sites")
    fig = px.bar(s, x=ent, y="FDPs/Sites", color=ent, text="FDPs/Sites", color_discrete_map={"WFP":"#0B63CE","TPM":"#16B6A1"})
    fig.update_traces(textposition="outside")
    fig.update_layout(height=300, title="WFP vs TPM Planned Allocation", xaxis_title="", yaxis_title="FDPs/Sites", showlegend=False, margin=dict(l=10,r=10,t=40,b=10))
    return fig

def fig_activity_alloc(plan):
    if plan.empty: return go.Figure()
    ent = "Final Entity" if "Final Entity" in plan.columns else "Planned Entity"
    s = plan.groupby(["Activity",ent])["FDP_ID"].nunique().reset_index(name="FDPs/Sites")
    fig = px.bar(s, x="Activity", y="FDPs/Sites", color=ent, barmode="stack", text="FDPs/Sites", color_discrete_map={"WFP":"#0B63CE","TPM":"#16B6A1"})
    fig.update_traces(textposition="inside")
    fig.update_layout(height=300, title="Allocation by Activity", xaxis_title="", margin=dict(l=10,r=10,t=40,b=10))
    return fig

def fig_req_achieved(rva):
    if rva.empty: return go.Figure()
    s = summarize_rva(rva, by=("Activity",))
    fig = px.bar(s, x="Activity", y=["Required","Achieved"], barmode="group", color_discrete_sequence=["#0B63CE","#28C76F"])
    fig.update_layout(height=300, title="Required vs Achieved Checklists by Activity", xaxis_title="", yaxis_title="Checklists", margin=dict(l=10,r=10,t=40,b=10))
    return fig

def fig_heatmap(rva):
    if rva.empty: return go.Figure()
    s = rva.groupby(["Activity","Checklist Type"])["Completion %"].mean().reset_index()
    fig = px.density_heatmap(s, x="Checklist Type", y="Activity", z="Completion %", text_auto=".0%", range_color=[0,1], color_continuous_scale=[(0,"#D64545"),(.5,"#F4C542"),(1,"#29B765")])
    fig.update_layout(height=330, title="Checklist Completion Heatmap by Activity and Checklist Type", xaxis_tickangle=-20, margin=dict(l=10,r=10,t=40,b=10))
    return fig

def fig_readiness(plan):
    if plan.empty: return go.Figure()
    s = plan.groupby(["Woreda","Reassignment Needed"])["FDP_ID"].nunique().reset_index(name="FDPs/Sites")
    fig = px.bar(s, x="Woreda", y="FDPs/Sites", color="Reassignment Needed", color_discrete_map={"Yes":"#F39C12","No":"#28C76F"}, title="Reassignment Need by Woreda")
    fig.update_layout(height=310, xaxis_tickangle=-35, margin=dict(l=10,r=10,t=40,b=10))
    return fig

def note(text):
    st.markdown(f"<div class='note-box'>{text}</div>", unsafe_allow_html=True)


def fig_gauge(title, coverage_value, wfp_share=0, tpm_share=0, planned=0, visited=0):
    """Semi-circle style gauge with WFP/TPM split annotation."""
    cov_pct = float(coverage_value or 0) * 100
    color = "#29B765" if cov_pct >= 80 else "#F4C542" if cov_pct >= 60 else "#D64545"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cov_pct,
        number={"suffix": "%", "font": {"size": 34, "color": "#0F172A"}},
        title={"text": f"<b>{title}</b><br><span style='font-size:0.78em;color:#64748B'>WFP {wfp_share:.0%} | TPM {tpm_share:.0%}<br>Visited {visited} / Planned {planned}</span>"},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8"},
            "bar": {"color": color},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "#E5E7EB",
            "steps": [
                {"range": [0, 60], "color": "#FDE2E2"},
                {"range": [60, 80], "color": "#FFF3CD"},
                {"range": [80, 100], "color": "#DDF7E8"},
            ],
            "threshold": {"line": {"color": "#0F172A", "width": 2}, "thickness": 0.75, "value": cov_pct},
        }
    ))
    fig.update_layout(height=270, margin=dict(l=16, r=16, t=55, b=10))
    return fig

def fig_coverage_planned_visited(summary_df):
    if summary_df is None or summary_df.empty:
        return go.Figure()
    fig = px.bar(
        summary_df,
        x="Activity",
        y=["Planned_Sites", "Visited_Sites"],
        barmode="group",
        color_discrete_sequence=["#94A3B8", "#0B63CE"],
    )
    fig.update_layout(height=330, title="Planned vs Visited by Activity", yaxis_title="FDPs/Sites", xaxis_title="", legend_title_text="")
    return fig

def fig_entity_contribution(site_coverage):
    if site_coverage is None or site_coverage.empty:
        return go.Figure()
    visited = site_coverage[site_coverage["Visited"].eq(1)].copy()
    if visited.empty:
        return go.Figure()
    data = visited.groupby(["Activity", "Entity"])["FDP_ID"].nunique().reset_index(name="Visited Sites")
    fig = px.bar(
        data,
        x="Activity",
        y="Visited Sites",
        color="Entity",
        barmode="stack",
        text="Visited Sites",
        color_discrete_map={"WFP": "#0B63CE", "TPM": "#16B6A1"},
        title="WFP vs TPM Contribution by Activity",
    )
    fig.update_traces(textposition="inside")
    fig.update_layout(height=330, yaxis_title="Visited FDPs/Sites", xaxis_title="", legend_title_text="")
    return fig

def fig_monthly_coverage_trend(site_coverage):
    if site_coverage is None or site_coverage.empty:
        return go.Figure()
    data = site_coverage.groupby(["Month", "Activity"]).agg(Planned=("Planned", "sum"), Visited=("Visited", "sum")).reset_index()
    data["Coverage %"] = data["Visited"] / data["Planned"].replace(0, pd.NA)
    fig = px.line(
        data,
        x="Month",
        y="Coverage %",
        color="Activity",
        markers=True,
        title="Monthly Coverage Trend by Activity",
    )
    fig.update_layout(height=330, yaxis_tickformat=".0%", yaxis_range=[0,1.05], xaxis_title="", yaxis_title="Coverage %")
    return fig

def fig_woreda_coverage_bar(site_coverage):
    if site_coverage is None or site_coverage.empty:
        return go.Figure()
    data = site_coverage.groupby("Woreda").agg(Planned=("Planned", "sum"), Visited=("Visited", "sum")).reset_index()
    data["Coverage %"] = data["Visited"] / data["Planned"].replace(0, pd.NA)
    data = data.sort_values("Coverage %", ascending=True).tail(20)
    fig = px.bar(
        data,
        x="Coverage %",
        y="Woreda",
        orientation="h",
        text=data["Coverage %"].map(lambda x: f"{x:.0%}"),
        color="Coverage %",
        color_continuous_scale=["#D64545", "#F4C542", "#29B765"],
        range_color=[0,1],
        title="Coverage by Woreda",
    )
    fig.update_layout(height=430, xaxis_tickformat=".0%", xaxis_range=[0,1.05], xaxis_title="Coverage %", yaxis_title="")
    return fig
