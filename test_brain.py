import asyncio
import os
from ai_engine.model_manager import ModelManager

# --- MOCK DATA PROFILE ---
# This simulates what Module 1 (Profiling) would generate for a messy CSV.
MOCK_DQR = """
DATA QUALITY REPORT
-------------------
Total Rows: 1000
Columns: ['Age', 'Salary', 'Join_Date']

1. Column 'Age':
   - Missing Values: 200 (20%)
   - Data Type: float
   - Skew: 2.5 (Highly Right Skewed)
   - Outliers: Detected values > 90

2. Column 'Salary':
   - Missing Values: 0
   - Data Type: object (String)
   - Sample Values: ['$50,000', '$65,000', 'USD 40000']
   - Issue: Numeric data stored as messy strings.

3. Column 'Join_Date':
   - Missing Values: 5
   - Data Type: object (String)
   - Issue: Should be datetime.
"""

async def run_test():
    print("--- Starting Brain Test ---")
    
    # 1. Setup API Key (Replace 'YOUR_KEY_HERE' if not using env vars)
    # Ideally, set this in your terminal: export GEMINI_API_KEY="AIza..."
    os.environ["GEMINI_API_KEY"] = "AIzaSyCb_wCDFO42Ab6wPAnPmFUzKUtxO8DP6NI" 
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: Please set GEMINI_API_KEY environment variable.")
        return

    # 2. Initialize Brain
    manager = ModelManager()
    
    # 3. Ask for a plan
    print("Sending DQR to Gemini...")
    try:
        plan = await manager.generate_cleaning_plan(MOCK_DQR)
        
        # 4. Print Results
        print("\n--- SUCCESS! PLAN GENERATED ---")
        print(f"Summary: {plan.action_summary}")
        print(f"\nAudit Log (Why): {plan.reasoning_audit_log}")
        print(f"\nRisk Report (Analysis): {plan.risk_and_alternative_report}")
        
        print("\n--- Proposed Steps ---")
        for step in plan.proposed_plan:
            print(f"[ ] Step {step.step_id}: {step.description}")
            print(f"    Code: {step.code_snippet}")
            print(f"    Libs: {step.required_libraries}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())