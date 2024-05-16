#!/bin/bash

# Function to install Rust
install_rust() {
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
    source $HOME/.cargo/env
    echo "Rust installed successfully."
}

# Function to upgrade pip
upgrade_pip() {
    echo "Upgrading pip..."
    pip install --upgrade pip
    echo "pip upgraded successfully."
}

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    install_rust
else
    echo "Rust is already installed."
fi

# Upgrade pip
upgrade_pip

# Try installing maturin again
echo "Installing maturin..."
pip install maturin
echo "maturin installed successfully."

echo "All steps completed."
