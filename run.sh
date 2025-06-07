#!/bin/bash

# Writing Assistant Web App Runner

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="writing-assistant-web"
PORT=3500

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to kill all Next.js processes on our port
cleanup_processes() {
    print_message $YELLOW "🧹 Cleaning up existing processes..."
    
    # Kill any process using our port
    lsof -ti:$PORT | xargs -r kill -9 2>/dev/null || true
    
    # Kill any Next.js dev processes
    pkill -f "next dev" 2>/dev/null || true
    
    # Give processes time to die
    sleep 1
    
    print_message $GREEN "✅ Cleanup complete"
}

# Function to handle script termination
handle_exit() {
    print_message $YELLOW "\n🛑 Shutting down Writing Assistant..."
    
    # Kill any child processes
    pkill -P $$ 2>/dev/null || true
    
    # Final cleanup
    cleanup_processes
    
    print_message $GREEN "👋 Writing Assistant stopped successfully"
    exit 0
}

# Set up signal handlers
trap handle_exit SIGINT SIGTERM EXIT

# Main execution
print_message $GREEN "🚀 Starting Writing Assistant"

# Clean up any existing processes
cleanup_processes

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    print_message $RED "❌ Error: $APP_DIR directory not found!"
    print_message $YELLOW "Please run this script from the Writing Assistant root directory"
    exit 1
fi

# Navigate to app directory
cd $APP_DIR

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_message $YELLOW "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        print_message $RED "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    print_message $YELLOW "⚠️  Warning: .env.local not found!"
    print_message $YELLOW "Please create .env.local with your API keys:"
    echo "  OPENAI_API_KEY=your_key"
    echo "  ANTHROPIC_API_KEY=your_key"
    echo "  GEMINI_API_KEY=your_key"
    
    # Check if parent .env exists
    if [ -f "../.env" ]; then
        print_message $YELLOW "Found .env in parent directory. Copy it to .env.local? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            cp ../.env .env.local
            print_message $GREEN "✅ Copied .env to .env.local"
        else
            print_message $RED "❌ Cannot continue without API keys"
            exit 1
        fi
    else
        print_message $RED "❌ Cannot continue without API keys"
        exit 1
    fi
fi

# Start the development server
print_message $GREEN "🌐 Starting server on http://localhost:$PORT"
print_message $YELLOW "Press Ctrl+C to stop the server\n"

# Run Next.js in the foreground
npm run dev &
SERVER_PID=$!

# Wait for the server to start
sleep 3

# Check if server started successfully
if ! ps -p $SERVER_PID > /dev/null; then
    print_message $RED "❌ Failed to start the server"
    exit 1
fi

print_message $GREEN "✨ Server is running!"

# Open browser (optional - comment out if you don't want auto-open)
if command -v open &> /dev/null; then
    sleep 2
    open "http://localhost:$PORT"
elif command -v xdg-open &> /dev/null; then
    sleep 2
    xdg-open "http://localhost:$PORT"
fi

# Keep the script running and wait for the server process
wait $SERVER_PID