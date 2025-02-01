#!/bin/bash

# Start the backend server
echo "Starting backend server..."
source venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
cd ..

# Start the frontend server
echo "Starting frontend server..."
cd frontend
npm start 