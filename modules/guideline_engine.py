"""Module 3: Clinical Guideline & Staging Engine."""

def evaluate_guideline_stage(metrics: dict, efw_percentile, amniotic_fluid: str):
    # 1. Missing Data Checks
    if efw_percentile is None:
        return {"error": "cannot stage, need EFW (Estimated Fetal Weight) percentile"}
    if not amniotic_fluid:
        return {"error": "cannot stage, need amniotic fluid level"}
        
    ga_weeks = metrics["clinical_weeks"]
    
    low_fluid = str(amniotic_fluid).lower() == "low"
    try:
        is_fgr = float(efw_percentile) < 10
    except ValueError:
        is_fgr = False
    
    # --- STAGE 0: Term Pregnancy Override ---
    if ga_weeks >= 40:
        return {
            "stage": "Term Pregnancy",
            "action": "Deliver NOW (Proceed with delivery / Induction of labor)",
            "interval": "N/A",
            "rule": f"Pregnancy is at {ga_weeks} weeks. Routine expectant management is no longer indicated."
        }

    # --- STAGE III: Pathological (REDF) ---
    if metrics["ua_flow"].lower() == "reversed":
        if ga_weeks >= 30:
            action = "Deliver NOW (Immediate termination of pregnancy to prevent fetal demise)"
        else:
            action = "Deliver at 30 weeks (or 24-48h post-steroids depending on viability)"
            
        return {
            "stage": "Stage III (Pathological: REDF)", 
            "action": action, 
            "interval": "Continuous / 12h CTG monitoring", 
            "rule": "Umbilical REDF carries extremely high risk of fetal hypoxia and demise."
        }

    # --- STAGE II: Pathological (AEDF) ---
    if metrics["ua_flow"].lower() == "absent":
        if ga_weeks >= 34:
            action = "Deliver NOW (Immediate delivery indicated)"
        else:
            action = "Target Delivery at 34 weeks; admit for intensive monitoring"
            
        return {
            "stage": "Stage II (Pathological: AEDF)", 
            "action": action, 
            "interval": "Rescan 48h / Daily CTG", 
            "rule": "Umbilical AEDF indicates severe placental insufficiency."
        }

    # --- STAGE I: Abnormal / Insufficiency ---
    diagnoses = []
    if is_fgr: diagnoses.append("IUGR")
    if low_fluid: diagnoses.append("Low Fluid")
    if metrics["ua_elevated"]: diagnoses.append("Cord Insufficiency")
    if metrics["ut_elevated"]: diagnoses.append("Uterine Insufficiency")
    if metrics["brain_sparing"]: diagnoses.append("Brain Sparing")
    
    if diagnoses:
        if ga_weeks >= 37:
            action = "Deliver NOW (Immediate delivery indicated)"
        else:
            action = "Target Delivery between 37-38 weeks"
            
        return {
            "stage": "Stage I (Abnormal): " + ", ".join(diagnoses),
            "action": action,
            "interval": "Weekly / Bi-weekly CTG",
            "rule": "Placental/Uterine insufficiency detected or FGR criteria met (GCPR 2022)."
        }
        
    # --- STAGE 0: Normal ---
    return {
        "stage": "Normal / Healthy",
        "action": "Target Delivery at term (39-40 weeks)",
        "interval": "Rescan in 2-3 weeks",
        "rule": "All Doppler indices, fluid, and EFW within normal limits."
    }