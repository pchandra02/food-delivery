#!/bin/bash

# Start Redis server if not running
# redis-server &

# Start the backend server
cd backend

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Start backend server
echo "Starting backend server..."
uvicorn app.main:app --reload --port 8000 &

# Start the frontend server
cd ../frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend server
echo "Starting frontend server..."
npm run dev &

echo "Servers are starting..."
echo "Frontend will be available at: http://localhost:5173"
echo "Backend will be available at: http://localhost:8000"
echo "API documentation will be available at: http://localhost:8000/docs"

# Wait for any key to terminate all background processes
read -p "Press any key to terminate servers..."
pkill -f "uvicorn"
pkill -f "vite"
pkill -f "redis-server" 