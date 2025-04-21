
import streamlit as st
import os
import math
from io import StringIO

# ── Configuration & CSS ───────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="SMART CVD Risk Reduction")
st.markdown("""
<style>
.header { position: sticky; top: 0; background: #f7f7f7; padding: 10px; display: flex; justify-content: flex-end; z-index: 100; }
.expander { margin-bottom: 20px; }
.button-container { display: flex; justify-content: space-between; margin-top: 10px; }
.bar-chart { margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ── Header with Logo ──────────────────────────────────────────────────────────
st.markdown('<div class="header">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)
else:
    st.warning("⚠️ Please upload 'logo.png' in the app directory.")
st.markdown('</div>', unsafe_allow_html=True)

# ── Wizard Step State ─────────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 0

def next_step():
    if st.session_state.step < 3:
        st.session_state.step += 1

def prev_step():
    if st.session_state.step > 0:
        st.session_state.step -= 1

# ── Trial Evidence Links ─────────────────────────────────────────────────────
TRIALS = {
    "Atorvastatin": ("CTT meta-analysis", "https://pubmed.ncbi.nlm.nih.gov/20167315/"),
    "Rosuvastatin": ("CTT meta-analysis", "https://pubmed.ncbi.nlm.nih.gov/20167315/"),
    "Ezetimibe":     ("IMPROVE-IT",         "https://pubmed.ncbi.nlm.nih.gov/26405142/"),
    "Bempedoic":     ("CLEAR Outcomes",     "https://pubmed.ncbi.nlm.nih.gov/35338941/"),
    "PCSK9":         ("FOURIER",            "https://pubmed.ncbi.nlm.nih.gov/28436927/"),
    "Inclisiran":    ("ORION-10",           "https://pubmed.ncbi.nlm.nih.gov/32302303/"),
    "Icosapent":     ("REDUCE-IT",          "https://pubmed.ncbi.nlm.nih.gov/31141850/"),
    "GLP1":          ("STEP",               "https://pubmed.ncbi.nlm.nih.gov/34499685/")
}

# ── Risk Calculation Functions ───────────────────────────────────────────────
def estimate_10y(age, sex, sbp, tc, hdl, smoker, dm, egfr, crp, vasc):
    sex_v = 1 if sex=="Male" else 0
    sm_v  = 1 if smoker else 0
    dm_v  = 1 if dm else 0
    crp_l = math.log(crp+1)
    lp = (0.064*age + 0.34*sex_v + 0.02*sbp + 0.25*tc - 0.25*hdl
          + 0.44*sm_v + 0.51*dm_v - 0.2*(egfr/10) + 0.25*crp_l + 0.4*vasc)
    raw = 1 - 0.900**math.exp(lp-5.8)
    return min(raw*100, 95.0)

def convert_5yr(r10):
    p = min(r10,95.0)/100
    return min((1-(1-p)**0.5)*100,95.0)

def estimate_lt(age, r10):
    years = max(85-age,0)
    p10 = min(r10,95.0)/100
    annual = 1-(1-p10)**(1/10)
    return min((1-(1-annual)**years)*100,95.0)

def fmt(x):
    return f"{x:.1f}%"

# ── Initialize Defaults ───────────────────────────────────────────────────────
defaults = {
    'age':60, 'sex':'Male', 'weight':75, 'height':170,
    'smoker':False, 'diabetes':False, 'egfr':90,
    'tc':5.2, 'hdl':1.3, 'ldl':3.0, 'crp':2.5,
    'hba1c':7.0, 'tg':1.2,
    'pre_stat':'None','pre_ez':False,'pre_bemp':False,
    'new_stat':'None','new_ez':False,'new_bemp':False,
    'sbp':140
}
for key,val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Step 1: Profile ───────────────────────────────────────────────────────────
with st.expander("Step 1: Patient Profile", expanded=(st.session_state.step==0)):
    st.session_state.age = st.number_input("Age (years)", 30, 90, st.session_state.age)
    st.session_state.sex = st.selectbox("Sex", ["Male","Female"], index=0 if st.session_state.sex=="Male" else 1)
    st.session_state.weight = st.number_input("Weight (kg)", 40, 200, st.session_state.weight)
    st.session_state.height = st.number_input("Height (cm)", 140, 210, st.session_state.height)
    bmi = st.session_state.weight/((st.session_state.height/100)**2)
    st.write(f"**BMI:** {bmi:.1f}")
    st.session_state.smoker = st.checkbox("Current smoker", st.session_state.smoker, help="Tobacco increases CVD risk")
    st.session_state.diabetes = st.checkbox("Diabetes", st.session_state.diabetes, help="Diabetes increases CVD risk")
    st.session_state.egfr = st.slider("eGFR (mL/min/1.73m²)", 15, 120, st.session_state.egfr)
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    st.button("Next", on_click=next_step)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Step 2: Labs ──────────────────────────────────────────────────────────────
with st.expander("Step 2: Laboratory Results", expanded=(st.session_state.step==1)):
    st.session_state.tc = st.number_input("Total Cholesterol (mmol/L)", 2.0, 10.0, st.session_state.tc)
    st.session_state.hdl = st.number_input("HDL-C (mmol/L)", 0.5, 3.0, st.session_state.hdl)
    st.session_state.ldl = st.number_input("LDL-C (mmol/L)", 0.5, 6.0, st.session_state.ldl)
    st.session_state.crp = st.number_input("hs-CRP (mg/L)", 0.1, 20.0, st.session_state.crp, help=f"{TRIALS['Icosapent'][0]}: {TRIALS['Icosapent'][1]}")
    st.session_state.hba1c = st.number_input("HbA1c (%)", 4.0, 14.0, st.session_state.hba1c, help=f"{TRIALS['GLP1'][0]}: {TRIALS['GLP1'][1]}")
    st.session_state.tg = st.number_input("Triglycerides (mmol/L)", 0.3, 5.0, st.session_state.tg)
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    st.button("Back", on_click=prev_step)
    st.button("Next", on_click=next_step)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Step 3: Therapies ─────────────────────────────────────────────────────────
with st.expander("Step 3: Therapies", expanded=(st.session_state.step==2)):
    st.session_state.pre_stat = st.selectbox("Pre-admission Statin", ["None","Atorvastatin","Rosuvastatin"], index=0)
    st.session_state.pre_ez = st.checkbox("Pre-admission Ezetimibe", st.session_state.pre_ez)
    st.session_state.pre_bemp = st.checkbox("Pre-admission Bempedoic acid", st.session_state.pre_bemp)
    st.markdown("---")
    st.session_state.new_stat = st.selectbox("Initiate/Intensify Statin", ["None","Atorvastatin","Rosuvastatin"], index=0)
    st.session_state.new_ez = st.checkbox("Add Ezetimibe", st.session_state.new_ez)
    st.session_state.new_bemp = st.checkbox("Add Bempedoic acid", st.session_state.new_bemp)
    # Gating
    pre_list = [st.session_state.pre_stat] if st.session_state.pre_stat!="None" else []
    if st.session_state.pre_ez: pre_list.append("Ezetimibe")
    if st.session_state.pre_bemp: pre_list.append("Bempedoic")
    new_list = [st.session_state.new_stat] if st.session_state.new_stat!="None" else []
    if st.session_state.new_ez: new_list.append("Ezetimibe")
    if st.session_state.new_bemp: new_list.append("Bempedoic")
    post_ldl = calculate_ldl_projection(st.session_state.ldl, pre_list, new_list)
    st.session_state.pcsk9 = st.checkbox("PCSK9 inhibitor", st.session_state.pcsk9, disabled=(post_ldl<=1.8))
    st.session_state.inclis = st.checkbox("Inclisiran", st.session_state.inclis, disabled=(post_ldl<=1.8))
    st.markdown('<div class="button-container">', unsafe_allow_html=True)
    st.button("Back", on_click=prev_step)
    st.button("Next", on_click=next_step)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Step 4: Results ───────────────────────────────────────────────────────────
with st.expander("Step 4: Results & Recommendations", expanded=(st.session_state.step==3)):
    vasc = len([x for x in [st.session_state.pre_stat!="None", st.session_state.pre_ez, st.session_state.pre_bemp] if x])
    r10 = estimate_10y(st.session_state.age, st.session_state.sex, st.session_state.sbp,
                       st.session_state.tc, st.session_state.hdl, st.session_state.smoker,
                       st.session_state.diabetes, st.session_state.egfr, st.session_state.crp, vasc)
    r5  = convert_5yr(r10)
    lt  = estimate_lt(st.session_state.age, r10) if st.session_state.age<85 else None
    st.write(f"5‑yr: **{fmt(r5)}**, 10‑yr: **{fmt(r10)}**, Lifetime: **{fmt(lt) if lt else 'N/A'}**")
    # Chart
    data = {'5‑yr': r5, '10‑yr': r10}
    if lt is not None: data['Lifetime'] = lt
    st.bar_chart(data)
    # ARR/RRR/NNT
    if lt is not None:
        arr = r10 - lt
        rrr = arr / r10 * 100 if r10 else 0
        nnt = 100 / arr if arr else None
        st.write(f"ARR (10y): **{arr:.1f}pp**, RRR: **{rrr:.1f}%**, NNT: **{nnt:.0f}**")
    else:
        st.write("ARR/RRR/NNT: N/A for age ≥85")
    # CSV Export
    csv = StringIO()
    csv.write('metric,value\n')
    csv.write(f'5yr,{r5:.1f}\n10yr,{r10:.1f}\n')
    if lt is not None: csv.write(f'lifetime,{lt:.1f}\n')
    st.download_button("Download Results (CSV)", csv.getvalue(), "cvd_results.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)
