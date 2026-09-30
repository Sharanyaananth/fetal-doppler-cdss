import streamlit as st
import json
import os
from datetime import datetime
from modules.percentile_engine import evaluate_percentiles
from modules.guideline_engine import evaluate_guideline_stage
from modules.report_generator import generate_pdf_report

st.set_page_config(page_title="Fetal Doppler Decision Engine", layout="wide")

DB_FILE = "patient_database.json"
SCHEMA_DIR = "schemas"

if not os.path.exists(SCHEMA_DIR):
    os.makedirs(SCHEMA_DIR)

def save_record(patient_id, data_to_process, metrics, staging):
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: db = json.load(f)
            except: db = {}
    else: db = {}
        
    if patient_id not in db: db[patient_id] = []
        
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_data": data_to_process,
        "metrics": metrics,
        "staging": staging
    }
    db[patient_id].append(record)
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

def get_records(patient_id):
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f).get(patient_id, [])
            except: return []
    return []

def load_selected_json():
    selection = st.session_state.json_selector
    if selection != "-- Manual Entry --":
        try:
            filepath = os.path.join(SCHEMA_DIR, selection)
            with open(filepath, "r") as f: data = json.load(f)
            
            st.session_state.p_id = data.get("patient_id", "")
            st.session_state.p_lmp = data.get("weeks_by_lmp", "")
            st.session_state.p_usg = data.get("weeks_by_scan", "")
            
            efw_val = data.get("efw_percentile")
            st.session_state.p_efw = str(efw_val) if efw_val is not None else ""
            st.session_state.p_fluid = data.get("amniotic_fluid", "normal").lower()
            
            for vessel in data.get("vessels", []):
                v_name = vessel.get("vessel")
                val = vessel.get("pi")
                num = float(val) if val is not None else None
                
                if v_name == "umbilical_artery":
                    st.session_state.p_ua_pi = num
                    st.session_state.p_ua_flow = vessel.get("flow_between_beats", "present").lower()
                elif v_name == "mca": st.session_state.p_mca_pi = num
                elif v_name == "uterine_right": st.session_state.p_ut_r = num
                elif v_name == "uterine_left": st.session_state.p_ut_l = num
                    
            st.toast(f"✅ Auto-filled data from {selection}")
        except Exception as e:
            st.error(f"Error loading scan data: {e}")

default_state = {
    "p_id": "", "p_lmp": "", "p_usg": "", "p_efw": "",
    "p_fluid": "normal", "p_ua_pi": None, "p_ua_flow": "present",
    "p_mca_pi": None, "p_ut_r": None, "p_ut_l": None
}
for key, val in default_state.items():
    if key not in st.session_state: st.session_state[key] = val

st.title("🩺 Fetal Doppler Decision Engine")
st.caption("Clinical Investigational Rules Engine (RCOG Green-top 31 Compliant)")

tab_new, tab_history = st.tabs(["📝 New Evaluation", "🔍 Patient History Lookup"])

with tab_new:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Clinical Data Input")
        json_files = [f for f in os.listdir(SCHEMA_DIR) if f.endswith('.json')]
        st.selectbox("📥 Auto-Fill from Vision Module", ["-- Manual Entry --"] + json_files, key="json_selector", on_change=load_selected_json)
        
        with st.form("manual_form"):
            st.write("**Verify or manually enter patient parameters:**")
            m_id = st.text_input("Patient ID", key="p_id")
            m_lmp = st.text_input("Weeks by LMP (e.g., 34w0d)", key="p_lmp")
            m_usg = st.text_input("Weeks by Scan (e.g., 34w0d)", key="p_usg")
            m_efw = st.text_input("EFW Percentile (leave blank if unknown)", key="p_efw")
            
            fluid_options = ["normal", "low"]
            fluid_idx = fluid_options.index(st.session_state.p_fluid) if st.session_state.p_fluid in fluid_options else 0
            m_fluid = st.selectbox("Amniotic Fluid", fluid_options, index=fluid_idx)
            
            st.write("**Doppler PI Values**")
            c_a, c_b = st.columns(2)
            m_ua = c_a.number_input("Umbilical Artery PI", key="p_ua_pi", step=0.01, format="%.2f", value=st.session_state.p_ua_pi)
            flow_options = ["present", "absent", "reversed"]
            flow_idx = flow_options.index(st.session_state.p_ua_flow) if st.session_state.p_ua_flow in flow_options else 0
            m_ua_flow = c_a.selectbox("UA Flow", flow_options, index=flow_idx)
            
            m_mca = c_b.number_input("MCA PI", key="p_mca_pi", step=0.01, format="%.2f", value=st.session_state.p_mca_pi)
            m_ut_r = c_a.number_input("Uterine Right PI", key="p_ut_r", step=0.01, format="%.2f", value=st.session_state.p_ut_r)
            m_ut_l = c_b.number_input("Uterine Left PI", key="p_ut_l", step=0.01, format="%.2f", value=st.session_state.p_ut_l)
            
            submit_manual = st.form_submit_button("Calculate Clinical Stage & Save")

    with col2:
        st.subheader("2. Guideline Engine Output")
        
        if submit_manual:
            data_to_process = {
                "patient_id": m_id, "weeks_by_lmp": m_lmp, "weeks_by_scan": m_usg,
                "efw_percentile": float(m_efw) if m_efw.strip() else None,
                "amniotic_fluid": m_fluid,
                "vessels": [
                    {"vessel": "umbilical_artery", "pi": m_ua, "flow_between_beats": m_ua_flow},
                    {"vessel": "mca", "pi": m_mca},
                    {"vessel": "uterine_right", "pi": m_ut_r},
                    {"vessel": "uterine_left", "pi": m_ut_l}
                ]
            }
            
            metrics = evaluate_percentiles(data_to_process.get("weeks_by_lmp", ""), data_to_process.get("weeks_by_scan", ""), data_to_process.get("vessels", []))
            staging = evaluate_guideline_stage(metrics, data_to_process.get("efw_percentile"), data_to_process.get("amniotic_fluid"))
            
            save_record(m_id, data_to_process, metrics, staging)
            st.toast(f"Record saved for Patient: {m_id}", icon="✅")

            if metrics.get("is_discrepancy"): st.warning(f"⚠️️ **Dating Discrepancy (>= 2 weeks):** Using LMP ({data_to_process.get('weeks_by_lmp')}) for percentile charts.")
                
            st.markdown(f"**Clinical Weeks Assigned:** {metrics['clinical_weeks']}")
            
            metric_cols = st.columns(4)
            metric_cols[0].metric("UA PI", str(metrics.get('ua_pi', 'N/A')))
            metric_cols[1].metric("MCA PI", str(metrics.get('mca_pi', 'N/A')))
            metric_cols[2].metric("Mean Uterine PI", str(metrics.get('mean_ut_pi', 'N/A')))
            metric_cols[3].metric("CPR", str(metrics.get('cpr', 'N/A')))
            
            st.divider()
            st.subheader(f"Classification: {staging.get('stage', 'UNKNOWN')}")
            st.success(f"**Action:** {staging.get('action', '')}")
            st.info(f"**Surveillance Interval:** {staging.get('interval', '')}")
            st.caption(f"**Applied Logic:** {staging.get('rule', '')}")
            
            st.divider()
            pdf_bytes = generate_pdf_report(data_to_process, metrics, staging)
            st.download_button(
                label="📄 Download In-Depth Doctor Report (PDF)",
                data=pdf_bytes,
                file_name=f"fetal_doppler_{m_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("👈 Select a scan from the dropdown or manually enter data, then click 'Calculate Clinical Stage' to generate the report.")

with tab_history:
    st.subheader("🔍 Search Patient History")
    search_id = st.text_input("Enter Patient ID to retrieve past records:", placeholder="e.g., R1-normal")
    if search_id:
        records = get_records(search_id)
        if not records: st.warning(f"No records found for Patient ID: {search_id}")
        else:
            st.success(f"Found {len(records)} record(s) for {search_id}")
            for i, record in enumerate(reversed(records)):
                with st.expander(f"🗓️ Evaluation Date: {record['timestamp']} - {record['staging']['stage']}", expanded=(i==0)):
                    st.write(f"**Action Recommended:** {record['staging']['action']}")
                    st.write(f"**Clinical Weeks at scan:** {record['metrics'].get('clinical_weeks', 'N/A')}")
                    
                    r_col1, r_col2 = st.columns(2)
                    r_col1.write(f"- **UA PI:** {record['metrics'].get('ua_pi', 'N/A')}")
                    r_col1.write(f"- **MCA PI:** {record['metrics'].get('mca_pi', 'N/A')}")
                    r_col2.write(f"- **Mean Uterine PI:** {record['metrics'].get('mean_ut_pi', 'N/A')}")
                    r_col2.write(f"- **CPR:** {record['metrics'].get('cpr', 'N/A')}")
                    
                    hist_pdf_bytes = generate_pdf_report(record['patient_data'], record['metrics'], record['staging'])
                    st.download_button(
                        label=f"📄 Download Past Report PDF",
                        data=hist_pdf_bytes,
                        file_name=f"historical_report_{search_id}_{record['timestamp'][:10].replace('-', '')}.pdf",
                        mime="application/pdf",
                        key=f"download_{search_id}_{i}"
                    )