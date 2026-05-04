
import numpy as np
import pandas as pd

def _safe_pct(num, den):
    return num / den if den else 0

def build_site_coverage_table(plan: pd.DataFrame, rva: pd.DataFrame) -> pd.DataFrame:
    """Build one row per planned FDP/site with visit coverage and checklist completion status."""
    if plan is None or plan.empty:
        return pd.DataFrame()

    p = plan.copy()
    p.columns = [str(c).strip() for c in p.columns]
    entity_col = "Final Entity" if "Final Entity" in p.columns else "Planned Entity"
    if "Entity" not in p.columns:
        p["Entity"] = p[entity_col]

    base_cols = [
        "Month", "Activity", "Modality", "Sub-office", "Zone", "Woreda", "FDP_ID",
        "FDP/Site Name", "Entity", "Partner", "Monthly Priority Level",
        "Priority Reason", "TPM Assigned to Woreda", "TPM Available This Month",
        "Reassignment Needed", "Allocation Reason", "70/30 Exception Reason",
        "Latitude", "Longitude", "GPS"
    ]
    for c in base_cols:
        if c not in p.columns:
            p[c] = ""

    site = p[base_cols].drop_duplicates(subset=["Month", "Activity", "Entity", "Woreda", "FDP_ID", "FDP/Site Name"]).copy()

    if rva is None or rva.empty:
        site["Required"] = 0
        site["Achieved"] = 0
    else:
        r = rva.copy()
        r.columns = [str(c).strip() for c in r.columns]
        group_cols = ["Month", "Activity", "Entity", "Woreda", "FDP_ID", "FDP/Site Name"]
        req_col = "Required Count" if "Required Count" in r.columns else "Required"
        agg = (
            r.groupby(group_cols, dropna=False)
            .agg(Required=(req_col, "sum"), Achieved=("Achieved", "sum"))
            .reset_index()
        )
        site = site.merge(agg, on=group_cols, how="left")
        site["Required"] = site["Required"].fillna(0).astype(int)
        site["Achieved"] = site["Achieved"].fillna(0).astype(int)

    site["Planned"] = 1
    site["Visited"] = np.where(site["Achieved"] > 0, 1, 0)
    site["Coverage %"] = site["Visited"] / site["Planned"]
    site["Checklist Completion %"] = np.where(site["Required"] > 0, site["Achieved"] / site["Required"], 0).clip(max=1)
    site["Visited Status"] = np.where(site["Visited"] == 1, "Visited", "Not Visited")

    def checklist_status(row):
        if row["Visited"] == 0:
            return "Not Visited"
        if row["Checklist Completion %"] >= 1:
            return "Visited - Complete"
        if row["Checklist Completion %"] >= .75:
            return "Visited - Partial"
        return "Visited - Incomplete"

    site["Checklist Status"] = site.apply(checklist_status, axis=1)
    site["Coverage Status"] = np.select(
        [
            site["Checklist Status"].eq("Visited - Complete"),
            site["Checklist Status"].isin(["Visited - Partial", "Visited - Incomplete"]),
            site["Visited Status"].eq("Not Visited")
        ],
        ["Visited and complete", "Visited but checklist incomplete", "Planned but not visited"],
        default="Unknown"
    )
    return site

def summarize_coverage(site_coverage: pd.DataFrame, by=None) -> pd.DataFrame:
    if site_coverage is None or site_coverage.empty:
        return pd.DataFrame()
    if by is None:
        by = []
    g = site_coverage.groupby(by, dropna=False) if by else [((), site_coverage)]
    rows = []
    if by:
        out = site_coverage.groupby(by, dropna=False).agg(
            Planned_Sites=("Planned", "sum"),
            Visited_Sites=("Visited", "sum"),
            Required_Checklists=("Required", "sum"),
            Achieved_Checklists=("Achieved", "sum"),
            High_Priority_Unvisited=("Monthly Priority Level", lambda s: 0),
        ).reset_index()
        # high priority unvisited is easier calculated separately
        hp = (
            site_coverage[
                site_coverage["Monthly Priority Level"].astype(str).str.lower().isin(["high", "critical", "priority"]) &
                site_coverage["Visited"].eq(0)
            ]
            .groupby(by, dropna=False)
            .size()
            .reset_index(name="High_Priority_Unvisited")
        )
        out = out.drop(columns=["High_Priority_Unvisited"], errors="ignore").merge(hp, on=by, how="left")
        out["High_Priority_Unvisited"] = out["High_Priority_Unvisited"].fillna(0).astype(int)
    else:
        out = pd.DataFrame([{
            "Planned_Sites": site_coverage["Planned"].sum(),
            "Visited_Sites": site_coverage["Visited"].sum(),
            "Required_Checklists": site_coverage["Required"].sum(),
            "Achieved_Checklists": site_coverage["Achieved"].sum(),
            "High_Priority_Unvisited": int((
                site_coverage["Monthly Priority Level"].astype(str).str.lower().isin(["high", "critical", "priority"]) &
                site_coverage["Visited"].eq(0)
            ).sum())
        }])
    out["Coverage %"] = np.where(out["Planned_Sites"] > 0, out["Visited_Sites"] / out["Planned_Sites"], 0)
    out["Checklist Completion %"] = np.where(out["Required_Checklists"] > 0, out["Achieved_Checklists"] / out["Required_Checklists"], 0).clip(max=1)
    return out

def entity_split(site_coverage: pd.DataFrame) -> pd.DataFrame:
    if site_coverage is None or site_coverage.empty:
        return pd.DataFrame(columns=["Entity", "Visited_Sites", "Share %"])
    visited = site_coverage[site_coverage["Visited"].eq(1)]
    out = visited.groupby("Entity")["FDP_ID"].nunique().reset_index(name="Visited_Sites")
    total = out["Visited_Sites"].sum()
    out["Share %"] = np.where(total > 0, out["Visited_Sites"] / total, 0)
    return out

def coverage_metrics(site_coverage: pd.DataFrame, target_wfp=.30, target_tpm=.70) -> dict:
    if site_coverage is None or site_coverage.empty:
        return {
            "planned": 0, "visited": 0, "coverage": 0, "wfp_visited": 0, "tpm_visited": 0,
            "wfp_share": 0, "tpm_share": 0, "priority_unvisited": 0, "wfp_deviation": 0, "tpm_deviation": 0
        }
    planned = int(site_coverage["Planned"].sum())
    visited = int(site_coverage["Visited"].sum())
    coverage = _safe_pct(visited, planned)
    visited_df = site_coverage[site_coverage["Visited"].eq(1)]
    wfp_visited = int(visited_df[visited_df["Entity"].eq("WFP")]["FDP_ID"].nunique())
    tpm_visited = int(visited_df[visited_df["Entity"].eq("TPM")]["FDP_ID"].nunique())
    wfp_share = _safe_pct(wfp_visited, wfp_visited + tpm_visited)
    tpm_share = _safe_pct(tpm_visited, wfp_visited + tpm_visited)
    priority_unvisited = int((
        site_coverage["Monthly Priority Level"].astype(str).str.lower().isin(["high", "critical", "priority"]) &
        site_coverage["Visited"].eq(0)
    ).sum())
    return {
        "planned": planned,
        "visited": visited,
        "coverage": coverage,
        "wfp_visited": wfp_visited,
        "tpm_visited": tpm_visited,
        "wfp_share": wfp_share,
        "tpm_share": tpm_share,
        "priority_unvisited": priority_unvisited,
        "wfp_deviation": wfp_share - target_wfp,
        "tpm_deviation": tpm_share - target_tpm,
    }

def auto_insights(site_coverage: pd.DataFrame) -> list[str]:
    m = coverage_metrics(site_coverage)
    if m["planned"] == 0:
        return ["No planned FDPs/sites are available for the selected filters."]
    insights = []
    insights.append(f"Overall monitoring visit coverage is {m['coverage']:.0%}: {m['visited']} of {m['planned']} planned FDPs/sites have at least one recorded checklist submission.")
    insights.append(f"Among visited sites, WFP covered {m['wfp_share']:.0%} and TPM covered {m['tpm_share']:.0%}; this shows the operational split after assistance priority and TPM availability constraints.")
    if m["priority_unvisited"] > 0:
        insights.append(f"{m['priority_unvisited']} high-priority planned site(s) remain unvisited and should be prioritized in the next field deployment follow-up.")
    else:
        insights.append("All high-priority planned sites in the current filter have at least one recorded monitoring submission.")
    no_tpm = int((site_coverage["TPM Assigned to Woreda"].astype(str).str.lower().eq("no") & site_coverage["Visited"].eq(0)).sum())
    if no_tpm > 0:
        insights.append(f"{no_tpm} planned site(s) are in woredas without a standing TPM assignment; these may require WFP coverage or JarCo reassignment.")
    reassign = int(site_coverage["Reassignment Needed"].astype(str).str.lower().eq("yes").sum()) if "Reassignment Needed" in site_coverage else 0
    if reassign > 0:
        insights.append(f"TPM reassignment is flagged for {reassign} planned site(s), indicating where early coordination with JarCo is needed.")
    return insights
