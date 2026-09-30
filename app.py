import streamlit as st
import json
import os
from datetime import datetime
from modules.percentile_engine import evaluate_percentiles
from modules.guideline_engine import evaluate_guideline_stage
from modules.report_generator import generate_pdf_report

st.set_page_config(page_title="Fetal Doppler Decision Engine", layout="wide")

# --- Database Helper Functions ---
DB_FILE = "patient_database.json"

def save_record(patient_id, data_to_process, metrics, staging):
    """Saves the clinical evaluation to a local JSON file."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                db = json.load(f)
            except:
                db = {}
    else:
        db = {}
        
    if patient_id not in db:
        db[patient_id] = []
        
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
    """Retrieves all past records for a given patient ID."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                db = json.load(f)
                return db.get(patient_id, [])
            except:
                return []
    return []

# --- Main App UI ---
st.title("🩺 Fetal Doppler Decision Engine")
st.caption("Clinical Investigational Rules Engine with Patient History tracking")

# Create top-level tabs for the app workflow
tab_new, tab_history = st.tabs(["📝 New Evaluation", "🔍 Patient History Lookup"])

with tab_new:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("1. Clinical Data Input")
        
        with st.form("manual_form"):
            st.write("Enter patient and scan parameters below:")
            m_id = st.text_input("Patient ID (used for saving/searching)", "Normal-001")
            m_lmp = st.text_input("Weeks by LMP (e.g., 34w0d)", "34w0d")
            m_usg = st.text_input("Weeks by Scan (e.g., 34w0d)", "34w0d")
            m_efw = st.text_input("EFW Percentile (leave blank if unknown)", "45")
            m_fluid = st.selectbox("Amniotic Fluid", ["normal", "low"])
            
            st.write("**Doppler PI Values**")
            c_a, c_b = st.columns(2)
            m_ua = c_a.number_input("Umbilical Artery PI", value=0.95, step=0.01)
            m_ua_flow = c_a.selectbox("UA Flow", ["present", "absent", "reversed"])
            m_mca = c_b.number_input("MCA PI", value=1.85, step=0.01)
            m_ut_r = c_a.number_input("Uterine Right PI", value=0.65, step=0.01)
            m_ut_l = c_b.number_input("Uterine Left PI", value=0.62, step=0.01)
            
            submit_manual = st.form_submit_button("Calculate Clinical Stage & Save")

    with col2:
        st.subheader("2. Guideline Engine Output")
        
        if submit_manual:
            data_to_process = {
                "patient_id": m_id,
                "weeks_by_lmp": m_lmp,
                "weeks_by_scan": m_usg,
                "efw_percentile": float(m_efw) if m_efw.strip() else None,
                "amniotic_fluid": m_fluid,
                "vessels": [
                    {"vessel": "umbilical_artery", "pi": m_ua, "flow_between_beats": m_ua_flow},
                    {"vessel": "mca", "pi": m_mca},
                    {"vessel": "uterine_right", "pi": m_ut_r},
                    {"vessel": "uterine_left", "pi": m_ut_l}
                ]
            }
            
            # Run Percentile Engine
            metrics = evaluate_percentiles(
                data_to_process.get("weeks_by_lmp", ""), 
                data_to_process.get("weeks_by_scan", ""), 
                data_to_process.get("vessels", [])
            )
            
            # Run Guideline Engine
            staging = evaluate_guideline_stage(metrics, data_to_process.get("efw_percentile"), data_to_process.get("amniotic_fluid"))
            
            if "error" in staging:
                st.error(f"**System Halted:** {staging['error']}")
            else:
                # Save to database
                save_record(m_id, data_to_process, metrics, staging)
                st.toast(f"Record saved for Patient: {m_id}", icon="✅")

                if metrics["is_discrepancy"]:
                    st.warning(f"⚠️ **Dating Discrepancy (≥ 2 weeks):** Using LMP ({data_to_process.get('weeks_by_lmp')}) for percentile charts.")
                    
                st.markdown(f"**Clinical Weeks Assigned:** {metrics['clinical_weeks']}")
                
                metric_cols = st.columns(4)
                metric_cols[0].metric("UA PI", metrics['ua_pi'])
                metric_cols[1].metric("MCA PI", metrics['mca_pi'])
                metric_cols[2].metric("Mean Uterine PI", metrics['mean_ut_pi'])
                metric_cols[3].metric("CPR", metrics['cpr'])
                
                st.divider()
                st.subheader(f"Classification: {staging['stage']}")
                st.success(f"**Action:** {staging['action']}")
                st.info(f"**Surveillance Interval:** {staging['interval']}")
                
                st.divider()
                pdf_bytes = generate_pdf_report(data_to_process, metrics, staging)
                st.download_button(
                    label="📄 Download In-Depth Doctor Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"fetal_doppler_{m_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("👈 Enter patient data on the left and click 'Calculate Clinical Stage' to see the result and save the report.")

with tab_history:
    st.subheader("🔍 Search Patient History")
    search_id = st.text_input("Enter Patient ID to retrieve past records:", placeholder="e.g., Normal-001")
    
    if search_id:
        records = get_records(search_id)
        
        if not records:
            st.warning(f"No records found for Patient ID: {search_id}")
        else:
            st.success(f"Found {len(records)} record(s) for {search_id}")
            
            # Display records in reverse chronological order (newest first)
            for i, record in enumerate(reversed(records)):
                with st.expander(f"🗓️ Evaluation Date: {record['timestamp']} - {record['staging']['stage']}", expanded=(i==0)):
                    
                    st.write(f"**Action Recommended:** {record['staging']['action']}")
                    st.write(f"**Clinical Weeks at scan:** {record['metrics']['clinical_weeks']}")
                    
                    r_col1, r_col2 = st.columns(2)
                    r_col1.write(f"- **UA PI:** {record['metrics']['ua_pi']}")
                    r_col1.write(f"- **MCA PI:** {record['metrics']['mca_pi']}")
                    r_col2.write(f"- **Mean Uterine PI:** {record['metrics']['mean_ut_pi']}")
                    r_col2.write(f"- **CPR:** {record['metrics']['cpr']}")
                    
                    # Generate historical PDF on the fly
                    hist_pdf_bytes = generate_pdf_report(record['patient_data'], record['metrics'], record['staging'])
                    
                    st.download_button(
                        label=f"📄 Download Past Report PDF",
                        data=hist_pdf_bytes,
                        file_name=f"historical_report_{search_id}_{record['timestamp'][:10].replace('-', '')}.pdf",
                        mime="application/pdf",
                        key=f"download_{search_id}_{i}" # Unique key required by Streamlit
                    )