# Major Changes - All-in-One FastAPI Server

## Summary

**Before:** 2 separate servers needed
- Approval API (port 8085) - handled approve/reject callbacks
- Agent Server (port 8080/8084) - ran the agent

**After:** 1 unified server
- All-in-One FastAPI Server (port 8086) - handles EVERYTHING

## What Changed

### 1. Port Changes
- **Old**: Approval API on 8085, Agent on 8080
- **New**: Everything on **8086**

### 2. Server Architecture
- **Merged** `approval_api.py` routes into `server.py`
- **No longer need** to run `start_approval_api.sh` separately
- **Single command** to start everything

### 3. Files Modified

#### server.py
- ✅ Changed default port to 8086
- ✅ Added all approval API endpoints (`/api/approve`, `/api/reject`, `/api/status`)
- ✅ Added `push_response_to_adk()` function
- ✅ Now handles both agent requests AND approval callbacks

#### agent.py
- ✅ Changed `APPROVAL_API_PORT` default from 8085 to 8086
- ✅ Uses `AGENT_SERVER_PORT` environment variable
- ✅ Falls back to `localhost:8086` instead of `localhost:8085`

#### start_agent_server.sh
- ✅ Changed port from 8080 to 8086
- ✅ Updated messaging to reflect "All-in-One" server

### 4. Environment Variables

**Old `.env`:**
```bash
APPROVAL_API_PORT=8085
AGENT_SERVER_PORT=8080
ADK_API_URL=http://127.0.0.1:8080
```

**New `.env`:**
```bash
AGENT_SERVER_PORT=8086  # Single port for everything!
ADK_API_URL=http://127.0.0.1:8086  # Point to the same server
APPROVAL_API_URL=http://your-external-ip:8086  # Optional
```

## How to Run

### Old Way (2 terminals):
```bash
# Terminal 1
bash insurance_notification/start_approval_api.sh  # Port 8085

# Terminal 2
bash insurance_notification/start_agent_server.sh  # Port 8080
```

### New Way (1 terminal):
```bash
# From hitl-adk/ directory (same as adk web .)
cd /path/to/hitl-adk
bash start_agent_server.sh  # Port 8086
```

**Note:**
- The startup script is located in `hitl-adk/start_agent_server.sh`
- Just like `adk web .`, you run this from the `hitl-adk/` directory
- Simple command: `bash start_agent_server.sh`

## What the FastAPI Server Now Includes

### 📋 Agent Endpoints (from `get_fast_api_app`)
- `POST /run` - Run the agent
- `GET /apps` - List apps
- `GET /dev-ui/` - Web interface
- All other ADK routes

### ✅ Approval Endpoints (merged from `approval_api.py`)
- `GET /api/approve/{ticket_id}` - Approve request
- `GET /api/reject/{ticket_id}` - Reject request
- `GET /api/status/{ticket_id}` - Get status
- `GET /api/approvals/pending` - List pending

### 🔧 Utility Endpoints (custom)
- `GET /health` - Health check
- `POST /feedback` - Submit feedback
- `GET /` - API overview

## Benefits

✅ **Simpler deployment** - 1 server instead of 2
✅ **Fewer ports to manage** - Everything on 8086
✅ **Easier configuration** - Single `.env` file
✅ **Better performance** - No cross-server communication
✅ **Production ready** - Cloud logging, tracing, session management

## Migration Guide

If you were using the old 2-server setup:

1. **Update your `.env`**:
   ```bash
   AGENT_SERVER_PORT=8086
   ADK_API_URL=http://127.0.0.1:8086
   ```

2. **Stop both old servers** (if running)

3. **Start the new unified server**:
   ```bash
   bash insurance_notification/start_agent_server.sh
   ```

4. **Update any external URLs** that pointed to port 8085 to now use 8086

That's it! Everything else works the same.
