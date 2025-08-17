#!/bin/bash

# D&D Monster Pipeline - Airflow Setup Script
# This script automates the complete Airflow setup process

set -e  # Exit on any error

echo "🐉 Setting up Airflow for D&D Monster Pipeline..."

# Step 1: Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Step 2: Setup environment variables
echo "📝 Setting up environment variables..."
export AIRFLOW_HOME=$(pwd)/airflow_home
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/dags
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# Step 3: Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Step 4: Check if database already exists
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
    echo "🗄️ Initializing Airflow database..."
    airflow db init
else
    echo "✅ Airflow database already exists"
fi

# Step 5: Check if admin user exists and create if needed
echo "👤 Checking admin user..."
if airflow users list 2>/dev/null | grep -q "| admin"; then
    echo "✅ Admin user already exists"
else
    echo "� Creating admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin
    
    # Verify user was created successfully
    if airflow users list 2>/dev/null | grep -q "| admin"; then
        echo "✅ Admin user created successfully"
    else
        echo "❌ Failed to create admin user"
        exit 1
    fi
fi

# Step 6: Start services in background
echo "🚀 Starting Airflow services..."

# Stop any existing processes
pkill -f "airflow webserver" 2>/dev/null || true
pkill -f "airflow scheduler" 2>/dev/null || true
sleep 2

# Start webserver
echo "🌐 Starting webserver on port 8080..."
nohup airflow webserver -p 8080 > airflow_webserver.log 2>&1 &
WEBSERVER_PID=$!

# Start scheduler
echo "⏰ Starting scheduler..."
nohup airflow scheduler > airflow_scheduler.log 2>&1 &
SCHEDULER_PID=$!

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if ps -p $WEBSERVER_PID > /dev/null; then
    echo "✅ Webserver started successfully (PID: $WEBSERVER_PID)"
else
    echo "❌ Failed to start webserver"
    exit 1
fi

if ps -p $SCHEDULER_PID > /dev/null; then
    echo "✅ Scheduler started successfully (PID: $SCHEDULER_PID)"
else
    echo "❌ Failed to start scheduler"
    exit 1
fi

# Final status
echo ""
echo "🎉 Airflow setup complete!"
echo "📊 Access the UI at: http://localhost:8080"
echo "🔑 Login credentials: admin / admin"
echo "📋 DAG available: dnd_monster_pipeline"
echo ""

# Verify login credentials work
echo "🔍 Verifying setup..."
if airflow users list 2>/dev/null | grep -q "| admin"; then
    echo "✅ Admin user verified"
else
    echo "⚠️ Warning: Admin user verification failed"
fi

# Check if webserver is responding
sleep 5
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/login/ 2>/dev/null | grep -q "200"; then
    echo "✅ Webserver is responding"
else
    echo "⚠️ Webserver may still be starting up..."
fi

echo ""
echo "📜 To stop services run:"
echo "   pkill -f 'airflow webserver'"
echo "   pkill -f 'airflow scheduler'"
echo ""
echo "📖 Logs:"
echo "   Webserver: $(pwd)/airflow_webserver.log"
echo "   Scheduler: $(pwd)/airflow_scheduler.log"
