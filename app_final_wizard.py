import streamlit as st
import os
import math
from io import StringIO

# ── Page Configuration & CSS ─────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="SMART CVD Risk Reduction")
st.markdown("""<style>
.header { position: sticky; top: 0; background: #f7f7f7; padding: 10px; display: flex; justify-content: flex-end; z-index: 100; }
.card { background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
</style>""", unsafe_allow_html=True)

# ── Header with Logo ──────────────────────────────────────────────────────────
st.markdown('<div class="header">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
else:
    st.warning("⚠️ Please upload 'logo.png' in the app directory.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Sidebar: Demographics & Risk Factors ───────────────────────────────────────
st.sidebar.header("Patient Demographics & Risk Factors")
age = st.sidebar.slider("Age (years)", 30, 90, 60, key="age")
sex = st.sidebar.radio("Sex", ["Male", "Female"], key="sex")
weight = st.sidebar.number_input("Weight (kg)", 40.0, 200.0, 75.0, key="weight")
height = st.sidebar.number_input("Height (cm)", 140.0, 210.0, 170.0, key="height")
bmi = weight / ((height / 100) ** 2)
st.sidebar.markdown(f"**BMI:** {bmi:.1f} kg/m²")
smoker = st.sidebar.checkbox("Current smoker", key="smoker")
diabetes = st.sidebar.checkbox("Diabetes", key="diabetes")
st.sidebar.markdown("**Vascular Disease (select all that apply)**")
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
def fmt(x):
    return f"{x:.1f}%"

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
with st.expander("Therapies"):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Pre-admission Lipid-Lowering")
    pre_stat = st.selectbox("Statin", ["None", "Atorvastatin 80 mg", "Rosuvastatin 20 mg"], key="ther_pre_stat")
    pre_ez = st.checkbox("Ezetimibe 10 mg", key="ther_pre_ez")
    pre_bemp = st.checkbox("Bempedoic acid", key="ther_pre_bemp")
    st.markdown("---")
    st.subheader("Initiate/Intensify Therapy")
    new_stat = st.selectbox("Statin change", ["None", "Atorvastatin 80 mg", "Rosuvastatin 20 mg"], key="ther_new_stat")
    new_ez = st.checkbox("Add Ezetimibe", key="ther_new_ez")
    new_bemp = st.checkbox("Add Bempedoic acid", key="ther_new_bemp")
    post_ldl = ldl
    reductions = {"Atorvastatin 80 mg":0.50, "Rosuvastatin 20 mg":0.55, "Ezetimibe 10 mg":0.20, "Bempedoic acid":0.18}
    for drug in [pre_stat, new_stat]:
        if drug in reductions:
            post_ldl *= (1 - reductions[drug])
    if pre_ez or new_ez:
        post_ldl *= (1 - reductions["Ezetimibe 10 mg"])
    if pre_bemp or new_bemp:
        post_ldl *= (1 - reductions["Bempedoic acid"])
    post_ldl = max(post_ldl, 0.5)
    pcsk9 = st.checkbox("PCSK9 inhibitor", key="ther_pcsk9", disabled=(post_ldl <= 1.8), help="FOURIER trial")
    inclis = st.checkbox("Inclisiran", key="ther_inclis", disabled=(post_ldl <= 1.8), help="ORION-10 trial")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Main: Results & Recommendations ────────────────────────────────────────────
with st.expander("Results & Recommendations"):
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
