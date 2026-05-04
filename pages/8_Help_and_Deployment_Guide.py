import streamlit as st
from utils.app_state import init_state, export_workbook
from utils.ui import inject_css, sidebar_brand, header, note

st.set_page_config(page_title="RAMTrack v3 | Help Guide", page_icon="📘", layout="wide")
inject_css(); sidebar_brand(); init_state()
header(subtitle="Help and deployment guide for RAMTrack v3", export_bytes=export_workbook(), export_name="RAMTrack_v3_Workbook.xlsx")

st.markdown("""
## What RAMTrack v3 does

RAMTrack v3 is a dynamic monthly monitoring planning and checklist compliance app for WFP Jijiga Area Office RAM work. It supports:

1. Monthly assistance prioritization for needs- and vulnerability-based relief planning.
2. JarCo TPM field monitor assignment and reassignment tracking.
3. Dynamic WFP–TPM 70/30 planning logic that respects operational constraints.
4. Checklist requirement generation based on activity standards.
5. Requirement versus achieved comparison using MoDA submissions.
6. Somali Region custom boundary layer upload with point mapping and popup details.
7. Export of all planning and compliance outputs to Excel.

## Recommended monthly workflow

1. Update the FDP master list.
2. Update the monthly assistance prioritization plan.
3. Update the TPM assignment matrix based on JarCo availability.
4. Generate the dynamic monitoring plan.
5. Review reassignment flags and discuss with TPM.
6. Apply manual overrides where agreed.
7. Export the monitoring plan and checklist requirement package.
8. Upload MoDA submissions during or after the cycle.
9. Review checklist gaps and map visited/non-visited sites.
10. Use the gap tracker in RAM/Programme/TPM follow-up meetings.

## GitHub + Streamlit deployment

Your repository should contain:

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

In Streamlit Cloud, set the main file as:

```text
streamlit_app.py
```

## Data protection

Do not upload real beneficiary names, phone numbers, household IDs, token numbers or sensitive free-text comments to a public deployment. Use dummy or anonymized data unless the app is hosted in an approved secure environment.
""")