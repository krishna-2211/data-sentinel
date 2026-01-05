import uvicorn # The server that will run our FastAPI app
from fastapi import FastAPI, HTTPException # The framework for building our API
from pydantic import BaseModel, Field # For data validation and defining our "API Contract"
# --- Data Science "Allowlist" Imports ---
# These are the ONLY libraries we will let the LLM's code use.
import pandas as pd
import numpy as np
import scipy
import scipy.stats
# --- Standard Utility Imports ---
import io    # Used to "trick" pandas into reading a string as if it were a file
import json    # Used for handling JSON data (though FastAPI does most of this)


class ExecutionRequest(BaseModel):
    """
    Defines the shape of the data we EXPECT TO RECEIVE from our main agent.
    FastAPI will automatically validate the incoming request against this shape.
    If it's wrong (e.g., 'code_snippet' is missing), FastAPI sends an error.
    """
    # The '...' (ellipsis) means this field is REQUIRED.
    dataframe_json: str = Field(..., description="...")
    code_snippet: str = Field(..., description="...")
    # In a future step, we could add 'required_libraries' here to double-check.

class ExecutionResponse(BaseModel):
    """
    Defines the shape of the data we PROMISE TO SEND BACK.
    Our main agent will know it can always expect this format.
    """
    # We use '| None' to say this field is "optional" (it will be 'None' on failure)
    cleaned_dataframe_json: str | None = Field(default=None, description="...")
    
    # These fields are required for our main agent's logic.
    success: bool
    error_message: str | None = Field(default=None, description="...")

# This line creates the actual web application. (FastAPI Application Instance)
app = FastAPI(
    title="Secure Code Runner Service",
    description="Executes data cleaning code in a sandboxed environment..."
)

# This function builds the "secure jail" for the LLM's code.
def create_execution_environment(df_in: pd.DataFrame) -> dict:
    """
    Prepares the safe execution environment (the "sandbox") for the exec() call.

    This is the HEART of Pillar 4: Security.
    
    It returns a dictionary that tells exec() *exactly* what variables and
    modules the code is allowed to see.
    """

    # 1. Create a "safelist" of built-in functions we will allow.
    #    We EXCLUDE 'import', 'open', 'eval', 'exec', etc.
    safe_builtins = {
        "print": print,
        "range": range,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "abs": abs,
        "max": max,
        "min": min,
        "sum": sum,
        "round": round,
        "True": True,
        "False": False,
        "None": None,
        # We can add more safe functions as needed (e.g., 'zip', 'enumerate')
    }

    # Create a *copy* of the DataFrame. This is a safety measure to
    # prevent any weird side-effects on the original object.
    df = df_in.copy()
    
    # This is our "allowlist." The executed code will ONLY be able
    # to see and use what is in this dictionary.
    safe_globals = {
        "__builtins__": safe_builtins,
        "pd": pd,
        "np": np,
        "scipy": scipy,
        "df": df,
    }
    
    # Why pass this dict for BOTH globals and locals?
    # We are telling exec(): "Use this ONE dictionary for everything.
    # Read from it (globals) and write any changes back INTO it (locals)."
    # This is how we'll get the modified 'df' back after exec() runs.
    return {"globals": safe_globals, "locals": safe_globals}


# === The API Endpoint (The "Front Door") ===
# This is the "page" or "URL" that our main agent will send its request to.
@app.post("/execute", response_model=ExecutionResponse)
async def execute_cleaning_code(request: ExecutionRequest):
    """
    This is the main function for our API. It will be triggered
    every time a POST request hits the '/execute' URL.
    
    FastAPI does a lot for us here:
    1. '@app.post("/execute")': Registers this function as a POST endpoint at '/execute'.
    2. 'response_model=ExecutionResponse': Tells FastAPI to validate our *return* value.
    3. 'request: ExecutionRequest': Tells FastAPI to validate the *incoming* data.
    """

    # --- STEP 1: Deserialize the input DataFrame ---
    # The 'request.dataframe_json' is just a string. We need to turn it
    # back into a real Pandas DataFrame.
    print("--- [Runner Service] Step 1: Deserializing DataFrame ---")
    try:
        # io.StringIO "pretends" the string is a file, which is what pd.read_json expects.
        df_json_io = io.StringIO(request.dataframe_json)
        df_in = pd.read_json(df_json_io, orient='records')
    except Exception as e:
        # If the JSON is bad, we can't proceed.
        # 'raise HTTPException' sends a proper web error back.
        print(f"--- [Runner Service] ERROR: Failed to read JSON: {e} ---")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to deserialize input DataFrame: {e}"
        )
    
    # --- NEW: Step 1.5: Static Security Check ---
    # This is our "belt-and-suspenders" check (Pillar 4)
    # We quickly scan the code snippet for forbidden keywords.
    # This is faster and safer than letting exec() be the only defense.
    print("--- [Runner Service] Step 1.5: Running static security check ---")
    # We'll block 'import' (they should use our provided modules)
    # and '__' (which blocks access to internal Python magic methods).
    FORBIDDEN_KEYWORDS = ["import ", "__"] 
    
    if any(keyword in request.code_snippet for keyword in FORBIDDEN_KEYWORDS):
        print(f"--- [Runner Service] ERROR: Forbidden keyword found in code snippet. ---")
        # This is a hard-stop security failure.
        # We don't even try to run it.
        return ExecutionResponse(
            cleaned_dataframe_json=None,
            success=False,
            error_message=f"Security Violation: Code snippet contains forbidden keyword."
        )
    
    # --- STEP 2: Create the secure sandbox environment ---
    print("--- [Runner Service] Step 2: Creating secure environment ---")
    # We call our function create_execution_environment to build the "jail".
    # The 'env' dict now holds {'globals': ..., 'locals': ...}
    env = create_execution_environment(df_in)

    # --- STEP 3: Execute the LLM's code (The "Magic") ---
    print(f"--- [Runner Service] Step 3: Executing code: {request.code_snippet} ---")
    try:
        # This is the moment of truth.
        # We run the 'code_snippet' (from the request).
        # We tell it to run *inside* our 'env'.
        # Any changes (like to 'df') happen *inside* the 'env' dictionaries.
        exec(request.code_snippet, env["globals"], env["locals"])

        # --- STEP 4: If execution succeeds, extract the result ---
        print("--- [Runner Service] Step 4: Execution Succeeded. Extracting cleaned data. ---")
        
        # We "reach into" the 'locals' part of our 'env'
        # and pull out the 'df' variable, which has now been modified.
        df_out = env["locals"]["df"]

                # --- STEP 5: Serialize the cleaned DataFrame for the response ---
        print("--- [Runner Service] Step 5: Serializing cleaned data to JSON. ---")
        cleaned_json = df_out.to_json(orient='records')
        
        # Return the final, successful response object.
        # FastAPI will turn this into a JSON string for us.
        return ExecutionResponse(
            cleaned_dataframe_json=cleaned_json,
            success=True,
            error_message=None
        )
    
    except Exception as e:
        # --- STEP 6 (FAILURE): Handle any execution error (Pillar 2) ---
        print(f"--- [Runner Service] ERROR: Code execution failed: {e} ---")
        
        # The 'exec()' call failed! This is not a crash for us.
        # We catch the error and package it nicely for the user.
        # This 'error_message' is what our main agent will use
        # for the "self-correction" loop.
        return ExecutionResponse(
            cleaned_dataframe_json=None, # Send no data back
            success=False,
            error_message=str(e) # Send the traceback as a string
        )
    
# === Main Execution (For Testing) ===
# This block of code *only* runs if you execute this file directly
# with the command: `python runner_service.py`

if __name__ == "__main__":
    print("--- Starting Secure Code Runner Service (for local testing) ---")
    print("--- To test, open your browser to: http://127.0.0.1:8000/docs ---")
    
    # This command starts the Uvicorn server.
    # 'host="0.0.0.0"' is CRITICAL for Docker. It tells the server
    # to listen for connections from "outside" the container.
    # If you use the default "127.0.0.1", Docker won't work.
    uvicorn.run(app, host="0.0.0.0", port=8000)
