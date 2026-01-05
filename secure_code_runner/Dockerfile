# === BLOCK 1: The "Base Image" ===
# We start from an official, pre-built "virtual computer"
# that already has Python 3.11 installed.
# "slim" means it's stripped down (no extra tools), which is safer.
FROM python:3.11-slim

# === BLOCK 2: Setup Environment ===
# Create a folder inside the container to hold our app.
WORKDIR /app

# Prevent Python from writing .pyc files (useless in a container)
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure logs are printed immediately to the console
ENV PYTHONUNBUFFERED=1

# === BLOCK 3: Install Dependencies ===
# We copy ONLY the requirements file first.
# Docker caches this step. If you change your code but not your libraries,
# Docker will skip this slow install step next time!
COPY requirements.txt .

# Install the libraries. 
# --no-cache-dir keeps the image small by deleting download caches.
RUN pip install --no-cache-dir -r requirements.txt

# === BLOCK 4: Copy Application Code ===
# Now copy the rest of our code (runner_service.py) into the container.
COPY runner_service.py .

# === BLOCK 5: Security (Run as non-root) ===
# By default, Docker runs as "root" (admin). That's a risk.
# We create a generic user and switch to it.
# This is a "Pillar 4" security best practice.
RUN useradd -m appuser
USER appuser

# === BLOCK 6: Startup Command ===
# This is the command that runs when the container starts.
# host="0.0.0.0" is CRITICAL to expose the server outside the container.
CMD ["uvicorn", "runner_service:app", "--host", "0.0.0.0", "--port", "8000"]