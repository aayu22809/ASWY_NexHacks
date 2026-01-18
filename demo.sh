#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}   Cold Plasma Treatment System - DEMO   ${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to check if a command exists
check_cmd() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed.${NC}"
        exit 1
    fi
}

# 1. Check Prerequisites
echo -e "\n${BLUE}[1/3] Checking Prerequisites...${NC}"
check_cmd python3
echo -e "${GREEN}✓ Python3 found.${NC}"

# 2. Setup Python Environment
echo -e "\n${BLUE}[2/3] Setting up Python Environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies (this may take a moment)..."
pip install -q fastapi uvicorn open3d numpy scipy 2>/dev/null || {
    echo -e "${YELLOW}Installing from requirements.txt...${NC}"
    pip install -q -r backend/requirements.txt 2>/dev/null
}
echo -e "${GREEN}✓ Dependencies installed.${NC}"

# 3. Start Unified Server
echo -e "\n${BLUE}[3/3] Starting Unified Demo Server...${NC}"

# Trap Ctrl+C to kill server
cleanup() {
    echo -e "\n${YELLOW}Shutting down server...${NC}"
    kill $SERVER_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT

# Start server
echo "Starting server on http://0.0.0.0:8000..."
python3 demo_server.py > demo.log 2>&1 &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✓ Server running (PID: $SERVER_PID)${NC}"
else
    echo -e "${RED}✗ Server failed to start. Check demo.log for errors.${NC}"
    exit 1
fi

# Try to open browser (works on macOS and Linux with xdg-open)
if command -v open &> /dev/null; then
    sleep 1
    open http://localhost:8000 2>/dev/null &
elif command -v xdg-open &> /dev/null; then
    sleep 1
    xdg-open http://localhost:8000 2>/dev/null &
fi

# Display info
echo -e "\n${BLUE}=================================================${NC}"
echo -e "${GREEN}Demo Server is Live!${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "\nAccess the interface at: ${GREEN}http://localhost:8000${NC}"
echo -e "\nLogs: ${YELLOW}demo.log${NC}"
echo -e "\n${RED}Press Ctrl+C to stop the server.${NC}\n"

# Wait for server
wait $SERVER_PID