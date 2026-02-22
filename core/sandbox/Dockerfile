FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    vim \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for tools
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create workspace directory
RUN mkdir -p /workspaces /home/agent

# Set working directory
WORKDIR /workspaces

# Default command
CMD ["/bin/bash"]
