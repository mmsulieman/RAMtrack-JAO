# RAMTrack v3: Dynamic Monthly Monitoring Planning App

Prepared for **WFP Jijiga Area Office – RAM Unit**.

RAMTrack v3 is a deployable Streamlit app for dynamic WFP–TPM monitoring planning, checklist requirement generation and MoDA submission gap tracking.

## What is new in v3

- Monthly assistance prioritization for needs- and vulnerability-based relief planning.
- JarCo TPM field monitor assignment matrix by woreda.
- Dynamic 70/30 planning logic that respects operational constraints.
- Automatic TPM reassignment-needed flags.
- Allocation reason and 70/30 exception reason fields.
- Activity-based checklist requirement generation.
- Requirement vs achieved tracking using MoDA-style submissions.
- Custom Somali Region boundary GeoJSON upload.
- Visited / non-visited / incomplete site map with popup details.

## Repository structure

```text
streamlit_app.py
requirements.txt
pages/
utils/
sample_data/
geodata/
.streamlit/config.toml
README.md
Dockerfile
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy on Streamlit Cloud

1. Upload all files/folders in this package to GitHub.
2. In Streamlit Community Cloud, select the repository and branch.
3. Set the main file path to:

```text
streamlit_app.py
```

4. Deploy.

## Core data inputs

### FDP master list

Required columns:

- FDP_ID
- Activity
- Modality
- Sub-office
- Zone
- Woreda
- FDP/Site Name
- Partner
- Active Status
- Priority Level
- Latitude
- Longitude

### Monthly assistance plan

This controls which FDPs/sites are planned for assistance in the selected month. Relief monitoring should be generated only for active monthly assistance-prioritized sites.

### TPM assignment matrix

This captures JarCo monitor assignment, availability and reassignment possibility by woreda.

### Checklist requirement matrix

Default standards included:

- Activity 1 Relief: 15 forms per FDP.
- Activity 2 Nutrition: 8 forms per TSFP site.
- Activity 3 Refugee Operations: 15 forms per site.

## Mapping

The package includes a sample/demo GeoJSON layer only. Replace it with the official Somali Region region/zone/woreda boundary GeoJSON when available.

## Data protection

Use dummy or anonymized data in public deployments. Do not upload real beneficiary identifiers, phone numbers, household IDs, token numbers or sensitive comments unless hosted in an approved secure environment.



## New in v3.1: Monitoring Visit Coverage Dashboard

A new page `4_Monitoring_Coverage_Dashboard.py` has been added. It provides:

- Overall monitoring visit coverage gauge
- Activity-specific gauges for Activity 1 Relief, Activity 2 Nutrition and Activity 3 Refugee Operations
- WFP/TPM split percentage inside each gauge
- Filters by month, activity, entity, sub-office, zone, woreda, priority level and visited/checklist status
- Planned vs visited by activity
- WFP vs TPM contribution by activity
- Monthly coverage trend
- Woreda coverage bar chart
- Auto-generated management insights
- Operational follow-up table for unvisited and incomplete checklist sites

Visit coverage is calculated as:

`Unique visited planned FDPs/sites ÷ unique planned FDPs/sites`

WFP/TPM split is calculated among visited sites only.
