#!/bin/bash

# Exit on error
set -e

# Define installation directories and variables
BOT_DIR="$HOME/pavlov-bot"
GIT_REPO="https://github.com/makupi/pavlov-bot"
PIPENV_PATH="/usr/local/bin/pipenv"

echo "Updating and installing prerequisites..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip software-properties-common

# Install Python 3.8 if necessary
if ! python3.8 --version &>/dev/null; then
    echo "Installing Python 3.8..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.8
fi

# Install pipenv
if ! command -v pipenv &>/dev/null; then
    echo "Installing pipenv..."
    sudo pip3 install pipenv
fi

# Clone the repository if it doesn't exist
if [ ! -d "$BOT_DIR" ]; then
    echo "Cloning pavlov-bot repository..."
    git clone "$GIT_REPO" "$BOT_DIR"
else
    echo "Repository already exists, pulling latest updates..."
    cd "$BOT_DIR"
    git pull
fi

cd "$BOT_DIR"

# Copy default config files if they do not exist
echo "Setting up configuration files..."
[ ! -f config.json ] && cp Examples/config.json.default config.json
[ ! -f servers.json ] && cp Examples/servers.json.default servers.json
[ ! -f aliases.json ] && cp Examples/aliases.json.default aliases.json
[ ! -f commands.json ] && cp Examples/commands.json.default commands.json
[ ! -f polling.json ] && cp Examples/polling.json.default polling.json
[ ! -f lists.json ] && cp Examples/lists.json.default lists.json

echo "Installing dependencies with pipenv..."
$PIPENV_PATH install

echo "Starting pavlov-bot..."
$PIPENV_PATH run python3.8 run.py
