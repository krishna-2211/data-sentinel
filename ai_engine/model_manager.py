import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
import google.generativeai as genai

class CleaningStep(BaseModel):
    """
    Represents a SINGLE, atomic action in the cleaning process.
    
    Why separate steps?
    So the user can un-check 'Step 2' without cancelling 'Step 1'.
    This enables the "Human-in-the-loop" architecture.
    """
    step_id: str = Field(
        ..., 
        description="Unique ID (e.g., 'step_1_impute_age'). Used by the UI to track selections."
    )
    description: str = Field(
        ..., 
        description="Human-readable explanation. This is what the User sees in the UI checklist."
    )
    code_snippet: str = Field(
        ..., 
        description="The actual Pandas code (e.g. `df['age'] = ...`). This is what gets sent to the Docker Sandbox."
    )
    required_libraries: List[str] = Field(
        ..., 
        description="Security check. We list what libs this specific step needs (e.g. ['numpy'])."
    )

class CleaningPlan(BaseModel):
    """
    Represents the FULL response from the AI.
    It contains the high-level logic (Pillar 1) and the list of steps (Pillar 3).
    """
    quality_score: int = Field(
        ..., 
        description="A score from 0-100 representing data health."
    )
    quality_verdict: str = Field(
        ..., 
        description="A 1-sentence executive summary (e.g., 'Your data is 80% clean...')."
    )
    action_summary: str = Field(
        ..., 
        description="A quick 1-sentence summary of the whole plan for the top of the dashboard."
    )
    reasoning_audit_log: str = Field(
        ..., 
        description="Pillar 1 (Value): The 'Why'. Explains the statistical reason for the choices (e.g., 'Chosen Median because...')."
    )
    risk_and_alternative_report: str = Field(
        ..., 
        description="Pillar 1 (Value): The 'Risk'. Explains what could go wrong (e.g., 'Risk: This might flatten distribution')."
    )
    target_columns: List[str] = Field(
        default_factory=list, 
        description="List of columns modified. Helps us highlight changes in the UI."
    )
    proposed_plan: List[CleaningStep] = Field(
        ..., 
        description="The list of atomic, approvable cleaning steps defined above."
    )

class ModelManager:
    def __init__(self):
        # 1. Get API Key
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
            
        # 2. Configure Gemini
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
            # 3. Initialize the Model
            # We use 'flash' because it is fast and cheap, perfect for iterating.
            # Later, we can swap this for 'pro' if we need more reasoning power.
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash-preview-09-2025', 
                # Just for getting the raw json response
                generation_config={"response_mime_type": "application/json"}
                )

    async def generate_cleaning_plan(self, data_profile: str) -> CleaningPlan:
        """
        The main function: Takes a Data Profile string (from Module 2),
        calls Gemini, and returns a structured CleaningPlan object.
        """
        
        if not self.api_key:
            raise ValueError("API Key is missing. Cannot call Gemini.")

        # --- STEP 1: The System Prompt (Prompt Engineering) ---
        system_prompt = f"""
        You are an expert Senior Data Scientist and Python Developer.
        Your task is to analyze the provided Data Quality Report (DQR) and generate a robust data cleaning plan.

        ### YOUR CONSTRAINTS (SECURITY & RELIABILITY):
        1. **Output Format:** You must return a valid JSON object matching the `CleaningPlan` schema exactly.
        2. **Library Allowlist:** You may ONLY use the following Python libraries: `pandas` (as pd), `numpy` (as np), and `scipy` (as scipy).
        3. **No Dangerous Code:** Do NOT use `os`, `sys`, `subprocess`, or file I/O operations.
        4. **Atomic Steps:** Break your plan into small, independent steps (e.g., separate imputation from type conversion).

        ### CRITICAL INSTRUCTION ON DATA QUALITY:
        - **IF THE DATA IS ALREADY CLEAN:** Do NOT invent problems. If missing values are 0%, types are correct, and outliers are minimal, there are no duplicate rows/columns, correlation is minimal between the numerical columns, return an **EMPTY** `proposed_plan`.
        - In `action_summary`, explicitly state: "The data appears clean. No automated actions required."
        - In `reasoning_audit_log`, explain that you verified the DQR and found no issues.

        ### SCORING CRITERIA:
        - 100: Perfect data.
        - 80-90: Minor issues (formatting, few missing values).
        - 50-70: Significant issues (skew, many missing values, outliers).
        - Below 50: Critical issues (wrong types, high redundancy, messy).

        ### OUTPUT REQUIREMENTS:
        - quality_score: An integer based on the criteria.
        - quality_verdict: A punchy summary: "Your data is [X]% clean. It needs [A, B, and C] adjustments to be production-ready."
        - If the data is clean, set quality_score to 100 and proposed_plan to [].

        ### YOUR ANALYSIS GOALS (PILLAR 1 - VALUE):
        1. **Audit Log:** In the `reasoning_audit_log`, clearly explain WHY you chose specific methods (e.g., "Chose Median imputation for Age because the DQR shows a skew of 2.5").
        2. **Risk Report:** In the `risk_and_alternative_report`, be honest about statistical risks (e.g., "Median imputation reduces variance") and suggest advanced alternatives (e.g., "KNN Imputation").

        ### CRITICAL REQUIREMENTS:
        1. You MUST populate EVERY field in the schema, including 'target_columns'.
        2. 'target_columns' must be a list of strings representing column names you are modifying.
        3. Only use pandas (pd) and numpy (np).
        4. Do not include any text outside the JSON object.

        ### THE DATA QUALITY REPORT (INPUT):
        {data_profile}
        """
        
        # --- STEP 2: Call the API ---
        try:
            # We pass 'response_schema' to force Pydantic structure
            response = self.model.generate_content(
                system_prompt,
                generation_config={
                    "response_mime_type": "application/json", 
                    "response_schema": CleaningPlan
                }
            )
            
            # --- STEP 3: Validate & Return ---
            # Using Pydantic to validate the JSON string immediately
            cleaning_plan = CleaningPlan.model_validate_json(response.text)
            return cleaning_plan

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise e
# --- Main Execution (For Testing) ---
if __name__ == "__main__":
    # This lets us verify the class loads correctly without running the full app.
    print("Model Manager initialized. Schema definitions loaded.")