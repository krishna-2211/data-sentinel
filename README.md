DataSentinel

A Human-in-the-Loop agent that safely cleans data, analyzes risk, and runs code in a real sandbox.

Why I Built This?

Most AI coding demos are scary. They take raw code from an LLM and run it directly on your machine using exec(). I wanted to build a tool I could actually trust with my own data, one that prioritizes safety and statistical rigor over just being a "magic black box."

This agent acts as a Statistical Co-Pilot:

1. Profiles your data to find actual issues (missing values, outliers, skew).
2. Consults Google Gemini to propose a cleaning plan.
3. Generates a "Risk Report" so you know if a cleaning step (like imputation) might bias your data.
4. Executes the code in a hardened Docker sandbox that I engineered to prevent Remote Code Execution (RCE).

Core Features:

1. Defense-in-Depth Security

I didn't want to rely on the AI "promising" not to be malicious. I implemented a 3-Layer Security Model:

Static Analysis: The system pre-scans code for forbidden keywords like import or __.
Runtime Sandbox: I overrode Python's __builtins__ to physically remove dangerous functions like open(), eval(), and exec().
Infrastructure Isolation: The execution engine runs in a dedicated Docker container with no network access. Even if code breaks out of Python, it's trapped in the container.

2. Statistical Context

The agent doesn't just fix errors; it explains them.

Audit Log: Explains why a specific method (e.g., Median vs Mean) was chosen based on the data distribution.
Risk Analysis: Warns you about potential downsides (e.g., "This method reduces variance by 5%") and suggests alternatives.

3. Human-in-the-Loop

No black boxes. The AI returns a Proposed Plan as a checklist. You explicitly Approve or Reject specific steps before any code is sent to the runner.

4. No Hallucinations

I used Pydantic to enforce strict JSON schemas on the Gemini output. This prevents the common issue where LLMs generate conversational text instead of usable code, ensuring the UI always renders a valid checklist.

System Architecture

graph LR
    User[User Upload] --> Profiler[Data Profiler]
    Profiler -->|DQR String| Brain[AI Engine (Gemini)]
    Brain -->|Structured Plan (JSON)| UI[Streamlit Dashboard]
    UI -->|User Approval| SecureRunner[Secure Docker Runner]
    SecureRunner -->|Cleaned Data| User


Tech Stack

Frontend: Streamlit
AI Engine: Google Gemini API (Flash Model) + Pydantic
Execution Engine: FastAPI + Docker
Data Stack: Pandas, NumPy, SciPy

Quick Start

Prerequisites:
Docker Desktop installed and running.
Python 3.10+.
A Google Gemini API Key.

1. Set up the Environment

# Clone the repo
git clone [https://github.com/yourusername/secure-ai-agent.git](https://github.com/yourusername/secure-ai-agent.git)
cd secure-ai-agent

# Install dependencies
pip install streamlit requests pandas google-generativeai pydantic

2. Build the Secure Engine (Docker)

You need to build the sandbox container before running the app.

cd secure_code_runner
docker build -t secure-runner .
docker run -p 8000:8000 secure-runner

(Keep this terminal window open)

3. Run the Dashboard

Open a new terminal window in the root folder.

# Set your API Key
$env:GEMINI_API_KEY="your_actual_api_key_here"

# Run the App
python -m streamlit run app.py


Security Deep Dive

The most interesting part of the build is the Secure Code Runner (runner_service.py). It uses a "Workshop vs. Workbench" model:

1. The Workshop (Server): Pre-imports safe libraries (pandas, numpy) into memory on startup.
2. The Workbench (Sandbox): When code runs, I give it a restricted globals() dictionary that contains only those pre-imported libraries and the dataframe.
3. The Lock: I block access to the import statement both statically and at runtime. This makes it impossible for the AI to import os or subprocess to attack the host.