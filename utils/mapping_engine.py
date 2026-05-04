import pandas as pd
import folium

STATUS_COLORS = {
    "Complete": "green",
    "Partial": "orange",
    "Moderate Gap": "orange",
    "Critical Gap": "red",
    "Not Visited / Not Submitted": "red",
}

def site_status_from_rva(rva: pd.DataFrame) -> pd.DataFrame:
    if rva.empty:
        return pd.DataFrame()
    s = rva.groupby(["Month","Activity","Entity","Woreda","FDP_ID","FDP/Site Name","Latitude","Longitude"], dropna=False).agg(
        Required=("Required Count","sum"),
        Achieved=("Achieved","sum"),
        Gap=("Gap","sum")
    ).reset_index()
    s["Completion %"] = (s["Achieved"] / s["Required"]).where(s["Required"] > 0, 0).clip(upper=1)
    def status(p):
        if p >= 1: return "Complete"
        if p >= .75: return "Partial"
        if p >= .50: return "Moderate Gap"
        if p > 0: return "Critical Gap"
        return "Not Visited / Not Submitted"
    s["Status"] = s["Completion %"].apply(status)
    return s

def build_map(rva: pd.DataFrame, boundary_geojson=None, center=(7.5, 43.0), zoom_start=6):
    site = site_status_from_rva(rva)
    if not site.empty and site[["Latitude","Longitude"]].notna().all(axis=1).any():
        center = [site["Latitude"].mean(), site["Longitude"].mean()]
    m = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap", control_scale=True)
    if boundary_geojson:
        folium.GeoJson(
            boundary_geojson,
            name="Somali Region / Woreda boundary layer",
            style_function=lambda x: {"fillColor":"#0072CE", "color":"#005EB8", "weight":1.2, "fillOpacity":0.05},
            tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Boundary:"]) if boundary_geojson.get("features") else None
        ).add_to(m)
    for _, r in site.iterrows():
        if pd.isna(r["Latitude"]) or pd.isna(r["Longitude"]):
            continue
        color = STATUS_COLORS.get(r["Status"], "blue")
        html = f"""
        <b>{r['FDP/Site Name']}</b><br>
        Activity: {r['Activity']}<br>
        Woreda: {r['Woreda']}<br>
        Entity: {r['Entity']}<br>
        Required: {int(r['Required'])}<br>
        Achieved: {int(r['Achieved'])}<br>
        Completion: {r['Completion %']:.0%}<br>
        Status: {r['Status']}
        """
        folium.CircleMarker(
            location=[r["Latitude"], r["Longitude"]],
            radius=6,
            popup=folium.Popup(html, max_width=320),
            tooltip=f"{r['FDP/Site Name']} | {r['Status']}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=.8
        ).add_to(m)
    folium.LayerControl().add_to(m)
    return m