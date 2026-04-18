#!/bin/bash

echo "======================================"
echo "  FAILSAFE - Starting Application"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check PostgreSQL
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL is running${NC}"
else
    echo -e "${RED}PostgreSQL is not running. Starting...${NC}"
    brew services start postgresql@15
    sleep 3
fi

# Activate backend venv
echo -e "${YELLOW}Activating Python environment...${NC}"
cd backend
source venv/bin/activate

# Check if model exists
if [ ! -f "app/ml/risk_model.joblib" ]; then
    echo -e "${YELLOW}Model not found. Training...${NC}"
    python -m app.ml.train_model
fi

# Start backend in background
echo -e "${YELLOW}Starting backend server...${NC}"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend
echo -e "${YELLOW}Starting frontend server...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}FAILSAFE is running!${NC}"
echo "======================================"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Login Credentials:"
echo "  Admin:   admin / admin123"
echo "  Faculty: faculty1 / faculty123"
echo "  HOD:     hod1 / hod123"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "======================================"

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '${RED}Shutting down...${NC}'; exit" INT TERM

# Wait
wait
