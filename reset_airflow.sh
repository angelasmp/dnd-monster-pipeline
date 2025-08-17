#!/bin/bash

# D&D Monster Pipeline - Complete Reset Script
# This script completely resets the Airflow environment

echo "🔄 Performing complete Airflow reset..."

# Stop all Airflow processes
echo "🛑 Stopping all Airflow processes..."
pkill -f "airflow webserver" 2>/dev/null || true
pkill -f "airflow scheduler" 2>/dev/null || true
pkill -f "airflow" 2>/dev/null || true
sleep 5

# Remove entire Airflow home directory
if [ -d "airflow_home" ]; then
    echo "🗂️ Removing Airflow home directory..."
    rm -rf airflow_home
fi

# Remove all log files
echo "📝 Removing all log files..."
rm -f airflow_webserver.log
rm -f airflow_scheduler.log
rm -f *.log

# Remove any PID files
rm -f *.pid

# Remove generated output files
rm -f monsters.json

echo "✅ Complete reset finished!"
echo "💡 Run ./setup_airflow.sh to start completely fresh"
