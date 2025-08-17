#!/bin/bash

# D&D Monster Pipeline - Airflow Cleanup Script
# This script stops Airflow services cleanly

echo "🛑 Stopping Airflow services..."

# Stop Airflow processes
pkill -f "airflow webserver" 2>/dev/null || true
pkill -f "airflow scheduler" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 3

# Check if any processes are still running
RUNNING=$(ps aux | grep airflow | grep -v grep | wc -l)

if [ "$RUNNING" -eq "0" ]; then
    echo "✅ All Airflow services stopped successfully"
else
    echo "⚠️  Some Airflow processes may still be running:"
    ps aux | grep airflow | grep -v grep
    echo ""
    echo "💡 You can force kill with: pkill -9 -f airflow"
fi

# Clean up log files if they exist
if [ -f "airflow_webserver.log" ]; then
    echo "🗑️  Cleaning up log files..."
    rm -f airflow_webserver.log airflow_scheduler.log
fi

echo "🏁 Cleanup complete!"
