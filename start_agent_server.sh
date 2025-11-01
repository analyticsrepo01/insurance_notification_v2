#!/bin/bash
# Startup script for Insurance Notification Agent All-in-One FastAPI Server
#
# IMPORTANT: Run this from the hitl-adk/ directory (parent directory):
#   cd /path/to/hitl-adk
#   bash insurance_notification/start_agent_server.sh
#
# This is the same way you run 'adk web .'

echo "================================================================================"
echo "🚀 Starting Insurance Notification Agent - All-in-One FastAPI Server"
echo "================================================================================"
echo ""

# Check if we're in the correct directory
if [ ! -d "insurance_notification" ]; then
    echo "❌ Error: Must run from hitl-adk/ directory (parent directory)"
    echo ""
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please run:"
    echo "  cd /path/to/hitl-adk"
    echo "  bash insurance_notification/start_agent_server.sh"
    echo ""
    exit 1
fi

echo "✅ Working directory: $(pwd)"
echo ""

# Set the port
export AGENT_SERVER_PORT=8086

# Start the unified FastAPI server (includes both agent and approval API)
python -m insurance_notification.server
