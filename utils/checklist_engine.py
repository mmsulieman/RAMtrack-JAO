import numpy as np
import pandas as pd

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out

def generate_checklist_requirements(plan: pd.DataFrame, requirement_matrix: pd.DataFrame) -> pd.DataFrame:
    plan = normalize(plan)
    req = normalize(requirement_matrix)
    rows = []
    if plan.empty:
        return pd.DataFrame(columns=["Month","Activity","Entity","Woreda","FDP_ID","FDP/Site Name","Checklist Type","Required Count"])
    entity_col = "Final Entity" if "Final Entity" in plan.columns else "Planned Entity"
    for _, site in plan.iterrows():
        reqs = req[req["Activity"].eq(site["Activity"])]
        for _, r in reqs.iterrows():
            rows.append({
                "Month": site["Month"],
                "Activity": site["Activity"],
                "Modality": site.get("Modality",""),
                "Entity": site[entity_col],
                "Woreda": site["Woreda"],
                "FDP_ID": site.get("FDP_ID",""),
                "FDP/Site Name": site["FDP/Site Name"],
                "Checklist Type": r["Checklist Type"],
                "Required Count": int(r["Requirement per FDP/Site"]),
                "Latitude": site.get("Latitude", None),
                "Longitude": site.get("Longitude", None),
                "GPS": site.get("GPS","")
            })
    return pd.DataFrame(rows)

def compare_required_vs_achieved(requirements: pd.DataFrame, submissions: pd.DataFrame) -> pd.DataFrame:
    req = normalize(requirements)
    sub = normalize(submissions)
    if req.empty:
        return pd.DataFrame()
    group_cols = ["Month","Activity","Entity","Woreda","FDP_ID","FDP/Site Name","Checklist Type"]
    for c in group_cols:
        if c not in sub.columns:
            sub[c] = ""
    achieved = sub.groupby(group_cols, dropna=False).size().reset_index(name="Achieved")
    out = req.merge(achieved, on=group_cols, how="left")
    out["Achieved"] = out["Achieved"].fillna(0).astype(int)
    out["Gap"] = out["Required Count"] - out["Achieved"]
    out["Completion %"] = np.where(out["Required Count"] > 0, out["Achieved"] / out["Required Count"], 0).clip(max=1)
    def status(p):
        if p >= 1: return "Complete"
        if p >= .75: return "Partial"
        if p >= .50: return "Moderate Gap"
        if p > 0: return "Critical Gap"
        return "Not Visited / Not Submitted"
    out["Status"] = out["Completion %"].apply(status)
    out["Visited Status"] = np.where(out["Achieved"] > 0, "Visited", "Not Visited")
    return out

def summarize_rva(rva: pd.DataFrame, by=("Month","Activity","Entity")) -> pd.DataFrame:
    if rva.empty:
        return pd.DataFrame()
    out = rva.groupby(list(by), dropna=False).agg(
        Required=("Required Count","sum"),
        Achieved=("Achieved","sum"),
        Gap=("Gap","sum"),
        Planned_Sites=("FDP_ID","nunique")
    ).reset_index()
    out["Completion %"] = np.where(out["Required"] > 0, out["Achieved"] / out["Required"], 0).clip(max=1)
    return out

def generate_dummy_moda_submissions(requirements: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    import random
    random.seed(seed)
    rows = []
    for _, r in requirements.iterrows():
        required = int(r["Required Count"])
        base_rate = random.uniform(0.55, 1.05)
        if "Partner" in str(r["Checklist Type"]): base_rate -= 0.20
        if "Warehouse" in str(r["Checklist Type"]): base_rate -= 0.10
        if r["Entity"] == "TPM": base_rate += 0.05
        achieved = max(0, min(required, round(required * base_rate)))
        for _ in range(achieved):
            rows.append({
                "Submission ID": f"SUB-{len(rows)+1:05d}",
                "Submission Date": "2025-05-" + str(random.randint(5, 28)).zfill(2),
                "Month": r["Month"],
                "Activity": r["Activity"],
                "Modality": r.get("Modality",""),
                "Checklist Type": r["Checklist Type"],
                "Entity": r["Entity"],
                "Monitor Name": f"{r['Entity']} Monitor {random.randint(1, 8)}",
                "Woreda": r["Woreda"],
                "FDP_ID": r.get("FDP_ID",""),
                "FDP/Site Name": r["FDP/Site Name"],
                "Latitude": r.get("Latitude", None),
                "Longitude": r.get("Longitude", None),
                "GPS": r.get("GPS",""),
                "Duration Minutes": random.randint(8, 65),
                "Valid Submission": "Yes"
            })
    return pd.DataFrame(rows)