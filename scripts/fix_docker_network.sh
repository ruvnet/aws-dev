#!/bin/bash

# Create or edit the Docker daemon configuration file
echo "Creating or editing the Docker daemon configuration file..."
sudo mkdir -p /etc/docker
echo '{ "iptables": false }' | sudo tee /etc/docker/daemon.json

# Restart the Docker service
echo "Restarting the Docker service..."
sudo service docker restart

# Check the Docker service status
echo "Checking the Docker service status..."
sudo service docker status

# Verify Docker setup
echo "Verifying Docker setup..."
docker info
