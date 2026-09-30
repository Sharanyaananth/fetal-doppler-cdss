"""Module 5: Clinical PDF Summary Generator."""
from fpdf import FPDF
from datetime import datetime

class ClinicalDopplerReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 8, 'DEPARTMENT OF FETAL MEDICINE', border=0, ln=1, align='C')
        self.set_font('Arial', 'B', 11)
        self.cell(0, 6, 'Fetal Doppler & Clinical Staging Report', border=0, ln=1, align='C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, '(Adhering to FOGSI GCPR 2022 & Barcelona Protocol)', border=0, ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_x(10)
        self.multi_cell(0, 4, 
            txt='PCPNDT ACT COMPLIANCE NOTICE: This system does not record, assess, or disclose fetal sex. This is a clinical decision-support document. All medical decisions must be independently confirmed by the attending obstetrician.')

def generate_pdf_report(patient_data, metrics, stage_data):
    pdf = ClinicalDopplerReport()
    pdf.add_page()
    
    # --- 1. Patient Demographics & Gestational Dating ---
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 7, ' 1. PATIENT DEMOGRAPHICS & DATING', border=1, ln=1, align='L', fill=True)
    
    pdf.set_font('Arial', '', 10)
    patient_id = patient_data.get("patient_id", "Manual-001")
    date_str = datetime.now().strftime('%d-%b-%Y %H:%M')
    
    pdf.cell(45, 7, ' Patient ID:', border='L', ln=0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(50, 7, f'{patient_id}', border=0, ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(45, 7, ' Date of Examination:', border=0, ln=0)
    pdf.cell(50, 7, f'{date_str}', border='R', ln=1)
    
    w_lmp = patient_data.get("weeks_by_lmp", "Unknown")
    w_usg = patient_data.get("weeks_by_scan", "Unknown")
    clin_weeks = metrics.get('clinical_weeks', 'Unknown')
    
    pdf.cell(45, 7, ' Gestational Age (LMP):', border='L', ln=0)
    pdf.cell(50, 7, f'{w_lmp}', border=0, ln=0)
    pdf.cell(45, 7, ' Gestational Age (USG):', border=0, ln=0)
    pdf.cell(50, 7, f'{w_usg}', border='R', ln=1)

    pdf.cell(45, 7, ' Assigned Clinical Age:', border='L,B', ln=0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(145, 7, f'{clin_weeks} Weeks', border='R,B', ln=1)
    pdf.ln(5)

    # --- 2. Fetal Biometry & Environment ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, ' 2. FETAL BIOMETRY & ENVIRONMENT', border=1, ln=1, align='L', fill=True)
    pdf.set_font('Arial', '', 10)
    
    efw = patient_data.get("efw_percentile")
    efw_str = f"{efw}th centile" if efw is not None else "Not Provided"
    fluid = patient_data.get("amniotic_fluid", "Unknown")
    
    pdf.cell(45, 7, ' Estimated Fetal Weight:', border='L,B', ln=0)
    pdf.cell(50, 7, f'{efw_str}', border='B', ln=0)
    pdf.cell(45, 7, ' Amniotic Fluid Level:', border='B', ln=0)
    pdf.cell(50, 7, f'{str(fluid).title()}', border='R,B', ln=1)
    pdf.ln(5)

    # --- 3. Comprehensive Doppler Indices ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, ' 3. DOPPLER INDICES & HEMODYNAMICS', border=1, ln=1, align='L', fill=True)
    
    # Table Header
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(50, 7, ' Vessel / Parameter', border=1, ln=0, align='C')
    pdf.cell(40, 7, ' Measured Value', border=1, ln=0, align='C')
    pdf.cell(50, 7, ' Flow Characteristics', border=1, ln=0, align='C')
    pdf.cell(50, 7, ' Interpretation', border=1, ln=1, align='C')
    
    pdf.set_font('Arial', '', 9)
    
    # Umbilical Artery
    pdf.cell(50, 7, ' Umbilical Artery (UA) PI', border=1, ln=0, align='L')
    pdf.cell(40, 7, f" {metrics['ua_pi'] if metrics['ua_pi'] else 'N/A'}", border=1, ln=0, align='C')
    pdf.cell(50, 7, f" {str(metrics['ua_flow']).title()}", border=1, ln=0, align='C')
    ua_interp = "Elevated (>95th %ile)" if metrics['ua_elevated'] else "Normal"
    pdf.cell(50, 7, f" {ua_interp}", border=1, ln=1, align='C')
    
    # Middle Cerebral Artery
    pdf.cell(50, 7, ' Middle Cerebral Artery PI', border=1, ln=0, align='L')
    pdf.cell(40, 7, f" {metrics['mca_pi'] if metrics['mca_pi'] else 'N/A'}", border=1, ln=0, align='C')
    pdf.cell(50, 7, " - ", border=1, ln=0, align='C')
    mca_interp = "Low (<5th %ile)" if metrics['mca_low'] else "Normal"
    pdf.cell(50, 7, f" {mca_interp}", border=1, ln=1, align='C')
    
    # CPR
    pdf.cell(50, 7, ' Cerebroplacental Ratio (CPR)', border=1, ln=0, align='L')
    pdf.cell(40, 7, f" {metrics['cpr'] if metrics['cpr'] else 'N/A'}", border=1, ln=0, align='C')
    pdf.cell(50, 7, " - ", border=1, ln=0, align='C')
    cpr_interp = "Abnormal (<5th %ile)" if metrics['brain_sparing'] else "Normal"
    pdf.cell(50, 7, f" {cpr_interp}", border=1, ln=1, align='C')

    # Uterine Artery
    pdf.cell(50, 7, ' Mean Uterine Artery PI', border=1, ln=0, align='L')
    pdf.cell(40, 7, f" {metrics['mean_ut_pi'] if metrics['mean_ut_pi'] else 'N/A'}", border=1, ln=0, align='C')
    pdf.cell(50, 7, " - ", border=1, ln=0, align='C')
    ut_interp = "Elevated (>95th %ile)" if metrics['ut_elevated'] else "Normal"
    pdf.cell(50, 7, f" {ut_interp}", border=1, ln=1, align='C')
    
    pdf.ln(5)

    # --- 4. Clinical Impression & Recommendations ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, ' 4. CLINICAL IMPRESSION & RECOMMENDATIONS', border=1, ln=1, align='L', fill=True)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, ' Classification:', border='L', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(150, 8, f"{stage_data['stage']}", border='R', ln=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, ' Action / Delivery:', border='L', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(150, 8, f"{stage_data['action']}", border='R', ln=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, ' Surveillance Plan:', border='L', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(150, 8, f"{stage_data['interval']}", border='R', ln=1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(40, 8, ' Clinical Rationale:', border='L,B', ln=0)
    pdf.set_font('Arial', '', 10)
    pdf.cell(150, 8, f"{stage_data['rule']}", border='R,B', ln=1)

    pdf.ln(15)

    # --- Signatures ---
    pdf.set_font('Arial', '', 10)
    pdf.cell(95, 5, '___________________________________', border=0, ln=0, align='C')
    pdf.cell(95, 5, '___________________________________', border=0, ln=1, align='C')
    pdf.cell(95, 5, 'Examining Physician Signature', border=0, ln=0, align='C')
    pdf.cell(95, 5, 'Date / Time', border=0, ln=1, align='C')

    return bytes(pdf.output())