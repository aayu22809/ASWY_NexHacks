#!/bin/bash

# Configuration
PI_HOST="raspberrypi.local"
PI_USER="pi"
PROJECT_DIR="ASWY_NexHacks"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Cold Plasma Robot Arm - Development Setup ===${NC}"

# 1. Ask for Pi Hostname
read -p "Enter Raspberry Pi hostname/IP [$PI_HOST]: " INPUT_HOST
PI_HOST=${INPUT_HOST:-$PI_HOST}

echo -e "\n${BLUE}[1/3] Configuring Frontend...${NC}"
echo "VITE_API_URL=http://${PI_HOST}:8000" > plasma-path-planner/.env.local
echo "Updated plasma-path-planner/.env.local to point to $PI_HOST"

echo -e "\n${BLUE}[2/3] Syncing Code to Pi...${NC}"
echo "Target: ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}"
read -p "Press Enter to sync (Ctrl+C to cancel)..."

# Sync code (excluding heavy folders)
rsync -avz --exclude 'node_modules' \
           --exclude 'venv' \
           --exclude '.git' \
           --exclude '.DS_Store' \
           ./ ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Sync complete!${NC}"
else
    echo -e "${RED}Sync failed. Check connection.${NC}"
    exit 1
fi

echo -e "\n${BLUE}[3/3] Ready to Launch${NC}"
echo "---------------------------------------------------"
echo "STEP 1: Start Backend on Pi (in a new terminal window):"
echo "ssh ${PI_USER}@${PI_HOST}"
echo "cd ${PROJECT_DIR}"
echo "python3 -m venv venv && source venv/bin/activate"
echo "pip install -r backend/requirements.txt"
echo "uvicorn backend.api:app --host 0.0.0.0 --port 8000"
echo "---------------------------------------------------"
echo "STEP 2: Start Frontend on Mac:"
echo "cd plasma-path-planner"
echo "npm run dev"
echo "---------------------------------------------------"
