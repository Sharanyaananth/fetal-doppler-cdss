# 🩺 Fetal Doppler Clinical Decision Support System (CDSS)

## What is this project doing?
This project is a deterministic, rule-based clinical decision-support engine designed to assist obstetricians in managing late-pregnancy fetal growth restriction (FGR). Developed for the **SwasthyaTech Synapse** grant prototype, it replaces manual chart lookups and guesswork with an instant, perfectly accurate computational pipeline. 

The system takes standard ultrasound measurements—such as Gestational Age, Estimated Fetal Weight (EFW), Amniotic Fluid, and Doppler Pulsatility Indices (PI) for four key blood vessels—and automatically maps them against **IRIA Samrakshan Indian reference charts**. It then applies the strict medical logic of the **FOGSI (GCPR 2022)** and **Barcelona FGR protocols** to instantly output the clinical risk stage, the required monitoring interval, and the exact recommended delivery week (including critical "Deliver NOW" alerts for severe pathological cases).

Crucially, this system operates **without black-box machine learning**. Every decision is 100% traceable to a specific medical rule, ensuring the transparency and reliability required for clinical safety.

## What is the content of this repository?
The project is modular, splitting the mathematical percentile calculations, the clinical rules, the user interface, and the reporting into distinct files.

```text
fetal-doppler-cdss/
│
├── app.py                      
│   # The main application file. It runs the Streamlit web dashboard, 
│   # providing tabs for manual patient data entry and historical record lookup.
│
├── modules/
│   ├── percentile_engine.py    
│   # The mathematical core. It safely handles dating discrepancies (LMP vs USG), 
│   # calculates the Cerebroplacental Ratio (CPR) and Mean Uterine PI, and compares 
│   # values against tabular reference charts to flag abnormalities.
│   │
│   ├── guideline_engine.py     
│   # The clinical brain. It takes the percentiles and fluid/EFW data to determine 
│   # if the pregnancy is Normal, Stage I (Abnormal), Stage II (AEDF), or Stage III (REDF), 
│   # and outputs strict delivery timelines.
│   │
│   └── report_generator.py     
│   # The document formatter. It dynamically builds a PCPNDT-compliant, 
│   # professional PDF lab report summarizing the clinical findings and delivery actions.
│
└── patient_database.json       
    # A lightweight, auto-generated local database. It is created the first time 
    # you save a patient record, allowing doctors to search and retrieve past visit data.
How to install and run the system
1. Prerequisites
You need Python 3.8 or newer installed on your computer.

2. Open Your Terminal
Open your computer's terminal or command prompt. If you are using an editor like VS Code, open the integrated terminal and ensure you are inside the fetal-doppler-cdss project folder.

3. Create a Virtual Environment (Recommended)
This keeps the project's libraries isolated from the rest of your computer.

Windows:

Bash
python -m venv venv
venv\Scripts\activate
Mac/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
(You will know this worked if you see (venv) appear on the left side of your terminal prompt).

4. Install Required Libraries
Run the following command to install the specific tools needed to run the dashboard and generate PDFs:

Bash
pip install streamlit fpdf2

5. Launch the Application
Run this final command to start the engine:

Bash
streamlit run app.py