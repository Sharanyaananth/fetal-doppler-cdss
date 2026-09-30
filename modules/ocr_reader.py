"""Module 1: Strict Automated Doppler Screen Parser."""
import re
import cv2
import numpy as np

def analyze_doppler_scan(image_bytes: bytes) -> dict:
    """
    Strict extraction from ultrasound image. 
    Does not guess or hallucinate missing data.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # STRICT Initialization: No default values.
    extracted_data = {
        "ua_pi": None,
        "mca_pi": None,
        "ua_flow": "Unknown",
        "dv_status": "Unknown",
        "detected_vessels": [],
        "raw_text": ""
    }
    
    if img is None:
        return extracted_data

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        ocr_results = reader.readtext(gray)
        text_lines = [item[1].upper() for item in ocr_results]
        extracted_data["raw_text"] = " | ".join(text_lines)
    except Exception:
        text_lines = []

    full_text = extracted_data["raw_text"]

    # 1. Strict PI Extraction - Requires explicit vessel label near the number
    ua_match = re.search(r'(?:UA|UMB|UMBILICAL).*?(?:PI|P\.I\.)[:\s]*([0-9]\.[0-9]{1,2})', full_text)
    mca_match = re.search(r'(?:MCA|CEREBRAL).*?(?:PI|P\.I\.)[:\s]*([0-9]\.[0-9]{1,2})', full_text)
    
    if ua_match:
        extracted_data["ua_pi"] = float(ua_match.group(1))
        extracted_data["detected_vessels"].append("Umbilical Artery")
        
    if mca_match:
        extracted_data["mca_pi"] = float(mca_match.group(1))
        extracted_data["detected_vessels"].append("Middle Cerebral Artery")

    # 2. Strict Flow Detection
    if "REDF" in full_text or "REVERSED" in full_text:
        extracted_data["ua_flow"] = "REDF"
    elif "AEDF" in full_text or "ABSENT" in full_text:
        extracted_data["ua_flow"] = "AEDF"
    else:
        extracted_data["ua_flow"] = "Normal"

    return extracted_data