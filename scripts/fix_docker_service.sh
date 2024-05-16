#!/bin/bash

# Backup the original Docker service script
echo "Backing up the original Docker service script..."
sudo cp /etc/init.d/docker /etc/init.d/docker.bak

# Modify the Docker service script to set a valid ulimit
echo "Modifying the Docker service script to set a valid ulimit..."
sudo sed -i 's/ulimit -n [0-9]*/ulimit -n 65535/' /etc/init.d/docker

# Start the Docker service
echo "Starting the Docker service..."
sudo service docker start

# Check the Docker service status
echo "Checking the Docker service status..."
sudo service docker status
