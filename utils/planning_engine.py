import numpy as np
import pandas as pd

REQUIRED_FDP_COLUMNS = ["FDP_ID","Activity","Modality","Sub-office","Zone","Woreda","FDP/Site Name","Partner","Active Status","Priority Level","Latitude","Longitude"]

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out

def validate_columns(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c not in df.columns]

def yes(x) -> bool:
    return str(x).strip().lower() in ["yes","y","true","1","available"]

def prepare_monthly_sites(fdp_master, assistance_plan, month, activity="All Activities"):
    fdp = normalize(fdp_master)
    assist = normalize(assistance_plan)
    missing = validate_columns(fdp, REQUIRED_FDP_COLUMNS)
    if missing:
        raise ValueError(f"FDP master is missing required columns: {missing}")
    fdp = fdp[fdp["Active Status"].astype(str).str.lower().eq("active")].copy()
    if activity != "All Activities":
        fdp = fdp[fdp["Activity"].eq(activity)].copy()
    if assist.empty:
        fdp["Month"] = month
        fdp["Assistance Planned"] = "Yes"
        fdp["Monthly Priority Level"] = fdp["Priority Level"]
        fdp["Priority Reason"] = "No assistance plan uploaded; active site included"
        fdp["Distribution Window"] = ""
        return fdp
    assist = assist[assist["Month"].eq(month)].copy()
    if activity != "All Activities":
        assist = assist[assist["Activity"].eq(activity)].copy()
    cols = ["Month","FDP_ID","Assistance Planned","Monthly Priority Level","Priority Reason","Distribution Window"]
    merged = fdp.merge(assist[[c for c in cols if c in assist.columns]], on="FDP_ID", how="left")
    merged["Month"] = merged["Month"].fillna(month)
    merged["Assistance Planned"] = merged["Assistance Planned"].fillna("No")
    merged["Monthly Priority Level"] = merged["Monthly Priority Level"].fillna(merged["Priority Level"])
    merged["Priority Reason"] = merged["Priority Reason"].fillna("Not listed in monthly assistance plan")
    merged["Distribution Window"] = merged["Distribution Window"].fillna("")
    return merged[merged["Assistance Planned"].astype(str).str.lower().eq("yes")].copy()

def generate_dynamic_monitoring_plan(
    fdp_master: pd.DataFrame,
    assistance_plan: pd.DataFrame,
    tpm_assignment: pd.DataFrame,
    month: str,
    activity: str = "All Activities",
    tpm_target: float = 0.70,
    large_threshold: int = 35,
    split_large_woredas: bool = True,
    priority_to_wfp: bool = True,
) -> pd.DataFrame:
    sites = prepare_monthly_sites(fdp_master, assistance_plan, month, activity)
    if sites.empty:
        return pd.DataFrame()
    tpm = normalize(tpm_assignment)
    if tpm.empty:
        for c in ["TPM Assigned to Woreda","TPM Field Monitor","TPM Available This Month","Reassignment Possible"]:
            sites[c] = "No" if c != "TPM Field Monitor" else ""
    else:
        key_cols = ["Month","Woreda"]
        tpm_month = tpm[tpm["Month"].eq(month)].copy() if "Month" in tpm.columns else tpm.copy()
        merge_cols = ["Month","Woreda","TPM Company","TPM Field Monitor","TPM Assigned to Woreda","TPM Available This Month","Reassignment Possible"]
        sites = sites.merge(tpm_month[[c for c in merge_cols if c in tpm_month.columns]], on=key_cols, how="left")
        for c in ["TPM Assigned to Woreda","TPM Available This Month","Reassignment Possible"]:
            sites[c] = sites[c].fillna("No")
        sites["TPM Field Monitor"] = sites.get("TPM Field Monitor", "").fillna("")
        sites["TPM Company"] = sites.get("TPM Company", "").fillna("")
    sites["FDP Count in Woreda"] = sites.groupby(["Activity","Woreda"])["FDP_ID"].transform("count")
    sites["Assignment Type"] = np.where(sites["FDP Count in Woreda"] > large_threshold, "Split large woreda", "Full woreda")
    sites["Planned Entity"] = ""
    sites["Allocation Reason"] = ""
    sites["Reassignment Needed"] = "No"
    sites["Reassignment Status"] = ""
    sites["70/30 Exception Reason"] = ""
    # First pass based on constraints.
    for idx, r in sites.iterrows():
        high_priority = str(r["Monthly Priority Level"]).lower() in ["high","critical","management priority"]
        tpm_available = yes(r.get("TPM Assigned to Woreda","No")) and yes(r.get("TPM Available This Month","No"))
        can_reassign = yes(r.get("Reassignment Possible","No"))
        if priority_to_wfp and high_priority:
            sites.at[idx,"Planned Entity"] = "WFP"
            sites.at[idx,"Allocation Reason"] = "High-priority/management assurance site assigned to WFP"
        elif tpm_available:
            sites.at[idx,"Planned Entity"] = "TPM"
            sites.at[idx,"Allocation Reason"] = "TPM monitor assigned and available"
        elif can_reassign:
            sites.at[idx,"Planned Entity"] = "WFP"
            sites.at[idx,"Allocation Reason"] = "No assigned TPM; WFP assigned pending JarCo reassignment"
            sites.at[idx,"Reassignment Needed"] = "Yes"
            sites.at[idx,"Reassignment Status"] = "Pending JarCo confirmation"
        else:
            sites.at[idx,"Planned Entity"] = "WFP"
            sites.at[idx,"Allocation Reason"] = "No TPM assigned/available"
    # Split large woredas where TPM available.
    if split_large_woredas:
        for (act, woreda), group in sites.groupby(["Activity","Woreda"]):
            if len(group) <= large_threshold:
                continue
            tpm_available = group["TPM Assigned to Woreda"].apply(yes).any() and group["TPM Available This Month"].apply(yes).any()
            if not tpm_available:
                continue
            eligible = group[~group["Monthly Priority Level"].astype(str).str.lower().isin(["high","critical","management priority"])].sort_values("FDP_ID")
            # aim roughly half WFP/TPM in this large woreda
            half = len(group) // 2
            current_wfp = (sites.loc[group.index,"Planned Entity"] == "WFP").sum()
            need_wfp = max(0, half - current_wfp)
            if need_wfp > 0:
                move_idx = eligible[eligible.index.isin(sites.loc[group.index][sites.loc[group.index,"Planned Entity"].eq("TPM")].index)].head(need_wfp).index
                sites.loc[move_idx,"Planned Entity"] = "WFP"
                sites.loc[move_idx,"Allocation Reason"] = "Large woreda split between WFP and TPM"
    # Rebalance only for unconstrained TPM-available non-high-priority sites.
    total = len(sites)
    tpm_target_n = round(total * tpm_target)
    current_tpm = int((sites["Planned Entity"] == "TPM").sum())
    if current_tpm < tpm_target_n:
        candidates = sites[
            (sites["Planned Entity"].eq("WFP")) &
            (sites["TPM Assigned to Woreda"].apply(yes)) &
            (sites["TPM Available This Month"].apply(yes)) &
            (~sites["Monthly Priority Level"].astype(str).str.lower().isin(["high","critical","management priority"]))
        ].sort_values(["Activity","Woreda","FDP_ID"])
        need = tpm_target_n - current_tpm
        move = candidates.head(need).index
        sites.loc[move,"Planned Entity"] = "TPM"
        sites.loc[move,"Allocation Reason"] = "Rebalanced toward 70/30 where TPM is available"
    elif current_tpm > tpm_target_n:
        candidates = sites[
            (sites["Planned Entity"].eq("TPM")) &
            (~sites["Monthly Priority Level"].astype(str).str.lower().isin(["high","critical","management priority"]))
        ].sort_values(["Activity","Woreda","FDP_ID"])
        move = candidates.head(current_tpm - tpm_target_n).index
        sites.loc[move,"Planned Entity"] = "WFP"
        sites.loc[move,"Allocation Reason"] = "Rebalanced toward 70/30"
    final_tpm = int((sites["Planned Entity"] == "TPM").sum())
    tpm_share = final_tpm / total if total else 0
    deviation = abs(tpm_share - tpm_target)
    exception_reason = "" if deviation <= 0.10 else "70/30 deviates due to monthly assistance priorities, TPM coverage gaps, or WFP priority assurance"
    sites["70/30 Exception Reason"] = exception_reason
    sites["Final Entity"] = sites["Planned Entity"]
    sites["Manual Override Entity"] = ""
    sites["Override Reason"] = ""
    sites["GPS"] = sites["Latitude"].round(6).astype(str) + ", " + sites["Longitude"].round(6).astype(str)
    out_cols = [
        "Month","Activity","Modality","Sub-office","Zone","Woreda","FDP_ID","FDP/Site Name","Partner",
        "Assistance Planned","Monthly Priority Level","Priority Reason","Distribution Window",
        "TPM Assigned to Woreda","TPM Field Monitor","TPM Available This Month","Reassignment Possible",
        "Reassignment Needed","Reassignment Status","Planned Entity","Allocation Reason","Assignment Type",
        "70/30 Exception Reason","Manual Override Entity","Override Reason","Final Entity",
        "Latitude","Longitude","GPS"
    ]
    return sites[out_cols].sort_values(["Activity","Woreda","FDP/Site Name"]).reset_index(drop=True)

def planning_readiness(plan: pd.DataFrame, tpm_target=.70) -> dict:
    if plan.empty:
        return {}
    total = len(plan)
    tpm = int((plan["Final Entity"]=="TPM").sum()) if "Final Entity" in plan else int((plan["Planned Entity"]=="TPM").sum())
    wfp = total - tpm
    return {
        "Assistance-prioritized FDPs": total,
        "TPM planned FDPs": tpm,
        "WFP planned FDPs": wfp,
        "TPM share": tpm/total if total else 0,
        "WFP share": wfp/total if total else 0,
        "70/30 deviation": abs((tpm/total if total else 0) - tpm_target),
        "Reassignment required": int((plan["Reassignment Needed"]=="Yes").sum()) if "Reassignment Needed" in plan else 0,
        "High-priority FDPs": int(plan["Monthly Priority Level"].astype(str).str.lower().isin(["high","critical","management priority"]).sum()) if "Monthly Priority Level" in plan else 0,
        "Missing coordinates": int(plan[["Latitude","Longitude"]].isna().any(axis=1).sum()) if set(["Latitude","Longitude"]).issubset(plan.columns) else 0,
    }