#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}   Cold Plasma Robot Arm - DEMO LAUNCHER   ${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to check if a command exists
check_cmd() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed.${NC}"
        exit 1
    fi
}

# 1. Check Prerequisites
echo -e "\n${BLUE}[1/5] Checking Prerequisites...${NC}"
check_cmd python3
check_cmd node
check_cmd npm
echo -e "${GREEN}✓ All prerequisites found.${NC}"

# 2. Setup Python Backend
echo -e "\n${BLUE}[2/5] Setting up Backend Environment...${NC}"
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing backend dependencies (this may take a moment)..."
pip install -r backend/requirements.txt > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install python requirements.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend ready.${NC}"

# 3. Setup Frontend
echo -e "\n${BLUE}[3/5] Setting up Frontend...${NC}"
cd plasma-path-planner
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install > /dev/null 2>&1
fi
cd ..
echo -e "${GREEN}✓ Frontend ready.${NC}"

# 4. Start Services
echo -e "\n${BLUE}[4/5] Starting Services...${NC}"

# Trap Ctrl+C to kill background processes
cleanup() {
    echo -e "\n${RED}Stopping services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT

# Start Backend
echo "Starting Backend API on port 8000..."
source venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend running (PID: $BACKEND_PID)${NC}"

# Start Frontend
echo "Starting Frontend..."
cd plasma-path-planner
npm run dev -- --open > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✓ Frontend running${NC}"

# 5. Open Browser and Wait
echo -e "\n${BLUE}[5/5] Demo Live!${NC}"
echo -e "Access the dashboard at: ${GREEN}http://localhost:5173${NC}"
echo -e "\n${BLUE}Logs:${NC}"
echo -e "- Backend: backend.log"
echo -e "- Frontend: frontend.log"
echo -e "\n${RED}Press Ctrl+C to stop the demo.${NC}"

wait $BACKEND_PID