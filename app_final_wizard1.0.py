import streamlit as st
import os
import math
from io import StringIO

# ── Page Configuration & CSS ─────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="SMART CVD Risk Reduction")
# Custom styling including watermark, header, and cards
st.markdown('''<style>
  .stApp::before {
    content: "";
    background: url(logo.png) no-repeat center center;
    background-size: 200px 200px;
    opacity: 0.1;
    position: absolute;
    top: 20%; left: 50%; transform: translate(-50%, -50%);
    z-index: 0;
  }
  .header {
    position: sticky; top: 0;
    background: #f7f7f7;
    padding: 10px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    z-index: 100;
  }
  .card {
    background: #fff;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    position: relative;
    z-index: 1;
  }
  /* Remove default expander borders */
  .streamlit-expanderHeader {
    border: none;
  }
''', unsafe_allow_html=True)

# ── Header with compact logo ─────────────────────────────────────────────────
st.markdown('<div class="header">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=150, use_column_width=False)
else:
    st.warning("⚠️ Please upload 'logo.png' in the app directory.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Sidebar: Demographics & Risk Factors ───────────────────────────────────────
st.sidebar.header("Patient Demographics")
age = st.sidebar.slider("Age (years)", 30, 90, 60, key="age")
sex = st.sidebar.radio("Sex", ["Male", "Female"], key="sex")
weight = st.sidebar.number_input("Weight (kg)", 40.0, 200.0, 75.0, key="weight")
height = st.sidebar.number_input("Height (cm)", 140.0, 210.0, 170.0, key="height")
bmi = weight / ((height / 100) ** 2)
st.sidebar.markdown(f"**BMI:** {bmi:.1f} kg/m²")

st.sidebar.header("Risk Factors")
smoker = st.sidebar.checkbox("Current smoker", key="smoker")
diabetes = st.sidebar.checkbox("Diabetes", key="diabetes")
st.sidebar.write("Known vascular disease in the following territories:")
vasc_cor = st.sidebar.checkbox("Coronary artery disease", key="vasc_cor")
vasc_cer = st.sidebar.checkbox("Cerebrovascular disease", key="vasc_cer")
vasc_per = st.sidebar.checkbox("Peripheral artery disease", key="vasc_per")
vasc_count = sum([vasc_cor, vasc_cer, vasc_per])
egfr = st.sidebar.slider("eGFR (mL/min/1.73 m²)", 15, 120, 90, key="egfr")

# ── Risk Calculation Functions ─────────────────────────────────────────────────
def estimate_10y_risk(age, sex, sbp, tc, hdl, smoker, diabetes, egfr, crp, vasc):
    sex_v = 1 if sex == "Male" else 0
    sm_v = 1 if smoker else 0
    dm_v = 1 if diabetes else 0
    crp_l = math.log(crp + 1)
    lp = (0.064 * age + 0.34 * sex_v + 0.02 * sbp + 0.25 * tc
          - 0.25 * hdl + 0.44 * sm_v + 0.51 * dm_v
          - 0.2 * (egfr / 10) + 0.25 * crp_l + 0.4 * vasc)
    raw = 1 - 0.900 ** math.exp(lp - 5.8)
    return min(raw * 100, 95.0)

def convert_5yr(r10):
    p = min(r10, 95.0) / 100
    return min((1 - (1 - p) ** 0.5) * 100, 95.0)

def estimate_lifetime_risk(age, r10):
    years = max(85 - age, 0)
    p10 = min(r10, 95.0) / 100
    annual = 1 - (1 - p10) ** (1 / 10)
    return min((1 - (1 - annual) ** years) * 100, 95.0)

# Formatting helper
def fmt(x): return f"{x:.1f}%"

# ── Main: Laboratory Results ───────────────────────────────────────────────────
with st.expander("Laboratory Results", expanded=True):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    total_chol = st.number_input("Total Cholesterol (mmol/L)", 2.0, 10.0, 5.2, 0.1, key="lab_tc")
    hdl = st.number_input("HDL-C (mmol/L)", 0.5, 3.0, 1.3, 0.1, key="lab_hdl")
    ldl = st.number_input("LDL-C (mmol/L)", 0.5, 6.0, 3.0, 0.1, key="lab_ldl")
    crp = st.number_input("hs-CRP (mg/L)", 0.1, 20.0, 2.5, 0.1, key="lab_crp")
    hba1c = st.number_input("HbA1c (%)", 4.0, 14.0, 7.0, 0.1, key="lab_hba1c")
    tg = st.number_input("Triglycerides (mmol/L)", 0.3, 5.0, 1.2, 0.1, key="lab_tg")
    sbp = st.number_input("Current SBP (mmHg)", 80, 220, 140, key="lab_sbp")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Main: Therapies ───────────────────────────────────────────────────────────
with st.expander("Therapies", expanded=True):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Pre-admission Lipid-Lowering Therapy")
    # Pre-admission lipid therapies - tick all that apply
    pre_simv_low = st.checkbox("Simvastatin 20 mg", key="pre_simv_low")
    pre_simv_high = st.checkbox("Simvastatin 40 mg", key="pre_simv_high")
    pre_atorva_low = st.checkbox("Atorvastatin 10 mg", key="pre_atorva_low")
    pre_atorva_high = st.checkbox("Atorvastatin 80 mg", key="pre_atorva_high")
    pre_rosu_low = st.checkbox("Rosuvastatin 5 mg", key="pre_rosu_low")
    pre_rosu_high = st.checkbox("Rosuvastatin 20 mg", key="pre_rosu_high")
    pre_ez = st.checkbox("Ezetimibe 10 mg", key="pre_ez")
    pre_bemp = st.checkbox("Bempedoic acid", key="pre_bemp")
    pre_pcsk9 = st.checkbox("PCSK9 inhibitor", key="pre_pcsk9")
    pre_sirna = st.checkbox("siRNA", key="pre_sirna")
    st.markdown("---")
    st.subheader("New / Intensified Lipid-Lowering Therapy")
    new_simv_low = st.checkbox("Start Simvastatin 20 mg", key="new_simv_low")
    new_simv_high = st.checkbox("Start Simvastatin 40 mg", key="new_simv_high")
    new_atorva_low = st.checkbox("Start Atorvastatin 10 mg", key="new_atorva_low")
    new_atorva_high = st.checkbox("Start Atorvastatin 80 mg", key="new_atorva_high")
    new_rosu_low = st.checkbox("Start Rosuvastatin 5 mg", key="new_rosu_low")
    new_rosu_high = st.checkbox("Start Rosuvastatin 20 mg", key="new_rosu_high")
    new_ez = st.checkbox("Add Ezetimibe 10 mg", key="new_ez")
    new_bemp = st.checkbox("Add Bempedoic acid", key="new_bemp")
    # Calculate post-LDL considering pre and new therapies
    therapies = []
    # mapping efficacy
    E = {"Simvastatin 20 mg":0.1,"Simvastatin 40 mg":0.2,
         "Atorvastatin 10 mg":0.3,"Atorvastatin 80 mg":0.5,
         "Rosuvastatin 5 mg":0.25,"Rosuvastatin 20 mg":0.55,
         "Ezetimibe 10 mg":0.2,"Bempedoic acid":0.18,
         "PCSK9 inhibitor":0.6,"siRNA":0.55}
    # collect pre therapies
    for name, flag in [("Simvastatin 20 mg", pre_simv_low),("Simvastatin 40 mg", pre_simv_high),
                       ("Atorvastatin 10 mg", pre_atorva_low),("Atorvastatin 80 mg", pre_atorva_high),
                       ("Rosuvastatin 5 mg", pre_rosu_low),("Rosuvastatin 20 mg", pre_rosu_high),
                       ("Ezetimibe 10 mg", pre_ez),("Bempedoic acid", pre_bemp),
                       ("PCSK9 inhibitor", pre_pcsk9),("siRNA", pre_sirna)]:
        if flag:
            therapies.append(name)
    # collect new therapies
    for name, flag in [("Simvastatin 20 mg", new_simv_low),("Simvastatin 40 mg", new_simv_high),
                       ("Atorvastatin 10 mg", new_atorva_low),("Atorvastatin 80 mg", new_atorva_high),
                       ("Rosuvastatin 5 mg", new_rosu_low),("Rosuvastatin 20 mg", new_rosu_high),
                       ("Ezetimibe 10 mg", new_ez),("Bempedoic acid", new_bemp)]:
        if flag:
            therapies.append(name)
    # baseline
    post_ldl = ldl
    for t in therapies:
        post_ldl *= (1 - E.get(t,0))
    post_ldl = max(post_ldl,0.5)
    # gated PCSK9i and siRNA
    pcsk9_allowed = post_ldl > 1.8
    sirna_allowed = post_ldl > 1.8
    if not pcsk9_allowed:
        st.info("PCSK9 inhibitors only if LDL >1.8 mmol/L post-therapy.")
    if not sirna_allowed:
        st.info("siRNA only if LDL >1.8 mmol/L post-therapy.")
    st.markdown('</div>', unsafe_allow_html=True), expanded=False):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    vasc = vasc_count
    r10 = estimate_10y_risk(age, sex, sbp, total_chol, hdl, smoker, diabetes, egfr, crp, vasc)
    r5 = convert_5yr(r10)
    lt = estimate_lifetime_risk(age, r10) if age < 85 else None
    st.subheader("Risk Estimates")
    if lt is not None:
        st.write(f"5‑year: **{fmt(r5)}**, 10‑year: **{fmt(r10)}**, Lifetime (to 85): **{fmt(lt)}**")
    else:
        st.write(f"5‑year: **{fmt(r5)}**, 10‑year: **{fmt(r10)}**, Lifetime: **N/A**")
    chart_data = {"5‑year": [r5], "10‑year": [r10]}
    if lt is not None:
        chart_data["Lifetime"] = [lt]
    st.bar_chart(chart_data)
    st.write("**ARR/RRR/NNT**:")
    if lt is not None:
        arr = r10 - lt
        rrr = arr / r10 * 100 if r10 else 0
        nnt = 100 / arr if arr else None
        st.write(f"ARR: {arr:.1f} pp, RRR: {rrr:.1f}%, NNT: {nnt:.0f}")
    else:
        st.write("Not applicable for age ≥ 85")
    csv = StringIO()
    csv.write("Metric,Value\n")
    csv.write(f"5yr,{r5:.1f}\n10yr,{r10:.1f}\n")
    if lt is not None:
        csv.write(f"Lifetime,{lt:.1f}\n")
    st.download_button("Download Results (CSV)", csv.getvalue(), "cvd_results.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("Created by Samuel Panday — 21/04/2025")
st.markdown("PRIME team, King's College Hospital")
st.markdown("For informational purposes; not a substitute for medical advice.")
"""

# Write to file
file_path = Path("/mnt/data/app_final_wizard.py")
file_path.write_text(script)

# Return path
file_path
