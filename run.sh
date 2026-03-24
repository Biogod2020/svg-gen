#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting SVG Optimization Lab...${NC}"

# Function to handle shutdown gracefully
cleanup() {
    echo -e "\n${GREEN}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}[Backend] Starting FastAPI on port 8000...${NC}"
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo -e "${BLUE}[Frontend] Starting Vite on port 5173...${NC}"
cd frontend && npm run dev -- --host &
FRONTEND_PID=$!

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}🚀 All services are up and running!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "🎨 Open your browser at: ${BLUE}http://localhost:5173${NC}"
echo -e "⚙️  Backend API is at:    ${BLUE}http://localhost:8000${NC}"
echo -e "\nPress ${GREEN}Ctrl+C${NC} to stop both servers."
echo -e "-----------------------------------------\n"

# Wait for any background process to exit
wait
