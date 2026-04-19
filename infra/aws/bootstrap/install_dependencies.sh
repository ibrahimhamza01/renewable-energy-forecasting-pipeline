#!/usr/bin/env bash
set -euo pipefail

echo "Updating apt packages..."
sudo apt update

echo "Installing system dependencies..."
sudo apt install -y \
  curl \
  unzip \
  git \
  openjdk-17-jdk \
  python3 \
  python3-pip \
  python3-venv

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
else
  echo "uv already installed."
fi

# Make sure uv is available in this shell too
export PATH="$HOME/.local/bin:$PATH"

echo "Verifying installations..."
java -version
git --version
python3 --version
pip3 --version
uv --version

echo "Dependency installation complete."