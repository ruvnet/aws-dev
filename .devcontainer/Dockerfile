# Base image
FROM mcr.microsoft.com/vscode/devcontainers/base:0-buster

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" &&     unzip awscliv2.zip &&     sudo ./aws/install &&     rm -rf awscliv2.zip ./aws

# Install other dependencies if needed
RUN apt-get update && apt-get install -y     jq     && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set the default shell to bash
SHELL ["/bin/bash", "-c"]

# Set user
USER vscode
