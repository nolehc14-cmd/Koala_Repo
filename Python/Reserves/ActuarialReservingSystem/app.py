# app.py
import streamlit as st
import plotly.express as px

from ars.db import SessionLocal
from ars.repositories import get_events, get_programs_df, get_layer_matrix

st.set_page_config(layout="wide", page_title="Actuarial Reserving System")

db = SessionLocal()

# --- Header / top controls
events = get_events(db)
if not events:
    st.error("No events found. Run: python data/seed.py")
    st.stop()

# mimic your top-left block
c1, c2, c3, c4, c5, c6, c7 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 1.0, 1.0])

with c1:
    ev = st.selectbox("Event", events, format_func=lambda x: f"{x.event_name} ({x.accident_year})")

with c2:
    accident_year = st.number_input("Accident Year", value=int(ev.accident_year), step=1)

with c3:
    period = st.number_input("Period", value=int(ev.period), step=1)

with c4:
    unit = st.number_input("Unit", value=float(ev.unit), step=100.0)

with c5:
    le = st.text_input("LE", value=ev.le_code or "")

with c7:
    save_clicked = st.button("Save", use_container_width=True)

# --- Main table
programs_df = get_programs_df(db, ev.id)

st.markdown("### Programs")
edited_df = st.data_editor(
    programs_df,
    hide_index=True,
    disabled=["id"],            # keep id read-only
    use_container_width=True,
    height=360,
    key="program_grid",
)

# Simple row selection approach (built-in): choose a row id from a selectbox
# (If you want click-to-select like Excel, use streamlit-aggrid)
selected_id = None
if not edited_df.empty:
    selected_id = st.selectbox("Selected Program (for layer detail + chart)", edited_df["id"].tolist())

# --- Lower panels
left, right = st.columns([1.25, 1.0])

with left:
    st.markdown("### Layer Detail")
    if selected_id:
        mat = get_layer_matrix(db, selected_id)
        st.data_editor(mat, hide_index=True, use_container_width=True, height=320, key="layer_matrix")
    else:
        st.info("Select a program to view layer detail.")

with right:
    st.markdown("### LAWF")
    # placeholder chart logic; replace with real lawf_service output
    if selected_id:
        dev = list(range(1, 13))
        y = [0]*12
        fig = px.line(x=dev, y=y, markers=True, labels={"x": "Dev Period", "y": "Gross Loss ($000)"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a program to view chart.")

# --- Persist changes (step 6 shows the full writeback pattern)
if save_clicked:
    st.success("Wire this button to persist Event + Program + Layer changes (see Step 6).")

db.close()