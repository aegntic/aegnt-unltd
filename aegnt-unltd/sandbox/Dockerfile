FROM python:3.11-slim

# The "Clean Room" for code execution
WORKDIR /workspace

# Install base tools ONLY. No networking allowed by default.
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# No network access by default
# Network can be enabled via Docker network mode

# Entry point awaits JSON commands via stdin
CMD ["python", "executor.py"]
