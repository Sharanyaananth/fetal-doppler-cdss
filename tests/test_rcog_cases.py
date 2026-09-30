import pytest
from modules.percentile_engine import evaluate_percentiles
from modules.guideline_engine import evaluate_guideline_stage

# The 11 doctor-provided test cases (RCOG compliant)
TEST_CASES = [
    {"id": "R1-normal", "lmp": "33w2d", "usg": "32w0d", "efw": 22, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 1.17, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 3.01}]},
    {"id": "R2-caseA", "lmp": "36w0d", "usg": "33w0d", "efw": None, "fluid": "low", "vessels": [{"vessel": "umbilical_artery", "pi": 1.51, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.72}]},
    {"id": "R3-caseB", "lmp": "32w0d", "usg": "30w0d", "efw": None, "fluid": "low", "vessels": [{"vessel": "umbilical_artery", "pi": 1.62, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.15}]},
    {"id": "S1-missing-ua", "lmp": "34w0d", "usg": "34w0d", "efw": 40, "fluid": "normal", "vessels": [{"vessel": "mca", "pi": 1.8}]},
    {"id": "S2-absent-flow", "lmp": "32w0d", "usg": "30w0d", "efw": 2, "fluid": "low", "vessels": [{"vessel": "umbilical_artery", "pi": 1.9, "flow_between_beats": "absent"}, {"vessel": "mca", "pi": 1.1}]},
    {"id": "S3-reversed-flow", "lmp": "31w0d", "usg": "28w5d", "efw": 1, "fluid": "low", "vessels": [{"vessel": "umbilical_artery", "pi": 2.2, "flow_between_beats": "reversed"}, {"vessel": "mca", "pi": 1.0}]},
    {"id": "S4-term-40w", "lmp": "40w0d", "usg": "40w0d", "efw": 50, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 0.8, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.5}]},
    {"id": "S5-SGA", "lmp": "36w0d", "usg": "35w0d", "efw": 7, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 0.9, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.7}]},
    {"id": "S6-efw-below-3", "lmp": "36w0d", "usg": "34w3d", "efw": 2, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 0.9, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.7}]},
    {"id": "S7-age-gap-only", "lmp": "34w0d", "usg": "31w0d", "efw": None, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 0.95, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.85}]},
    {"id": "S8-bad-input", "lmp": "45w0d", "usg": "34w0d", "efw": 150, "fluid": "normal", "vessels": [{"vessel": "umbilical_artery", "pi": 15, "flow_between_beats": "present"}, {"vessel": "mca", "pi": 1.8}]}
]

def run_case(case):
    metrics = evaluate_percentiles(case.get("lmp"), case.get("usg"), case.get("vessels", []))
    return evaluate_guideline_stage(metrics, case.get("efw"), case.get("fluid"))

def test_r1_normal():
    res = run_case(TEST_CASES[0])
    assert "no SGA pathway action" in res.get("action", "")
    assert "check probe pressure" in res.get("action", "")

def test_r2_case_a():
    res = run_case(TEST_CASES[1])
    assert "SGA needs EFW" in res.get("action", "")
    assert "deliver no later than 37 weeks" in res.get("action", "")

def test_r3_case_b():
    res = run_case(TEST_CASES[2])
    assert "brain sparing" in res.get("action", "")
    assert "no later than 37 weeks" in res.get("action", "")

def test_s1_missing_ua():
    res = run_case(TEST_CASES[3])
    assert "Cannot assess cord Doppler: need umbilical artery PI. Must NOT say Normal" in res.get("action", "")

def test_s2_absent_flow():
    res = run_case(TEST_CASES[4])
    assert "Absent flow" in res.get("action", "")
    assert "caesarean recommended" in res.get("action", "")

def test_s3_reversed_flow():
    res = run_case(TEST_CASES[5])
    assert "Reversed flow" in res.get("action", "")
    assert "consider 30-32" in res.get("action", "")
    assert "caesarean" in res.get("action", "")

def test_s4_term():
    res = run_case(TEST_CASES[6])
    assert "Must NOT say 'rescan in 2-3 weeks'" in res.get("action", "")

def test_s5_sga():
    res = run_case(TEST_CASES[7])
    assert "repeat cord Doppler every 14 days" in res.get("action", "")

def test_s6_efw_below_3():
    res = run_case(TEST_CASES[8])
    assert "Severe SGA (<3rd)" in res.get("action", "")
    assert "offer delivery at 37 weeks" in res.get("action", "")

def test_s7_age_gap_only():
    res = run_case(TEST_CASES[9])
    assert "Need EFW/AC" in res.get("action", "")

def test_s8_bad_input():
    res = run_case(TEST_CASES[10])
    assert "Reject" in res.get("action", "")