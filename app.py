# import streamlit as st
# import pandas as pd
# import asyncio
# import requests
# import json
# from ai_engine.model_manager import ModelManager
# from ai_engine.profiler import generate_data_profile

# # --- CONFIGURATION ---
# RUNNER_URL = "http://127.0.0.1:8000/execute" 

# st.set_page_config(page_title="DataSentinel", layout="wide")
# st.title("🛡️ DataSentinel")
# st.markdown("### A Human-in-the-Loop Statistical Co-Pilot")

# # --- PERSISTENT STATE ---
# if "cleaning_plan" not in st.session_state:
#     st.session_state.cleaning_plan = None
# if "raw_df" not in st.session_state:
#     st.session_state.raw_df = None
# if "cleaned_df" not in st.session_state:
#     st.session_state.cleaned_df = None

# # --- SIDEBAR: Upload ---
# with st.sidebar:
#     st.header("Upload Data")
#     uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
#     if uploaded_file is not None:
#         new_df = pd.read_csv(uploaded_file)
#         if st.session_state.raw_df is None or not st.session_state.raw_df.equals(new_df):
#             st.session_state.raw_df = new_df
#             st.session_state.cleaning_plan = None
#             st.session_state.cleaned_df = None
#             st.rerun() # Force refresh on new upload
        
#         st.success(f"Loaded {len(st.session_state.raw_df)} rows.")
#         st.subheader("Data Preview")
#         st.dataframe(st.session_state.raw_df.head())

# # --- MAIN FLOW ---
# if st.session_state.raw_df is not None:
#     df = st.session_state.raw_df

#     st.header("AI Analysis & Strategy")
    
#     # Disable this button if we already have a plan to prevent double-clicking confusion
#     disable_analyze = st.session_state.cleaning_plan is not None
#     if st.button("🤖 Analyze & Generate Plan", disabled=disable_analyze):
#         with st.spinner("Consulting Gemini..."):
#             dqr = generate_data_profile(df)
#             try:
#                 manager = ModelManager()
#                 plan = asyncio.run(manager.generate_cleaning_plan(dqr))
#                 st.session_state.cleaning_plan = plan
#                 st.rerun() # Force refresh to show the plan cleanly
#             except Exception as e:
#                 st.error(f"Error: {e}")

#     # --- PHASE 2: HUMAN REVIEW ---
#     if st.session_state.cleaning_plan:
#         plan = st.session_state.cleaning_plan
        
#         st.subheader("Proposed Cleaning Plan")
        
#         # Only show the form if we haven't finished cleaning yet
#         if st.session_state.cleaned_df is None:
#             with st.form("approval_form"):
#                 st.markdown("##### Review the proposed steps:")
#                 selected_steps = []
#                 seen_step_ids = set()
                
#                 # 1. The Checklist (The "What")
#                 for step in plan.proposed_plan:
#                     if step.step_id in seen_step_ids:
#                         continue
#                     seen_step_ids.add(step.step_id)
                    
#                     col_check, col_code = st.columns([0.8, 0.2])
#                     with col_check:
#                         if st.checkbox(f"**{step.step_id}**: {step.description}", value=True):
#                             selected_steps.append(step)
#                     with col_code:
#                         with st.expander("View Code"):
#                             st.code(step.code_snippet, language='python')

#                 st.divider()
                
#                 # 2. The Context (The "Why" & "Risks") - Reordered & Prettier
#                 st.markdown("##### 🧠 Strategic Analysis")
#                 tab_why, tab_risk = st.tabs(["🔍 Audit Log (The Logic)", "⚠️ Risk Analysis (The Warning)"])
                
#                 with tab_why:
#                     st.success("Why were these steps chosen?")
#                     st.markdown(plan.reasoning_audit_log)
                    
#                 with tab_risk:
#                     st.warning("What are the statistical risks?")
#                     st.markdown(plan.risk_and_alternative_report)

#                 st.divider()

#                 # 3. Execution
#                 submitted = st.form_submit_button("🚀 Execute Approved Steps", type="primary")
                
#                 if submitted:
#                     if not selected_steps:
#                         st.warning("Select at least one step.")
#                     else:
#                         with st.spinner("Running in Sandbox..."):
#                             full_code = "\n".join([s.code_snippet for s in selected_steps])
#                             payload = {
#                                 "dataframe_json": df.to_json(orient="records"),
#                                 "code_snippet": full_code
#                             }
                            
#                             try:
#                                 response = requests.post(RUNNER_URL, json=payload)
#                                 if response.status_code == 200:
#                                     result = response.json()
#                                     if result.get("success"):
#                                         st.session_state.cleaned_df = pd.read_json(
#                                             result["cleaned_dataframe_json"], 
#                                             orient="records"
#                                         )
#                                         st.rerun()
#                                     else:
#                                         st.error(f"Execution Error: {result.get('error_message')}")
#                                 else:
#                                     st.error(f"Docker Error: {response.text}")
#                             except Exception as e:
#                                 st.error(f"Connection Error: {e}")
#         else:
#             st.info("✅ Execution Complete. See results below.")

#     # --- PHASE 3: RESULTS (Persistent) ---
#     if st.session_state.cleaned_df is not None:
#         st.divider()
#         st.header("Cleaned Data Results")
#         st.success("Cleaned Data is ready!")
#         st.dataframe(st.session_state.cleaned_df.head())
        
#         csv_data = st.session_state.cleaned_df.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label="Download Cleaned CSV",
#             data=csv_data,
#             file_name="cleaned_data.csv",
#             mime="text/csv",
#             key="download-persistent"
#         )
        
#         if st.button("Start Over"):
#             st.session_state.raw_df = None
#             st.session_state.cleaning_plan = None
#             st.session_state.cleaned_df = None
#             st.rerun()

import streamlit as st
import pandas as pd
import asyncio
import requests
import json
from ai_engine.model_manager import ModelManager
from ai_engine.profiler import generate_data_profile

# --- CONFIGURATION ---
RUNNER_URL = "http://127.0.0.1:8000/execute" 

st.set_page_config(page_title="DataSentinel", layout="wide", page_icon="🛡️")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #2ecc71;
    }
    .verdict-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ DataSentinel")

# --- PERSISTENT STATE ---
if "cleaning_plan" not in st.session_state: st.session_state.cleaning_plan = None
if "raw_df" not in st.session_state: st.session_state.raw_df = None
if "cleaned_df" not in st.session_state: st.session_state.cleaned_df = None
if "dqr_cache" not in st.session_state: st.session_state.dqr_cache = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Data Ingestion")
    uploaded_file = st.file_uploader("Upload Raw CSV", type=["csv"])
    if uploaded_file is not None:
        new_df = pd.read_csv(uploaded_file)
        if st.session_state.raw_df is None or not st.session_state.raw_df.equals(new_df):
            st.session_state.raw_df = new_df
            st.session_state.cleaning_plan = None
            st.session_state.cleaned_df = None
            st.session_state.dqr_cache = None
            st.rerun() # Force refresh on new upload
        
        st.success(f"Loaded {len(st.session_state.raw_df)} rows.")
        st.subheader("Data Preview")
        st.dataframe(st.session_state.raw_df.head())

# --- MAIN FLOW ---
if st.session_state.raw_df is not None:
    df = st.session_state.raw_df

    st.header("Analysis & Strategy")
    col_a, col_b = st.columns([0.2, 0.8])
    
    with col_a:
        if st.button("🤖 Analyze Data", disabled=st.session_state.cleaning_plan is not None, type="primary"):
            with st.spinner("Analyzing..."):
                dqr = generate_data_profile(df)
                st.session_state.dqr_cache = dqr
                manager = ModelManager()
                st.session_state.cleaning_plan = asyncio.run(manager.generate_cleaning_plan(dqr))
                st.rerun()
    
    with col_b:
        if st.session_state.dqr_cache:
            st.download_button("📄 Download DQR", st.session_state.dqr_cache, "dqr.txt")

    # --- RESULTS SECTION ---
    if st.session_state.cleaning_plan:
        plan = st.session_state.cleaning_plan
        
        st.divider()
        
        # --- NEW: QUALITY VERDICT & SCORE ---
        st.subheader("📊 Data Health Overview")
        c1, c2 = st.columns([0.3, 0.7])
        
        with c1:
            st.metric("Data Quality Score", f"{plan.quality_score}%")
            st.progress(plan.quality_score / 100)
            
        with c2:
            st.markdown(f'<div class="verdict-card"><b>AI Verdict:</b><br>{plan.quality_verdict}</div>', unsafe_allow_html=True)

        # --- STEPS & REVIEW ---
        if not plan.proposed_plan:
            st.success("✅ Your data is in great shape! No cleaning needed.")
        else:
            tab_steps, tab_logic, tab_risks = st.tabs(["📝 Cleaning Steps", "🔍 Reasoning", "⚠️ Risks"])
            
            with tab_logic: st.markdown(plan.reasoning_audit_log)
            with tab_risks: st.markdown(plan.risk_and_alternative_report)
            
            with tab_steps:
                if st.session_state.cleaned_df is None:
                    with st.form("clean_form"):
                        selected = []
                        for step in plan.proposed_plan:
                            if st.checkbox(f"**{step.step_id}**: {step.description}", value=True):
                                selected.append(step)
                        
                        if st.form_submit_button("🚀 Run Approved Cleaning", type="primary"):
                            with st.spinner("Executing..."):
                                code = "\n".join([s.code_snippet for s in selected])
                                res = requests.post(RUNNER_URL, json={
                                    "dataframe_json": df.to_json(orient="records"),
                                    "code_snippet": code
                                }).json()
                                if res.get("success"):
                                    st.session_state.cleaned_df = pd.read_json(res["cleaned_dataframe_json"], orient="records")
                                    st.rerun()
                                else:
                                    st.error(res.get("error_message"))
                else:
                    st.info("✅ Cleaning Complete.")

    # --- DOWNLOAD CLEANED DATA ---
    if st.session_state.cleaned_df is not None:
        st.divider()
        st.subheader("Cleaned Dataset")
        st.dataframe(st.session_state.cleaned_df.head())
        csv = st.session_state.cleaned_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Cleaned CSV", csv, "cleaned.csv", "text/csv", type="primary")
        if st.button("Start New Session"):
            st.session_state.clear()
            st.rerun()