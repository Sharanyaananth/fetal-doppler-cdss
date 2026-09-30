"""Module 3: Clinical Guideline Engine (RCOG Green-top 31)."""
import re

def _safe_float(val):
    if val in (None, "", "None", "N/A"): return None
    match = re.search(r"[-+]?\d*\.\d+|\d+", str(val).replace(",", "."))
    return float(match.group()) if match else None

def evaluate_guideline_stage(metrics: dict, efw_percentile, amniotic_fluid: str):
    ga_weeks = metrics.get("clinical_weeks", 0)
    ua_pi = metrics.get("ua_pi")
    ua_flow = metrics.get("ua_flow", "").lower() if metrics.get("ua_flow") else ""
    
    ua_num = _safe_float(ua_pi)
    mca_num = _safe_float(metrics.get("mca_pi"))
    cpr_num = _safe_float(metrics.get("cpr"))
    
    # --- FORMAL CLASSIFICATION FOR BAD/MISSING DATA (NO MORE ERRORS) ---
    if ua_num is None or ua_num <= 0.0: 
        return {
            "stage": "ABNORMAL - MISSING MANDATORY DOPPLER",
            "action": "DELIVERY TIMING: UNABLE TO ASSESS. NOTES: Cannot assess cord Doppler: need umbilical artery PI. Must NOT say Normal.",
            "interval": "Urgent Rescan Required",
            "rule": "RATIONALE: Umbilical Artery PI is the primary surveillance tool. Cannot safely calculate delivery timing without it."
        }
    if ga_weeks > 44 or ga_weeks < 20: 
        return {
            "stage": "ABNORMAL - INVALID GESTATION",
            "action": f"DELIVERY TIMING: UNABLE TO ASSESS. NOTES: Reject: {ga_weeks} weeks impossible. No result produced.",
            "interval": "Data Correction Required",
            "rule": "RATIONALE: Gestational age is outside viable or valid clinical limits."
        }
    if efw_percentile is not None and (float(efw_percentile) > 100 or float(efw_percentile) < 0): 
        return {
            "stage": "ABNORMAL - INVALID EFW",
            "action": f"DELIVERY TIMING: UNABLE TO ASSESS. NOTES: Reject: EFW centile {efw_percentile} out of range.",
            "interval": "Data Correction Required",
            "rule": "RATIONALE: EFW Centile must be between 0 and 100."
        }

    is_sga = float(efw_percentile) < 10 if efw_percentile is not None else None
    steroids_needed = (24 <= ga_weeks < 36)
    steroids_text = "steroids if delivery considered (24+0 to 35+6)" if steroids_needed else "steroids"
    
    # Brain Sparing logic
    is_brain_sparing = False
    if mca_num and ua_num and (mca_num / ua_num) < 1.0: is_brain_sparing = True
    elif cpr_num and cpr_num < 1.0: is_brain_sparing = True
    elif metrics.get("mca_low") or metrics.get("cpr_low"): is_brain_sparing = True

    mca_flag = " Flag: MCA shows reversed flow between beats -> 'check probe pressure / repeat', not danger." if mca_num and mca_num > 3.0 else ""

    # --- RULE 1: GATEKEEPER (Not SGA) ---
    if is_sga is False:
        if ga_weeks >= 40:
             action = "DELIVERY TIMING: Routine term delivery. NOTES: Not SGA -> outside the SGA pathway; routine care by the obstetrician. Must NOT say 'rescan in 2-3 weeks'."
        else:
             action = f"DELIVERY TIMING: Routine term delivery. NOTES: Not SGA (EFW {efw_percentile}th centile), cord Doppler normal -> no SGA pathway action.{mca_flag}"
        return {
            "stage": "NORMAL - Appropriate for Gestational Age",
            "action": action,
            "interval": "Routine obstetric care",
            "rule": "RATIONALE (Rule 1): EFW >= 10th centile. RCOG SGA pathway does not apply."
        }

    # --- MISSING EFW HANDLING ---
    if is_sga is None:
        base_msg = "SGA needs EFW or AC <10th: missing -> ask for it, but still show Doppler findings. IF SGA:"
        if ua_flow in ["absent", "reversed"]:
             return {
                 "stage": "PATHOLOGICAL - Pending EFW (AREDV Detected)", 
                 "action": f"DELIVERY TIMING: TERMINATE NOW (By 32 weeks). NOTES: {base_msg} daily surveillance; ductus venosus Doppler needed; deliver by 32 weeks after steroids. caesarean recommended.", 
                 "interval": "Daily; Needs DV", 
                 "rule": "RATIONALE (Rules 1 & 4): Suspected SGA with Critical AREDV requires immediate action."
             }
        elif metrics.get("ua_elevated") or is_brain_sparing:
            mca_low_text = " MCA/CPR low = brain sparing (shown, but RCOG: MCA does not time delivery before term)." if is_brain_sparing else ""
            return {
                "stage": "ABNORMAL - Pending EFW (Abnormal Doppler shown)",
                "action": f"DELIVERY TIMING: Deliver no later than 37 weeks. NOTES: {base_msg}{mca_low_text} after 32 weeks + abnormal cord Doppler -> deliver no later than 37 weeks; twice-weekly surveillance; {steroids_text}. Need EFW/AC.",
                "interval": "Twice weekly",
                "rule": "RATIONALE (Rules 1, 3, 5): Abnormal Dopplers detected. Must confirm SGA to execute delivery plan."
            }
        else:
            return {
                "stage": "ABNORMAL - Pending EFW", 
                "action": "DELIVERY TIMING: Pending. NOTES: Need EFW/AC to decide SGA.", 
                "interval": "Unknown", 
                "rule": "RATIONALE (Rule 1): SGA status unknown."
            }

    # --- SGA PATHWAY (EFW < 10th centile) ---
    
    # RULE 4: AREDV
    if ua_flow in ["absent", "reversed"]:
        if ua_flow == "reversed":
             action = f"DELIVERY TIMING: TERMINATE NOW. NOTES: Reversed flow in cord (AREDV) before 32 weeks: daily surveillance; deliver when ductus venosus becomes abnormal, and by 32 weeks anyway (consider 30-32); {steroids_text}; caesarean. Needs DV value -> ask for it."
        else:
             action = f"DELIVERY TIMING: TERMINATE NOW. NOTES: Absent flow in cord (AREDV), SGA, at {ga_weeks}w: daily surveillance; ductus venosus Doppler needed; delivery recommended now (by 32 weeks) after steroids; caesarean recommended. Most urgent level."
        return {
            "stage": "PATHOLOGICAL - Severe SGA with AREDV", 
            "action": action, 
            "interval": "Daily (DV Required)", 
            "rule": "RATIONALE (Rules 4, 6): High risk of fetal demise. Immediate termination via Caesarean indicated. Administer steroids if preterm."
        }
        
    # RULE 3 & 9: Elevated UA PI
    if metrics.get("ua_elevated"):
        return {
            "stage": "ABNORMAL - SGA with Elevated UA PI",
            "action": f"DELIVERY TIMING: Deliver no later than 37 weeks. NOTES: SGA with elevated UA PI: deliver no later than 37 weeks. {steroids_text if steroids_needed else ''}",
            "interval": "Twice weekly",
            "rule": "RATIONALE (Rules 3, 9): Abnormal resistance increases risk. Expedite delivery at early term. Induction can be offered with continuous HR monitoring."
        }

    # RULE 2 & 5: Normal UA Doppler
    if float(efw_percentile) < 3:
        action = f"DELIVERY TIMING: Offer delivery at 37 weeks. NOTES: Severe SGA (<3rd) with normal cord Doppler at {ga_weeks}w: more frequent surveillance may be appropriate; offer delivery at 37 weeks, senior obstetrician involved."
        interval = "Frequent (<14 days)"
    else:
        action = f"DELIVERY TIMING: Offer delivery at 37 weeks. NOTES: SGA (EFW <10th) with normal cord Doppler at {ga_weeks}w: repeat cord Doppler every 14 days; offer delivery at 37 weeks with a senior obstetrician involved."
        interval = "Every 14 days"
        
    return {
        "stage": "ABNORMAL - SGA (Normal UA)", 
        "action": action, 
        "interval": interval, 
        "rule": "RATIONALE (Rules 2, 5, 7, 8): Continued growth restriction requires early term delivery. MCA does not time preterm. Fluid/CTG are never sole surveillance. Uterine PI has limited value in 3rd trimester."
    }