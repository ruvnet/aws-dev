#!/bin/bash

# Update package information
echo "Updating package information..."
sudo apt-get update

# Install necessary packages
echo "Installing necessary packages..."
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker’s official GPG key
echo "Adding Docker’s official GPG key..."
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository for Debian Buster
echo "Setting up the stable Docker repository for Debian Buster..."
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian buster stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
echo "Updating package index..."
sudo apt-get update

# Install Docker Engine
echo "Installing Docker Engine..."
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Verify Docker installation
echo "Verifying Docker installation..."
sudo docker run hello-world

# Manage Docker as a non-root user
echo "Adding the current user to the Docker group..."
sudo groupadd docker
sudo usermod -aG docker $USER

# Activate the changes to groups
echo "Activating the changes to groups..."
newgrp docker

# Verify non-root Docker installation
echo "Verifying Docker installation without sudo..."
docker run hello-world

# Ensure Docker starts automatically
echo "Ensuring Docker starts automatically at boot..."
sudo systemctl enable docker

echo "Docker installation and configuration complete."
