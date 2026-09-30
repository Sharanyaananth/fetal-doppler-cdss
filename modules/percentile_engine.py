"""Module 2: Percentile & Ratio Calculation Engine (Tabular)."""

# Tabular data representing IRIA Samrakshan / Published Charts
# Values are approx 95th centile for UA/UtA, 5th centile for MCA/CPR
CHART_TABLE = {
    30: {"ua_p95": 1.31, "mca_p5": 1.20, "ut_p95": 1.05, "cpr_p5": 1.08},
    31: {"ua_p95": 1.28, "mca_p5": 1.18, "ut_p95": 1.03, "cpr_p5": 1.08},
    32: {"ua_p95": 1.25, "mca_p5": 1.15, "ut_p95": 1.00, "cpr_p5": 1.08},
    33: {"ua_p95": 1.22, "mca_p5": 1.12, "ut_p95": 0.98, "cpr_p5": 1.08},
    36: {"ua_p95": 1.10, "mca_p5": 1.05, "ut_p95": 0.90, "cpr_p5": 1.08},
    40: {"ua_p95": 1.00, "mca_p5": 1.00, "ut_p95": 0.85, "cpr_p5": 1.08},
}

def parse_weeks(week_str: str) -> int:
    """Parses '32w0d' to integer 32."""
    if not week_str: return 0
    return int(str(week_str).lower().split('w')[0])

def evaluate_percentiles(weeks_lmp_str: str, weeks_usg_str: str, vessels: list):
    w_lmp = parse_weeks(weeks_lmp_str)
    w_usg = parse_weeks(weeks_usg_str)
    
    # Dating Logic: Flag >= 2 weeks, always use LMP/Early USG for charts
    dating_diff = abs(w_lmp - w_usg)
    is_discrepancy = dating_diff >= 2
    clinical_weeks = w_lmp if w_lmp > 0 else w_usg
    
    # Get closest chart week safely
    if clinical_weeks < min(CHART_TABLE.keys()): chart_week = min(CHART_TABLE.keys())
    elif clinical_weeks > max(CHART_TABLE.keys()): chart_week = max(CHART_TABLE.keys())
    else: chart_week = min(CHART_TABLE.keys(), key=lambda k: abs(k - clinical_weeks))
    
    thresholds = CHART_TABLE[chart_week]
    
    # Extract vessel values from the JSON structure
    ua_pi = next((v['pi'] for v in vessels if v['vessel'] == 'umbilical_artery'), None)
    mca_pi = next((v['pi'] for v in vessels if v['vessel'] == 'mca'), None)
    ut_r = next((v['pi'] for v in vessels if v['vessel'] == 'uterine_right'), None)
    ut_l = next((v['pi'] for v in vessels if v['vessel'] == 'uterine_left'), None)
    ua_flow = next((v.get('flow_between_beats', 'present') for v in vessels if v['vessel'] == 'umbilical_artery'), 'present')
    
    cpr = round(mca_pi / ua_pi, 2) if mca_pi and ua_pi else None
    
    mean_ut_pi = None
    if ut_r is not None and ut_l is not None:
        mean_ut_pi = round((ut_r + ut_l) / 2, 2)
    elif ut_r is not None:
        mean_ut_pi = ut_r
    elif ut_l is not None:
        mean_ut_pi = ut_l
        
    return {
        "clinical_weeks": clinical_weeks,
        "is_discrepancy": is_discrepancy,
        "ua_pi": ua_pi,
        "mca_pi": mca_pi,
        "mean_ut_pi": mean_ut_pi,
        "cpr": cpr,
        "ua_flow": ua_flow,
        "ua_elevated": ua_pi > thresholds["ua_p95"] if ua_pi else False,
        "mca_low": mca_pi < thresholds["mca_p5"] if mca_pi else False,
        "ut_elevated": mean_ut_pi > thresholds["ut_p95"] if mean_ut_pi else False,
        "brain_sparing": cpr < thresholds["cpr_p5"] if cpr else False
    }