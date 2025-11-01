#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
FastAPI server for the Insurance Notification Agent.
Wraps the ADK agent in a FastAPI application for production deployment.
Includes both the agent endpoints and approval API endpoints in a single server.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel
from typing import Literal
from google.cloud import logging as google_cloud_logging
import httpx


# Load environment variables from .env file
load_dotenv()

logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)

# AGENT_DIR should point to hitl-adk/ (parent of insurance_notification/)
# This allows the server to find all agent directories, just like 'adk web .'
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Get session service URI from environment variables
session_uri = os.getenv("SESSION_SERVICE_URI", None)

# Prepare arguments for get_fast_api_app
app_args = {"agents_dir": AGENT_DIR, "web": True, "trace_to_cloud": True}

# Only include session_service_uri if it's provided
if session_uri:
    app_args["session_service_uri"] = session_uri
else:
    logger.log_text(
        "SESSION_SERVICE_URI not provided. Using in-memory session service instead. "
        "All sessions will be lost when the server restarts.",
        severity="WARNING",
    )

# Create FastAPI app with appropriate arguments
app: FastAPI = get_fast_api_app(**app_args)

app.title = "insurance-notification-agent"
app.description = (
    "API for interacting with the Insurance Notification Agent. "
    "This agent provides email notifications, claim status tracking, "
    "policy management, and human-in-the-loop approval workflows. "
    "This server includes both agent endpoints and approval callback endpoints."
)


class Feedback(BaseModel):
    """Represents feedback for a conversation."""

    score: int | float
    text: str | None = ""
    invocation_id: str
    log_type: Literal["feedback"] = "feedback"
    service_name: Literal["insurance-notification-agent"] = "insurance-notification-agent"
    user_id: str = ""


class ApprovalStatus(BaseModel):
    """Status of pending approvals."""

    ticket_id: str
    claim_id: str
    user_email: str
    status: str
    created_at: str


# =============================================================================
# Helper Functions for Approval Workflow
# =============================================================================

async def push_response_to_adk(approval_request: dict, approval_status: str):
    """
    Push the FunctionResponse back to ADK to resume agent execution.

    Args:
        approval_request: The approval request data
        approval_status: "approved" or "rejected"
    """
    print(f"\n{'='*80}")
    print(f"🔄 PUSH_RESPONSE_TO_ADK CALLED")
    print(f"{'='*80}")
    print(f"Approval Status: {approval_status}")
    print(f"Ticket ID: {approval_request.get('ticket_id')}")

    try:
        session_info = approval_request.get("metadata", {}).get("session_info", {})
        function_call_id = approval_request.get("function_call_id")

        print(f"Session Info: {session_info}")
        print(f"Function Call ID: {function_call_id}")

        if not function_call_id or not session_info:
            print(f"⚠️  Missing session info, cannot resume agent automatically")
            print(f"   - function_call_id present: {bool(function_call_id)}")
            print(f"   - session_info present: {bool(session_info)}")
            return False

        # Get ADK API server URL (this same server)
        port = int(os.getenv("AGENT_SERVER_PORT", "8086"))
        adk_api_url = os.getenv("ADK_API_URL", f"http://127.0.0.1:{port}")

        # Prepare the function response
        function_response = {
            "status": "success",
            "approval_status": approval_status,
            "ticket_id": approval_request.get("ticket_id"),
            "claim_id": approval_request.get("claim_id"),
            "message": f"Claim verification {approval_status} by user"
        }

        # Push the response to ADK to resume the agent
        push_url = f"{adk_api_url}/run"
        payload = {
            "app_name": session_info.get("app_name"),
            "user_id": session_info.get("user_id"),
            "session_id": session_info.get("session_id"),
            "new_message": {
                "role": "function",
                "parts": [{
                    "function_response": {
                        "name": "request_claim_approval",
                        "id": function_call_id,
                        "response": function_response
                    }
                }]
            }
        }

        print(f"📤 Pushing FunctionResponse to ADK: {push_url}")
        print(f"   Session: {session_info.get('user_id')}/{session_info.get('session_id')}")
        print(f"   Function Call ID: {function_call_id}")
        print(f"   Status: {approval_status}")
        print(f"   Payload: {payload}")

        print(f"\n🌐 Making HTTP POST request...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(push_url, json=payload)

            print(f"\n📥 Response received:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Text (first 500 chars): {response.text[:500]}")

            if response.status_code == 200:
                print(f"✅ Successfully resumed agent with approval status: {approval_status}")
                print(f"{'='*80}\n")
                return True
            else:
                print(f"❌ Failed to resume agent: {response.status_code}")
                print(f"   Full Response: {response.text}")
                print(f"{'='*80}\n")
                return False

    except Exception as e:
        print(f"\n❌ EXCEPTION in push_response_to_adk:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        print("\n📋 Full Traceback:")
        traceback.print_exc()
        print(f"{'='*80}\n")
        return False


# =============================================================================
# Agent Endpoints (from ADK)
# =============================================================================

# These are automatically provided by get_fast_api_app():
# - POST /run - Run the agent
# - GET /apps - List available apps
# - GET /dev-ui/ - Web interface
# - And all other ADK routes


# =============================================================================
# Custom Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint showing all available services."""
    return {
        "service": "Insurance Notification Agent - All-in-One Server",
        "version": "2.0.0",
        "endpoints": {
            "agent": {
                "run": "POST /run",
                "apps": "GET /apps",
                "web_ui": "GET /dev-ui/",
                "docs": "GET /docs"
            },
            "approvals": {
                "approve": "GET /api/approve/{ticket_id}",
                "reject": "GET /api/reject/{ticket_id}",
                "status": "GET /api/status/{ticket_id}",
                "pending": "GET /api/approvals/pending"
            },
            "utilities": {
                "health": "GET /health",
                "feedback": "POST /feedback"
            }
        }
    }


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "insurance-notification-agent",
        "version": "2.0.0",
    }


# =============================================================================
# Approval API Endpoints (merged from approval_api.py)
# =============================================================================

@app.get("/api/approve/{ticket_id}")
async def approve_request(ticket_id: str):
    """
    Approve an approval request.
    This endpoint is called when a user clicks the APPROVE button in their email.
    Automatically pushes the response back to ADK to resume the agent.
    """
    from .approval_manager import approval_manager

    # Get the approval request before updating it
    approval_request = approval_manager.get_approval(ticket_id)
    if not approval_request:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # Convert to dict for easier handling
    from dataclasses import asdict
    approval_dict = asdict(approval_request)

    # Update approval status
    result = approval_manager.approve(ticket_id, approver_notes="Approved via email link")

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    # Push the response back to ADK to resume the agent
    await push_response_to_adk(approval_dict, "approved")

    # Return a nice HTML response
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claim Approved</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                text-align: center;
            }}
            .success {{
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .checkmark {{
                font-size: 48px;
                color: #28a745;
            }}
            .details {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="checkmark">✓</div>
        <div class="success">
            <h2>Claim Approved Successfully</h2>
            <p>Thank you for verifying your claim submission.</p>
        </div>
        <div class="details">
            <p><strong>Ticket ID:</strong> {ticket_id}</p>
            <p><strong>Claim ID:</strong> {result.get('claim_id', 'N/A')}</p>
            <p><strong>Status:</strong> Approved</p>
            <p><strong>Next Steps:</strong> You will receive a confirmation email shortly with the claim processing details.</p>
        </div>
        <p style="color: #666; margin-top: 30px;">
            You may now close this window.
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/api/reject/{ticket_id}")
async def reject_request(ticket_id: str):
    """
    Reject an approval request.
    This endpoint is called when a user clicks the REJECT button in their email.
    Automatically pushes the response back to ADK to resume the agent.
    """
    from .approval_manager import approval_manager

    # Get the approval request before updating it
    approval_request = approval_manager.get_approval(ticket_id)
    if not approval_request:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    # Convert to dict for easier handling
    from dataclasses import asdict
    approval_dict = asdict(approval_request)

    # Update approval status
    result = approval_manager.reject(ticket_id, rejection_reason="Rejected via email link")

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])

    # Push the response back to ADK to resume the agent
    await push_response_to_adk(approval_dict, "rejected")

    # Return a nice HTML response
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claim Rejected</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                text-align: center;
            }}
            .warning {{
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .xmark {{
                font-size: 48px;
                color: #dc3545;
            }}
            .details {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="xmark">✗</div>
        <div class="warning">
            <h2>Claim Submission Rejected</h2>
            <p>You have indicated that you did not submit this claim.</p>
        </div>
        <div class="details">
            <p><strong>Ticket ID:</strong> {ticket_id}</p>
            <p><strong>Claim ID:</strong> {result.get('claim_id', 'N/A')}</p>
            <p><strong>Status:</strong> Rejected</p>
            <p><strong>Next Steps:</strong> Our security team will investigate this matter. You will receive a follow-up email within 24 hours.</p>
        </div>
        <p style="color: #666; margin-top: 30px;">
            If you have any concerns, please contact our customer service immediately.
        </p>
        <p style="color: #666;">
            You may now close this window.
        </p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/api/status/{ticket_id}")
async def get_status(ticket_id: str):
    """
    Get the status of an approval request.
    """
    from .approval_manager import approval_manager

    request = approval_manager.get_approval(ticket_id)

    if not request:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return {
        "ticket_id": request.ticket_id,
        "claim_id": request.claim_id,
        "status": request.status,
        "request_type": request.request_type,
        "created_at": request.created_at,
        "updated_at": request.updated_at
    }


@app.get("/api/approvals/pending")
def get_pending_approvals() -> dict:
    """Get all pending approval requests.

    Returns:
        List of pending approval requests
    """
    from .approval_manager import approval_manager

    pending = approval_manager.get_all_pending()
    return {
        "count": len(pending),
        "pending_approvals": [
            {
                "ticket_id": req.ticket_id,
                "claim_id": req.claim_id,
                "user_email": req.user_email,
                "request_type": req.request_type,
                "created_at": req.created_at
            }
            for req in pending
        ]
    }


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    port = int(os.getenv("AGENT_SERVER_PORT", "8086"))

    print("=" * 80)
    print("🚀 Insurance Notification Agent - All-in-One FastAPI Server")
    print("=" * 80)
    print(f"")
    print(f"Server running at: http://0.0.0.0:{port}")
    print(f"")
    print(f"📋 AGENT ENDPOINTS:")
    print(f"  - POST /run                       - Run the agent")
    print(f"  - GET  /apps                      - List available apps")
    print(f"  - GET  /dev-ui/                   - Web interface")
    print(f"  - GET  /docs                      - Interactive API docs")
    print(f"")
    print(f"✅ APPROVAL ENDPOINTS (Human-in-the-Loop):")
    print(f"  - GET  /api/approve/{{ticket_id}}   - Approve a request")
    print(f"  - GET  /api/reject/{{ticket_id}}    - Reject a request")
    print(f"  - GET  /api/status/{{ticket_id}}    - Get request status")
    print(f"  - GET  /api/approvals/pending     - List pending approvals")
    print(f"")
    print(f"🔧 UTILITY ENDPOINTS:")
    print(f"  - GET  /health                    - Health check")
    print(f"  - POST /feedback                  - Submit feedback")
    print(f"  - GET  /                          - API overview")
    print(f"")
    print(f"✨ This is a unified server - no need to run approval_api.py separately!")
    print("=" * 80)
    print()

    uvicorn.run(app, host="0.0.0.0", port=port)
