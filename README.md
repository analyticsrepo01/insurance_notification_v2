# Insurance Notification Agent

An AI-powered insurance customer service agent built with Google's Agent Development Kit (ADK) that automatically sends email notifications to customers about claims, policy renewals, and other insurance matters.

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
insurance_notification/
├── __init__.py              # Package initialization
├── agent.py                 # Agent configuration and setup with HITL tools
├── server.py                # FastAPI server wrapper for production deployment
├── approval_api.py          # FastAPI server for handling approval callbacks
├── approval_manager.py      # Manages approval state and lifecycle
├── start_agent_server.sh    # Script to start the agent FastAPI server
├── start_approval_api.sh    # Script to start the approval API server
├── design.md                # Architecture and design documentation
├── README.md                # This file
└── .env                     # Environment variables (create from .env.example)
```

## Prerequisites

1. **Python 3.9+**
2. **Google Cloud Project** with Vertex AI API enabled
3. **Gmail Account** (optional - for sending real emails)
4. **ADK Python SDK** installed

## Setup Instructions

### 1. Install Dependencies

```bash
pip install google-adk python-dotenv fastapi uvicorn httpx
```

### 2. Configure Environment Variables

Create a `.env` file in the `insurance_notification` directory:

```bash
# Required for ADK
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional - For sending real emails (leave empty for demo mode)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# All-in-One Server Configuration
AGENT_SERVER_PORT=8086  # Port for the unified FastAPI server (agent + approvals)
ADK_API_URL=http://127.0.0.1:8086  # Server URL for agent resumption (use 8086 for FastAPI, 8084 for adk web)

# Approval URL Configuration (Optional)
APPROVAL_API_URL=http://your-external-ip:8086  # Optional - auto-detected if not set
                                                # Used for email approve/reject button URLs

# Session Service (Optional - for production)
SESSION_SERVICE_URI=  # Leave empty for in-memory sessions (development)
                      # For production, use: redis://localhost:6379 or firestore://your-project
```

**Note:**
- If you leave `SENDER_PASSWORD` empty, the agent will run in **demo mode** and print email notifications to the console instead of sending real emails.
- `APPROVAL_API_URL` is auto-detected using your external IP if not set. Set it manually if you need a specific URL for email links.
- `ADK_API_URL`: Set to `http://127.0.0.1:8086` when using FastAPI server (recommended), or `http://127.0.0.1:8084` when using `adk web` for development.
- `AGENT_SERVER_PORT`: Everything runs on port **8086** now (agent + approvals in one server).
- `SESSION_SERVICE_URI`: Leave empty for development (in-memory sessions). For production, configure a persistent session service.

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

**This application now runs as a single unified server!** No need to run multiple terminals or services.

The FastAPI server includes:
- ✅ Agent endpoints (run agent, web UI, API docs)
- ✅ Approval endpoints (approve/reject callbacks)
- ✅ Utility endpoints (health check, feedback)

#### Start the All-in-One FastAPI Server

**Important:** Run from the `hitl-adk/` directory (same as `adk web .`).

```bash
# Navigate to hitl-adk directory
cd /path/to/hitl-adk

# Run the startup script (located in hitl-adk/)
bash start_agent_server.sh
```

Or run directly:
```bash
# From hitl-adk/ directory
python -m insurance_notification.server
```

The server will start on port **8086** by default.

**Expected Output:**
```
================================================================================
🚀 Insurance Notification Agent - All-in-One FastAPI Server
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

#### Access the Application

**Web Interface:**
Open your browser and navigate to:
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

### Alternative: ADK Web Server (Development Only)

For quick development/testing, you can still use the ADK web server:

```bash
# From the project root directory (hitl-adk)
adk web .
```

Runs on port **8084** by default. Access at `http://localhost:8084`

**Note:** When using `adk web`, you'll need to update your `.env`:
```bash
ADK_API_URL=http://127.0.0.1:8084  # Use port 8084 for adk web
```

**⚠️ Important:** The ADK web server does NOT include approval endpoints. For full HITL functionality, use the FastAPI server on port 8086.

### Example Interactions

**Claim Verification with Human-in-the-Loop Approval:**
```
User: "I need approval for claim CLM-001 from analyticsrepo@gmail.com"

Agent:
1. Retrieves claim details for CLM-001
2. Sends email with APPROVE/REJECT buttons to analyticsrepo@gmail.com
3. Pauses and waits for user response
4. (User clicks APPROVE in their email)
5. Agent automatically resumes execution
6. Sends confirmation email with next steps
```

**Claim Status Update:**
```
User: "Check claim CLM-001 and send an email to analyticsrepo@gmail.com"

Agent:
- Retrieves claim details
- Sends formatted email with claim status
- Confirms notification sent
```

**Policy Renewal Reminder:**
```
User: "Check policy POL-67890 and send renewal reminder to analyticsrepo@gmail.com"

Agent:
- Checks policy status
- Detects upcoming renewal (4 days)
- Sends urgent renewal reminder email
```

**Custom Notification:**
```
User: "Send an email to analyticsrepo@gmail.com about our customer satisfaction survey"

Agent:
- Composes professional email
- Uses general notification template
- Sends email with survey information
```

## Human-in-the-Loop (HITL) Approval Workflow

This agent implements a sophisticated human-in-the-loop approval workflow that allows the agent to pause execution and wait for human approval before proceeding.

### How It Works

1. **Agent Requests Approval**: The agent calls the `request_claim_approval()` tool
2. **Email Sent**: An email with approve/reject buttons is sent to the user
3. **Agent Pauses**: The agent pauses execution and waits for user response
4. **User Responds**: User clicks APPROVE or REJECT button in their email
5. **Callback Received**: The approval API receives the callback
6. **Agent Resumes**: The API pushes the response back to ADK, automatically resuming the agent
7. **Agent Continues**: The agent processes the approval status and continues execution

### Architecture

```
┌─────────────────┐                    ┌──────────────────┐
│                 │  1. Request        │                  │
│   ADK Agent     │  Approval          │  Approval API    │
│   (Port 8084)   ├───────────────────>│  (Port 8085)     │
│                 │                    │                  │
└────────┬────────┘                    └────────┬─────────┘
         │                                      │
         │ 2. Send Email                        │
         │ with Approve/                        │
         │ Reject buttons                       │
         │                                      │
         v                                      │
    ┌─────────┐                                │
    │  User   │  3. Click                      │
    │  Email  │  Approve/Reject ───────────────┘
    └─────────┘                    4. Callback
                                      │
                                      v
                          5. Push FunctionResponse
                             to ADK /run endpoint
                                      │
                                      v
                          6. Agent automatically resumes
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
    customer_email="analyticsrepo@gmail.com",
    user_id="customer001",  # Optional - auto-detected from context
    session_id="test_session_001"  # Optional - auto-detected from context
)
```

**Note:** The `user_id` and `session_id` are automatically extracted from the tool context, so you don't need to provide them manually.

## Tools Available

### 1. `send_email_notification()`
Sends HTML-formatted email notifications to customers.

**Parameters:**
- `recipient_email` (str): Email address of recipient
- `subject` (str): Email subject line
- `message` (str): Email body content
- `notification_type` (str): Type of notification (claim_update, policy_renewal, payment_reminder, general)

**Returns:**
- Status, recipient, subject, and send confirmation

### 2. `get_claim_status()`
Retrieves current status of an insurance claim.

**Parameters:**
- `claim_id` (str): Claim ID to look up

**Returns:**
- Claim details including status, amounts, and dates

**Demo Claims:**
- `CLM-001`: Approved auto accident claim ($4,500 approved)
- `CLM-002`: Pending property damage claim ($12,000 claimed)

### 3. `check_policy_status()`
Checks status of an insurance policy.

**Parameters:**
- `policy_number` (str): Policy number to look up

**Returns:**
- Policy details including status, premium, coverage, and renewal date

**Demo Policies:**
- `POL-12345`: Active auto insurance policy (65 days until renewal)
- `POL-67890`: Home insurance pending renewal (4 days until renewal)

### 4. `request_claim_approval()` (Long-Running Tool)
Requests approval for a claim submission via email with approve/reject buttons.

**Parameters:**
- `claim_id` (str): The claim ID requiring approval
- `customer_email` (str): Email address to send approval request to
- `user_id` (str): User ID for the ADK session (optional - auto-detected)
- `session_id` (str): Session ID for the ADK session (optional - auto-detected)

**Returns:**
- Status, ticket ID, claim ID, and approval URLs

**Behavior:**
- Sends an email with clickable approve/reject buttons
- Creates an approval ticket in the system
- Returns "pending" status
- When user responds, the approval API automatically pushes the response back to ADK
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
To: analyticsrepo@gmail.com
Subject: Claim Status Update - CLM-001
Type: claim_update
Message: Your claim has been approved...
```

### Production Mode
When SMTP credentials are configured, real emails are sent via Gmail:

```
✅ Email notification sent successfully
Recipient: analyticsrepo@gmail.com
Subject: Claim Status Update
Status: Delivered
```

## Email Template

All emails use a professional HTML template with:
- Insurance company branding header
- Notification type badge
- Formatted message content
- Automated disclaimer footer

Example email structure:
```
┌─────────────────────────────────┐
│   Insurance Notification        │  ← Header
├─────────────────────────────────┤
│ Notification Type: Claim Update │  ← Type
│ ──────────────────────────────  │
│                                 │
│ [Your message content here]     │  ← Message
│                                 │
│ ──────────────────────────────  │
│ Automated notification...       │  ← Footer
└─────────────────────────────────┘
```

## Customization

### Adding New Notification Types

Edit `tools.py` to add custom notification types in the email template.

### Adding More Claims/Policies

Edit the simulated databases in `tools.py`:
- `claims` dictionary in `get_claim_status()`
- `policies` dictionary in `check_policy_status()`

### Changing Email Recipient

The default recipient is `analyticsrepo@gmail.com`. To change:
- Modify the agent instruction in `agent.py`, or
- Specify a different email in your query

### Customizing Agent Behavior

Edit the `instruction` field in `agent.py` to change how the agent handles different scenarios.

## Troubleshooting

**Email Not Sending:**
- Check `SENDER_EMAIL` and `SENDER_PASSWORD` in `.env`
- Verify Gmail App Password is correct
- Ensure "Less secure app access" is enabled (if not using App Password)
- Check SMTP server and port settings

**Agent Not Responding:**
- Verify `GOOGLE_CLOUD_PROJECT` is set correctly
- Ensure you've authenticated with `gcloud auth application-default login`
- Check that Vertex AI API is enabled in your project

**Import Errors:**
- Make sure you're running from the correct directory
- Install missing dependencies: `pip install google-adk python-dotenv`

## Extending the Agent

You can extend this agent by:

1. **Integrating with Real Databases**: Replace simulated data with actual database queries
2. **Adding More Tools**: Create tools for premium calculations, policy modifications, etc.
3. **Multi-Channel Notifications**: Add SMS, push notifications, or webhooks
4. **Additional Approval Workflows**: Extend the HITL pattern to other operations (policy changes, large payments, etc.)
5. **Customer Authentication**: Add user verification before sharing sensitive information
6. **Scheduled Reminders**: Set up automated renewal reminders using cron jobs
7. **Approval Dashboard**: Create a web dashboard to view and manage pending approvals
8. **Approval Analytics**: Track approval metrics, response times, and patterns

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

## License

Copyright 2025 Google LLC

Licensed under the Apache License, Version 2.0

## Support

For issues or questions:
- Check the ADK documentation: https://google.github.io/adk-python/
- Review ADK samples: https://github.com/google/adk-python/tree/main/samples
- File an issue in your project repository

## Example Output

```bash
$ python main.py

======================================================================
🏢 INSURANCE NOTIFICATION AGENT - DEMO
======================================================================

📋 SCENARIO 1: Claim Status Update
======================================================================
👤 Customer Query: Please check the status of claim CLM-001...
----------------------------------------------------------------------
🤖 Agent: I'll check the claim status and send a notification.
   🔧 Tool Call: get_claim_status()
   ✅ Tool Response: {'status': 'found', 'claim': {...}}
   🔧 Tool Call: send_email_notification()
   ✅ Tool Response: {'status': 'success', 'demo_mode': True}
🤖 Agent: I've sent the claim update email to analyticsrepo@gmail.com

📧 EMAIL NOTIFICATION (Demo Mode - Not Actually Sent)
To: analyticsrepo@gmail.com
Subject: Claim CLM-001 - Approved
Type: claim_update
Message: Good news! Your auto accident claim has been approved...
============================================================
```

---

Built with ❤️ using Google Agent Development Kit (ADK)
# insurance_notification_v2
