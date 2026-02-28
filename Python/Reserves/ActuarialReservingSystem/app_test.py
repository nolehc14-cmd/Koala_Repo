import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Actuarial Reserving System - Main Screen", layout="wide")

# streamlit run app_test.py

# -----------------------------
# Helpers
# -----------------------------
PROGRAM_COLS = [
    "id",
    "Cedant",
    "Program#",
    "Program Desc",
    "Facility",
    "LOB",
    "Company",
    "UW",
    "Type",
    "Currency",
    "FX",
    "Exposed",
    "Rep_FGU",
    "Rep_UNL",
    "Selected UNL",
    "Layer Loss",
    "Arch Loss",
    "Arch USD Gross",
    "Arch USD Ceded to US",
    "Arch USD Net",
    "Arch USD NetRP",
    "Arch USD Net of RP",
    "Booked Prior Gross",
    "Booked Prior Net of RP",
    "Change Gross",
    "Change Net of RP",
]

LAYER_COLUMNS = ["Layer 1","Layer 2","Layer 3","Layer 4","Layer 5","Layer 6","Layer 7","Layer 8","Inuring 1","Inuring 2","Inuring 3","Total"]
LAYER_METRICS = [
    "Description",
    "UY",
    "Currency",
    "Placed",
    "Reinst",
    "Contract Limit",
    "Occ Limit",
    "Attachment",
    "Share %",
    "Share - Occ Limit",
    "ROL",
    "Reported UNL",
    "Selected UNL",
    "100% Layer Loss",
    "Share Layer Loss",
    "Share Limit remaining",
    "Net Layer Loss",
    "Reinst Prem",
    "Net Reinst Prem",
    "Net of RIP Layer Loss",
]

def _make_programs_df():
    # Sample data roughly shaped like your grid
    data = [
        [1, "American Family Insurance G", "417540", "", "9PC", "1PC", "101", "JLeg", "XS", "USD", 1.0, 1.0, 0, 0, 24261, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, "St Johns Insurance", "420850", "", "9PC", "1PC", "101", "JLeg", "XS", "USD", 1.0, 1.0, 135936, 195000, 234000, 100000, 4000, 4000, 1903, 2097, 0, 2097, 4000, 4000, 0, -1903],
        [3, "Southern Oak Insurance", "421660", "", "9PC", "1PC", "101", "MMel", "XS", "USD", 1.0, 1.0, 29930, 33400, 39270, 34270, 1714, 1714, 815, 899, 256, 642, 1710, 1251, -4, -603],
        [4, "Liberty Mutual Insurance", "422580", "", "9PC", "1PC", "101", "MMel", "XS", "USD", 1.0, 1.0, 0, 0, 92679, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [5, "Travelers", "422830", "", "9PP", "2CO", "101", "JLeg", "QS", "USD", 1.0, 1.0, 5537, 5537, 24000, 24000, 1560, 1560, 125, 1435, 0, 1435, 1560, 1560, 0, -125],
        [6, "Olympus Insurance Co", "424920", "", "9PC", "1PC", "101", "MMel", "XS", "USD", 1.0, 1.0, 73844, 71454, 138000, 47111, 8467, 8467, 4028, 4439, 0, 4439, 8490, 8490, 23, -4051],
        [7, "Universal Property Casualty", "425680", "", "9PC", "1PC", "101", "MMel", "XS", "USD", 1.0, 1.0, 78719, 350000, 375000, 364000, 6010, 6010, 2859, 3151, 871, 2279, 6015, 4331, 5, -2072],
        [8, "USAA Group", "425850", "", "9SL", "1SL", "101", "JLeg", "XS", "USD", 1.0, 1.0, 1038300, 2390000, 4399000, 291933, 854, 854, 218, 636, 0, 636, 854, 854, 0, -218],
    ]
    df = pd.DataFrame(data, columns=PROGRAM_COLS)
    return df

def _make_default_layer_matrix(accident_year: int, currency: str, selected_unl: float):
    # A simple, editable layer matrix placeholder, not actuarial logic yet
    mat = pd.DataFrame({"Metric": LAYER_METRICS})
    for col in LAYER_COLUMNS:
        mat[col] = 0.0

    # Fill a few obvious rows for usability
    mat.loc[mat["Metric"] == "UY", LAYER_COLUMNS] = accident_year
    mat.loc[mat["Metric"] == "Currency", LAYER_COLUMNS] = currency
    mat.loc[mat["Metric"] == "Selected UNL", "Layer 1"] = float(selected_unl)
    mat.loc[mat["Metric"] == "Reported UNL", "Layer 1"] = float(selected_unl)  # placeholder
    mat.loc[mat["Metric"] == "Description", "Layer 1"] = "Default Layer Setup"
    return mat

def _compute_totals(layer_df: pd.DataFrame) -> pd.DataFrame:
    df = layer_df.copy()

    # Ensure Total exists
    if "Total" not in df.columns:
        df["Total"] = np.nan

    numeric_cols = [c for c in LAYER_COLUMNS if c != "Total"]

    # Force numeric dtype for all numeric columns (including Total)
    for c in numeric_cols + ["Total"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Compute totals row-by-row
    df["Total"] = df[numeric_cols].fillna(0).sum(axis=1)

    # Optional: keep Total blank for rows that are conceptually non-numeric
    non_numeric_metrics = {"Description", "Currency"}
    df.loc[df["Metric"].isin(non_numeric_metrics), "Total"] = np.nan

    return df

def _lawf_series_from_program_row(row: pd.Series):
    # Placeholder LAWF series driven by Selected UNL / Arch Loss
    base = float(row.get("Selected UNL", 0) or 0)
    arch = float(row.get("Arch Loss", 0) or 0)
    # Create a smooth-ish decline curve; purely illustrative
    dev = np.arange(1, 13)
    y = (base * 0.12) * np.exp(-0.18 * (dev - 1)) + (arch * 0.02)
    y = np.maximum(y, 0)
    return pd.DataFrame({"Dev Period": dev, "Gross Loss ($000)": y})

# -----------------------------
# Session State Initialization
# -----------------------------
if "event_ctx" not in st.session_state:
    st.session_state.event_ctx = {
        "Accident Year": 2018,
        "Period": 2018,
        "Unit": 1000,
        "Event": "Michael",
        "LE": "ARL",
    }

if "programs_df" not in st.session_state:
    st.session_state.programs_df = _make_programs_df()

if "selected_program_id" not in st.session_state:
    st.session_state.selected_program_id = int(st.session_state.programs_df["id"].iloc[0])

if "layer_by_program" not in st.session_state:
    st.session_state.layer_by_program = {}

# Ensure a layer matrix exists for current selection
def ensure_layer(program_id: int):
    if program_id not in st.session_state.layer_by_program:
        programs = st.session_state.programs_df
        r = programs.loc[programs["id"] == program_id].iloc[0]
        mat = _make_default_layer_matrix(
            accident_year=int(st.session_state.event_ctx["Accident Year"]),
            currency=str(r["Currency"]),
            selected_unl=float(r["Selected UNL"]),
        )
        st.session_state.layer_by_program[program_id] = mat

ensure_layer(st.session_state.selected_program_id)

# -----------------------------
# UI
# -----------------------------
st.markdown("## Main Screen")

# Top controls bar
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 1.1, 1.0, 1.0, 1.1, 0.9, 0.9, 0.9])

with c1:
    st.button("Event >>", use_container_width=True)

with c2:
    st.button("Add Program >>", use_container_width=True)

with c3:
    st.session_state.event_ctx["Accident Year"] = st.number_input(
        "Accident Year", value=int(st.session_state.event_ctx["Accident Year"]), step=1
    )
with c4:
    st.session_state.event_ctx["Period"] = st.number_input(
        "Period", value=int(st.session_state.event_ctx["Period"]), step=1
    )
with c5:
    st.session_state.event_ctx["Unit"] = st.number_input(
        "Unit", value=float(st.session_state.event_ctx["Unit"]), step=100.0
    )
with c6:
    st.session_state.event_ctx["Event"] = st.text_input("Event", value=st.session_state.event_ctx["Event"])
with c7:
    st.session_state.event_ctx["LE"] = st.text_input("LE", value=st.session_state.event_ctx["LE"])
with c8:
    save_clicked = st.button("Save", type="primary", use_container_width=True)

st.divider()

# Main program grid
st.markdown("### Programs")

programs_df = st.session_state.programs_df.copy()

# Configure some columns as numeric for nicer editing
col_config = {
    "FX": st.column_config.NumberColumn(format="%.4f", step=0.0001),
    "Exposed": st.column_config.NumberColumn(step=0.1),
    "Rep_FGU": st.column_config.NumberColumn(step=1.0),
    "Rep_UNL": st.column_config.NumberColumn(step=1.0),
    "Selected UNL": st.column_config.NumberColumn(step=1.0),
    "Layer Loss": st.column_config.NumberColumn(step=1.0),
    "Arch Loss": st.column_config.NumberColumn(step=1.0),
    "Arch USD Gross": st.column_config.NumberColumn(step=1.0),
    "Arch USD Ceded to US": st.column_config.NumberColumn(step=1.0),
    "Arch USD Net": st.column_config.NumberColumn(step=1.0),
    "Arch USD NetRP": st.column_config.NumberColumn(step=1.0),
    "Arch USD Net of RP": st.column_config.NumberColumn(step=1.0),
    "Booked Prior Gross": st.column_config.NumberColumn(step=1.0),
    "Booked Prior Net of RP": st.column_config.NumberColumn(step=1.0),
    "Change Gross": st.column_config.NumberColumn(step=1.0),
    "Change Net of RP": st.column_config.NumberColumn(step=1.0),
}

edited_programs = st.data_editor(
    programs_df,
    hide_index=True,
    use_container_width=True,
    height=340,
    disabled=["id"],
    column_config=col_config,
    key="program_grid_editor",
)

# Persist edits to session state immediately (like Excel)
st.session_state.programs_df = edited_programs.copy()

# Program selector (simple + reliable without extra packages)
ids = st.session_state.programs_df["id"].tolist()
selected_id = st.selectbox(
    "Selected Program",
    options=ids,
    index=ids.index(st.session_state.selected_program_id) if st.session_state.selected_program_id in ids else 0,
    format_func=lambda i: f"{i} - {st.session_state.programs_df.loc[st.session_state.programs_df['id']==i, 'Cedant'].iloc[0]}",
)
st.session_state.selected_program_id = int(selected_id)
ensure_layer(st.session_state.selected_program_id)

st.divider()

# Lower panels: Layer detail + Chart
left, right = st.columns([1.35, 1.0], gap="large")

with left:
    st.markdown("### Layer Detail")

    layer_df = st.session_state.layer_by_program[st.session_state.selected_program_id].copy()

    # Make sure totals are updated before display (and after edits)
    layer_df = _compute_totals(layer_df)

    edited_layer = st.data_editor(
        layer_df,
        hide_index=True,
        use_container_width=True,
        height=360,
        disabled=["Metric"],
        key="layer_editor",
    )

    # Recompute totals after edits and persist
    edited_layer = _compute_totals(edited_layer)
    st.session_state.layer_by_program[st.session_state.selected_program_id] = edited_layer

with right:
    st.markdown("### LAWF")

    row = st.session_state.programs_df.loc[
        st.session_state.programs_df["id"] == st.session_state.selected_program_id
    ].iloc[0]

    lawf = _lawf_series_from_program_row(row)
    fig = px.line(lawf, x="Dev Period", y="Gross Loss ($000)", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# Save behavior (for now: snapshot + message)
if save_clicked:
    # In a DB-backed version, this is where you'd write to database.
    st.session_state["last_saved_snapshot"] = {
        "event": dict(st.session_state.event_ctx),
        "programs": st.session_state.programs_df.copy(),
        "layers": {k: v.copy() for k, v in st.session_state.layer_by_program.items()},
    }
    st.success("Saved (in-session). Next step: persist to database / files.")

# Optional: show debug info
with st.expander("Debug / Current Context", expanded=False):
    st.json(st.session_state.event_ctx)
    st.write("Selected Program ID:", st.session_state.selected_program_id)