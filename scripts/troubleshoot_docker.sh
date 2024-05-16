#!/bin/bash

# Check Docker logs for errors
echo "Checking Docker logs for errors..."
sudo journalctl -u docker.service | tail -n 100

# Check Docker log file for errors
echo "Checking Docker log file for errors..."
sudo tail -n 100 /var/log/docker.log

# Verify ulimit changes
echo "Verifying ulimit changes..."
sudo cat /lib/systemd/system/docker.service | grep -i limitnofile

# Validate Docker configuration
echo "Validating Docker configuration..."
sudo cat /etc/docker/daemon.json

# Restart Docker service
echo "Restarting Docker service..."
sudo service docker restart

# Check Docker service status
echo "Checking Docker service status..."
sudo service docker status

# Verify Docker is running
echo "Verifying Docker setup..."
docker info
