#!/bin/bash

# Simple script to run the frontend in development mode

echo "Starting frontend development server..."

cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Set environment variables if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from env.example..."
    cp env.example .env
fi

# Run the development server
echo "Starting Vite dev server on http://localhost:3030"
npm run dev
