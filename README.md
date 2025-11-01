# Insurance Notification Agent V2

An AI-powered insurance customer service agent built with Google's Agent Development Kit (ADK) that automatically sends email notifications to customers about claims, policy renewals, and other insurance matters.

## What's New in V2

✨ **Unified All-in-One Server** - Single FastAPI server combining agent and approval endpoints
🚀 **Simplified Deployment** - One command to start everything (no more multiple servers)
🔧 **Production Ready** - Cloud logging, tracing, and session management built-in
📦 **Clean Architecture** - Removed deprecated files, streamlined codebase

## Features

🔔 **Email Notifications** - Send formatted HTML email notifications to customers
📋 **Claim Status Tracking** - Check and update customers on insurance claim status
📄 **Policy Management** - Monitor policy status and send renewal reminders
🤖 **AI-Powered** - Uses Gemini 2.5 Flash model for intelligent customer service
💼 **Professional Templates** - Beautiful HTML email templates for all notification types
✅ **Human-in-the-Loop Approval** - Request user approval via email with approve/reject buttons
🔄 **Automatic Agent Resumption** - Agent automatically resumes after user responds to approval request

## Notification Types

- **claim_update**: Claim status changes and approvals
- **claim_verification**: Human-in-the-loop approval requests with approve/reject buttons
- **policy_renewal**: Policy renewal reminders
- **payment_reminder**: Payment due notices
- **general**: General insurance communications

## Project Structure

```
insurance_notification_v2/
├── __init__.py              # Package initialization
├── agent.py                 # Agent configuration with HITL tools
├── server.py                # All-in-One FastAPI server (agent + approvals)
├── approval_manager.py      # Approval state management
├── tools.py                 # Agent tools (email, claims, policies)
├── start_agent_server.sh    # Startup script
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── CHANGES.md               # Migration guide from V1
└── README.md                # This file
```

## Prerequisites

1. **Python 3.9+**
2. **Google Cloud Project** with Vertex AI API enabled
3. **Gmail Account** (optional - for sending real emails)
4. **ADK Python SDK** installed

## Quick Start

### 1. Install Dependencies

```bash
pip install google-adk python-dotenv fastapi uvicorn httpx
```

### 2. Configure Environment Variables

Create a `.env` file in the `insurance_notification_v2` directory:

```bash
# Google Cloud Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Email Configuration (optional - leave empty for demo mode)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# All-in-One Server Configuration
AGENT_SERVER_PORT=8086
ADK_API_URL=http://127.0.0.1:8086

# Approval URL Configuration (optional - auto-detected if not set)
APPROVAL_API_URL=http://your-external-ip:8086

# Session Service (optional - for production)
SESSION_SERVICE_URI=  # Leave empty for in-memory sessions (development)
                      # For production: redis://localhost:6379 or firestore://your-project
```

**Note:**
- If you leave `SENDER_PASSWORD` empty, the agent runs in **demo mode** (emails printed to console)
- `APPROVAL_API_URL` is auto-detected using your external IP if not set
- `ADK_API_URL` should point to the same server (port 8086)
- `SESSION_SERVICE_URI`: Leave empty for development, configure for production

### 3. Set Up Gmail App Password (Optional)

To send real emails via Gmail:

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password: https://myaccount.google.com/apppasswords
4. Use the generated password in your `.env` file

### 4. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## Usage

### Starting the Server

**Simple one-command startup!**

```bash
# Navigate to hitl-adk directory (parent directory)
cd /path/to/hitl-adk

# Start the all-in-one server
bash start_agent_server.sh
```

Or run directly:
```bash
# From hitl-adk/ directory
python -m insurance_notification_v2.server
```

The server will start on port **8086** by default.

**Expected Output:**
```
================================================================================
🚀 Insurance Notification Agent V2 - All-in-One FastAPI Server
================================================================================

Server running at: http://0.0.0.0:8086

📋 AGENT ENDPOINTS:
  - POST /run                       - Run the agent
  - GET  /apps                      - List available apps
  - GET  /dev-ui/                   - Web interface
  - GET  /docs                      - Interactive API docs

✅ APPROVAL ENDPOINTS (Human-in-the-Loop):
  - GET  /api/approve/{ticket_id}   - Approve a request
  - GET  /api/reject/{ticket_id}    - Reject a request
  - GET  /api/status/{ticket_id}    - Get request status
  - GET  /api/approvals/pending     - List pending approvals

🔧 UTILITY ENDPOINTS:
  - GET  /health                    - Health check
  - POST /feedback                  - Submit feedback
  - GET  /                          - API overview

✨ This is a unified server - no need to run approval_api.py separately!
================================================================================
```

### Access the Application

**Web Interface:**
```
http://localhost:8086/dev-ui/
```

**Interactive API Documentation:**
```
http://localhost:8086/docs
```

**API Overview:**
```
http://localhost:8086/
```

### Example Interactions

**Claim Verification with Human-in-the-Loop Approval:**
```
User: "I need approval for claim CLM-001 from customer@example.com"

Agent:
1. Retrieves claim details for CLM-001
2. Sends email with APPROVE/REJECT buttons to customer@example.com
3. Pauses and waits for user response
4. (User clicks APPROVE in their email)
5. Agent automatically resumes execution
6. Sends confirmation email with next steps
```

**Claim Status Update:**
```
User: "Check claim CLM-001 and send an email to customer@example.com"

Agent:
- Retrieves claim details
- Sends formatted email with claim status
- Confirms notification sent
```

**Policy Renewal Reminder:**
```
User: "Check policy POL-67890 and send renewal reminder to customer@example.com"

Agent:
- Checks policy status
- Detects upcoming renewal (4 days)
- Sends urgent renewal reminder email
```

## Human-in-the-Loop (HITL) Approval Workflow

This agent implements a sophisticated human-in-the-loop approval workflow that allows the agent to pause execution and wait for human approval before proceeding.

### How It Works

1. **Agent Requests Approval**: The agent calls the `request_claim_approval()` tool
2. **Email Sent**: An email with approve/reject buttons is sent to the user
3. **Agent Pauses**: The agent pauses execution and waits for user response
4. **User Responds**: User clicks APPROVE or REJECT button in their email
5. **Callback Received**: The approval API receives the callback on the same server
6. **Agent Resumes**: The API pushes the response back to `/run`, automatically resuming the agent
7. **Agent Continues**: The agent processes the approval status and continues execution

### Unified Architecture (V2)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│    All-in-One FastAPI Server (Port 8086)              │
│                                                         │
│  ┌─────────────────┐      ┌──────────────────┐        │
│  │                 │      │                  │        │
│  │  Agent          │      │  Approval API    │        │
│  │  Endpoints      │      │  Endpoints       │        │
│  │  /run, /apps    │      │  /api/approve    │        │
│  │                 │      │  /api/reject     │        │
│  └─────────────────┘      └──────────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
         │                            ▲
         │ 1. Send Email              │ 3. HTTP Callback
         │ with Approve/              │    /api/approve/{id}
         │ Reject buttons             │
         v                            │
    ┌─────────┐                       │
    │  User   │  2. Click Approve  ───┘
    │  Email  │     or Reject
    └─────────┘

         4. Server pushes FunctionResponse to itself via /run
         5. Agent automatically resumes with approval status
```

### Using the Approval Tool

The `request_claim_approval()` tool is a long-running tool that:
- Sends an email with approve/reject buttons
- Stores approval state in `/tmp/approval_requests.json`
- Returns with status "pending"
- When user responds, the approval API automatically pushes the response back to ADK
- The agent resumes with the approval status

**Example Call:**
```python
request_claim_approval(
    claim_id="CLM-001",
    customer_email="customer@example.com"
)
```

**Note:** The `user_id` and `session_id` are automatically extracted from the tool context.

## Tools Available

### 1. `send_email_notification()`
Sends HTML-formatted email notifications to customers.

**Parameters:**
- `recipient_email` (str): Email address of recipient
- `subject` (str): Email subject line
- `message` (str): Email body content
- `notification_type` (str): Type of notification (claim_update, policy_renewal, payment_reminder, general)

### 2. `get_claim_status()`
Retrieves current status of an insurance claim.

**Parameters:**
- `claim_id` (str): Claim ID to look up

**Demo Claims:**
- `CLM-001`: Approved auto accident claim ($4,500 approved)
- `CLM-002`: Pending property damage claim ($12,000 claimed)

### 3. `check_policy_status()`
Checks status of an insurance policy.

**Parameters:**
- `policy_number` (str): Policy number to look up

**Demo Policies:**
- `POL-12345`: Active auto insurance policy (65 days until renewal)
- `POL-67890`: Home insurance pending renewal (4 days until renewal)

### 4. `request_claim_approval()` (Long-Running Tool)
Requests approval for a claim submission via email with approve/reject buttons.

**Parameters:**
- `claim_id` (str): The claim ID requiring approval
- `customer_email` (str): Email address to send approval request to

**Behavior:**
- Sends an email with clickable approve/reject buttons
- Creates an approval ticket in the system
- Returns "pending" status
- When user responds, the approval API automatically pushes the response back to the agent
- The agent resumes execution with the approval status

**Example Approval Email:**
The user receives an email with two buttons:
- ✓ YES, I SUBMITTED THIS CLAIM (green button)
- ✗ NO, I DID NOT SUBMIT THIS (red button)

Clicking either button:
1. Updates the approval status
2. Shows a confirmation page
3. Automatically resumes the agent with the response

## Demo Mode vs. Production Mode

### Demo Mode (Default)
When `SENDER_PASSWORD` is not set, emails are **printed to console** instead of sent:

```
📧 EMAIL NOTIFICATION (Demo Mode - Not Actually Sent)
To: customer@example.com
Subject: Claim Status Update - CLM-001
Type: claim_update
Message: Your claim has been approved...
```

### Production Mode
When SMTP credentials are configured, real emails are sent via Gmail:

```
✅ Email notification sent successfully
Recipient: customer@example.com
Subject: Claim Status Update
Status: Delivered
```

## Troubleshooting

**Email Not Sending:**
- Check `SENDER_EMAIL` and `SENDER_PASSWORD` in `.env`
- Verify Gmail App Password is correct
- Check SMTP server and port settings

**Agent Not Responding:**
- Verify `GOOGLE_CLOUD_PROJECT` is set correctly
- Ensure you've authenticated with `gcloud auth application-default login`
- Check that Vertex AI API is enabled in your project

**Approval Not Resuming Agent:**
- Verify `ADK_API_URL=http://127.0.0.1:8086` (same port as server)
- Check server logs for push_response_to_adk() output
- Ensure app_name is "insurance_notification_v2" in agent.py

**Import Errors:**
- Make sure you're running from the `hitl-adk/` directory
- Install missing dependencies: `pip install google-adk python-dotenv fastapi uvicorn httpx`

## Deployment Options

### Development
```bash
# In-memory sessions, demo email mode
bash start_agent_server.sh
```

### Production
1. Configure persistent session service (Redis/Firestore)
2. Set up real SMTP credentials
3. Use external IP for APPROVAL_API_URL
4. Enable cloud logging and tracing
5. Run behind reverse proxy (nginx) with HTTPS

```bash
# Example production .env
SESSION_SERVICE_URI=redis://localhost:6379
SENDER_EMAIL=noreply@yourcompany.com
SENDER_PASSWORD=your-app-password
APPROVAL_API_URL=https://your-domain.com:8086
```

## Security Considerations

⚠️ **Important Security Notes:**

- Never commit `.env` file with real credentials to version control
- Use Google Cloud Secret Manager for production credentials
- Implement rate limiting to prevent email spam
- Validate recipient email addresses before sending
- Add authentication for customer data access
- Use encryption for sensitive claim/policy information
- **Approval API Security**:
  - The approval endpoints are currently unauthenticated (designed for email callbacks)
  - Consider adding HMAC signatures to approval URLs to prevent tampering
  - Implement one-time use tokens for approval links
  - Add expiration times to approval requests
  - Use HTTPS in production to encrypt approval callbacks
  - Store approval data securely (currently in `/tmp/approval_requests.json`)

## Migration from V1

See [CHANGES.md](CHANGES.md) for detailed migration guide.

**Key Changes:**
- Port changed from 8080/8085 to unified 8086
- Single server instead of two separate servers
- app_name changed to "insurance_notification_v2"
- Simplified startup with one command

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0

## Support

For issues or questions:
- Check the ADK documentation: https://google.github.io/adk-python/
- Review ADK samples: https://github.com/google/adk-python/tree/main/samples
- File an issue at: https://github.com/analyticsrepo01/insurance_notification_v2/issues

---

Built with ❤️ using Google Agent Development Kit (ADK)
