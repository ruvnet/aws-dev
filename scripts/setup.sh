# Base image
FROM mcr.microsoft.com/vscode/devcontainers/base:0-buster

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    sudo ./aws/install && \
    rm -rf awscliv2.zip ./aws

# Install system dependencies
RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    python3-distutils \
    python3-venv \
    docker.io \
    build-essential \
    curl \
    sudo \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Manually install pip
RUN curl -O https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# Install Rust (needed for maturin)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install Python dependencies
RUN pip install maturin==1.0.0 typing-extensions==4.6.3 boto3 fastapi pydantic uvicorn aws-sam-cli

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    sudo apt update && \
    sudo apt install -y gh

# Ensure pip is available globally
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set user
USER vscode
