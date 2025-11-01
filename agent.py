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

import os
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.long_running_tool import LongRunningFunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from .approval_manager import approval_manager

# Load environment variables
load_dotenv()


def send_email_notification(
    recipient_email: str,
    subject: str,
    message: str,
    notification_type: str
) -> Dict[str, Any]:
    """
    Send email notification to insurance customer.

    Args:
        recipient_email: Email address of the recipient
        subject: Email subject line
        message: Email message body
        notification_type: Type of notification (claim_update, policy_renewal, payment_reminder, general)

    Returns:
        Dictionary with status and details
    """
    try:
        # Get email credentials from environment variables
        sender_email = os.getenv("SENDER_EMAIL", "noreply@insurance.com")
        sender_password = os.getenv("SENDER_PASSWORD", "")
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email

        # Create email body with HTML formatting
        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <div style="background-color: #0066cc; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                <h2 style="margin: 0;">Insurance Notification</h2>
              </div>
              <div style="border: 1px solid #ddd; padding: 20px; border-radius: 0 0 5px 5px;">
                <p><strong>Notification Type:</strong> {notification_type.replace('_', ' ').title()}</p>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <div style="margin: 20px 0;">
                  {message}
                </div>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px; margin-top: 20px;">
                  This is an automated notification from your insurance company.
                  Please do not reply to this email.
                </p>
              </div>
            </div>
          </body>
        </html>
        """

        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # For demo purposes, if no password is set, just return success without actually sending
        if not sender_password:
            print(f"\n📧 EMAIL NOTIFICATION (Demo Mode - Not Actually Sent)")
            print(f"To: {recipient_email}")
            print(f"Subject: {subject}")
            print(f"Type: {notification_type}")
            print(f"Message: {message}")
            print("=" * 60)
            return {
                "status": "success",
                "message": "Email notification sent successfully (demo mode)",
                "recipient": recipient_email,
                "subject": subject,
                "notification_type": notification_type,
                "demo_mode": True
            }

        # Send actual email if credentials are provided
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return {
            "status": "success",
            "message": "Email notification sent successfully",
            "recipient": recipient_email,
            "subject": subject,
            "notification_type": notification_type,
            "demo_mode": False
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
            "recipient": recipient_email,
            "error": str(e)
        }


def get_claim_status(claim_id: str) -> Dict[str, Any]:
    """
    Retrieve the current status of an insurance claim.

    Args:
        claim_id: The claim ID to look up

    Returns:
        Dictionary with claim details
    """
    # Simulated claim database
    claims = {
        "CLM-001": {
            "claim_id": "CLM-001",
            "status": "approved",
            "claim_type": "auto_accident",
            "claim_amount": 5000.00,
            "approved_amount": 4500.00,
            "filed_date": "2025-10-15",
            "updated_date": "2025-10-25"
        },
        "CLM-002": {
            "claim_id": "CLM-002",
            "status": "pending_review",
            "claim_type": "property_damage",
            "claim_amount": 12000.00,
            "approved_amount": 0,
            "filed_date": "2025-10-20",
            "updated_date": "2025-10-20"
        }
    }

    claim = claims.get(claim_id)
    if claim:
        return {
            "status": "found",
            "claim": claim
        }
    else:
        return {
            "status": "not_found",
            "message": f"Claim {claim_id} not found in system"
        }


def check_policy_status(policy_number: str) -> Dict[str, Any]:
    """
    Check the status of an insurance policy.

    Args:
        policy_number: The policy number to look up

    Returns:
        Dictionary with policy details
    """
    # Simulated policy database
    policies = {
        "POL-12345": {
            "policy_number": "POL-12345",
            "policy_type": "auto_insurance",
            "status": "active",
            "premium": 1200.00,
            "coverage_amount": 100000.00,
            "start_date": "2025-01-01",
            "renewal_date": "2026-01-01",
            "days_until_renewal": 65
        },
        "POL-67890": {
            "policy_number": "POL-67890",
            "policy_type": "home_insurance",
            "status": "pending_renewal",
            "premium": 1800.00,
            "coverage_amount": 500000.00,
            "start_date": "2024-11-01",
            "renewal_date": "2025-11-01",
            "days_until_renewal": 4
        }
    }

    policy = policies.get(policy_number)
    if policy:
        return {
            "status": "found",
            "policy": policy
        }
    else:
        return {
            "status": "not_found",
            "message": f"Policy {policy_number} not found in system"
        }


def request_claim_approval(
    claim_id: str,
    customer_email: str,
    user_id: str = "customer001",
    session_id: str = "default_session",
    tool_context: ToolContext = None
) -> Dict[str, Any]:
    """
    Request approval for a claim submission. This is a long-running tool that sends
    an email with approve/reject buttons and waits for user response.

    Args:
        claim_id: The claim ID requiring approval
        customer_email: Email address to send approval request to
        user_id: User ID for the ADK session (default: customer001)
        session_id: Session ID for the ADK session (default: default_session)
        tool_context: ADK tool context for long-running operations

    Returns:
        Dictionary with status and ticket information
    """
    # Get claim details
    claim_result = get_claim_status(claim_id)

    if claim_result.get("status") == "not_found":
        return {
            "status": "error",
            "message": f"Claim {claim_id} not found"
        }

    claim = claim_result.get("claim", {})

    # Extract session info from tool_context to enable resuming the agent
    import sys
    if tool_context:
        print(f"🔍 tool_context type: {type(tool_context)}", file=sys.stderr)
        print(f"🔍 tool_context attributes: {dir(tool_context)}", file=sys.stderr)

        # Get function_call_id
        function_call_id = getattr(tool_context, 'function_call_id', None)

        # Try to extract user_id and session_id from _invocation_context
        actual_user_id = None
        actual_session_id = None

        invocation_context = getattr(tool_context, '_invocation_context', None)
        if invocation_context:
            print(f"🔍 _invocation_context type: {type(invocation_context)}", file=sys.stderr)
            print(f"🔍 _invocation_context attributes: {dir(invocation_context)}", file=sys.stderr)

            actual_user_id = getattr(invocation_context, 'user_id', None)
            actual_session_id = getattr(invocation_context, 'session_id', None)

            # Try to get session_id from the session object
            session = getattr(invocation_context, 'session', None)
            if session:
                print(f"🔍 session type: {type(session)}", file=sys.stderr)
                print(f"🔍 session attributes: {dir(session)}", file=sys.stderr)

                # Try different possible attributes
                if hasattr(session, 'session_id'):
                    actual_session_id = session.session_id
                elif hasattr(session, 'id'):
                    actual_session_id = session.id
                elif hasattr(session, 'uuid'):
                    actual_session_id = session.uuid

                print(f"🔍 Extracted session_id from session object: {actual_session_id}", file=sys.stderr)

            print(f"🔍 Extracted from _invocation_context: user_id={actual_user_id}, session_id={actual_session_id}", file=sys.stderr)

        # If we couldn't extract from context, fall back to parameters
        if not actual_user_id:
            actual_user_id = user_id
        if not actual_session_id:
            actual_session_id = session_id
    else:
        actual_user_id = user_id
        actual_session_id = session_id
        function_call_id = None

    session_info = {
        "app_name": "insurance_notification_v2",
        "user_id": actual_user_id,
        "session_id": actual_session_id,
        "function_call_id": function_call_id
    }

    print(f"🔍 Final session info: user_id={actual_user_id}, session_id={actual_session_id}, function_call_id={function_call_id}", file=sys.stderr)

    # Create approval request
    approval_request = approval_manager.create_approval_request(
        claim_id=claim_id,
        user_email=customer_email,
        request_type="claim_verification",
        metadata={
            "claim": claim,
            "session_info": session_info
        },
        function_call_id=session_info["function_call_id"]
    )

    ticket_id = approval_request.ticket_id

    # Get approval API server URL (same as agent server in unified deployment)
    approval_api_url = os.getenv("APPROVAL_API_URL")

    if not approval_api_url:
        # Dynamically get external IP
        try:
            external_ip = subprocess.check_output(
                ["curl", "-s", "ifconfig.me"],
                timeout=5
            ).decode('utf-8').strip()
            approval_port = os.getenv("AGENT_SERVER_PORT", "8086")
            approval_api_url = f"http://{external_ip}:{approval_port}"
        except Exception:
            # Fallback to localhost if external IP detection fails
            approval_api_url = "http://localhost:8086"

    # Generate approve/reject URLs
    approve_url = f"{approval_api_url}/api/approve/{ticket_id}"
    reject_url = f"{approval_api_url}/api/reject/{ticket_id}"

    # Send email with approval buttons
    email_subject = f"Action Required: Verify Claim Submission - {claim_id}"
    email_body = f"""
    <h3>Claim Verification Required</h3>

    <p>We received a request related to claim <strong>{claim_id}</strong>.</p>

    <p><strong>Claim Details:</strong></p>
    <ul>
        <li>Claim ID: {claim.get('claim_id', 'N/A')}</li>
        <li>Type: {claim.get('claim_type', 'N/A').replace('_', ' ').title()}</li>
        <li>Amount: ${claim.get('claim_amount', 0):,.2f}</li>
        <li>Status: {claim.get('status', 'N/A').replace('_', ' ').title()}</li>
        <li>Filed Date: {claim.get('filed_date', 'N/A')}</li>
    </ul>

    <p><strong>Please confirm:</strong> Did you submit this claim via mail?</p>

    <div style="margin: 30px 0; text-align: center;">
        <a href="{approve_url}"
           style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none;
                  border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
            ✓ YES, I SUBMITTED THIS CLAIM
        </a>

        <a href="{reject_url}"
           style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none;
                  border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
            ✗ NO, I DID NOT SUBMIT THIS
        </a>
    </div>

    <p style="margin-top: 30px; color: #666; font-size: 12px;">
        <strong>Ticket ID:</strong> {ticket_id}<br>
        Click one of the buttons above to confirm. This is a one-time action and cannot be undone.
    </p>
    """

    # Send the approval email
    email_result = send_email_notification(
        recipient_email=customer_email,
        subject=email_subject,
        message=email_body,
        notification_type="claim_verification"
    )

    if email_result.get("status") != "success":
        return {
            "status": "error",
            "message": "Failed to send approval email",
            "error": email_result.get("message")
        }

    # Return pending status - the agent will wait for approval
    return {
        "status": "pending",
        "ticket_id": ticket_id,
        "claim_id": claim_id,
        "message": f"Approval request sent to {customer_email}. Awaiting response.",
        "approve_url": approve_url,
        "reject_url": reject_url
    }


# Insurance Customer Service Agent
root_agent = Agent(
    model='gemini-2.5-flash',
    name='insurance_notification_agent',
    instruction="""
    You are a helpful insurance customer service agent for an insurance company.
    Your primary responsibilities are:

    1. **Claim Status Updates**: Check claim status and notify customers via email
    2. **Policy Information**: Provide policy details and renewal reminders
    3. **Email Notifications**: Send formatted email notifications to customers
    4. **Claim Verification**: Request customer approval for claim submissions via email with approve/reject buttons

    **Important Guidelines:**
    - Always be professional and empathetic when dealing with insurance matters
    - When sending email notifications, use clear and concise language
    - For claim updates, include relevant details like claim ID, status, and amounts
    - For policy renewals, mention renewal dates and any action required
    - Use the default recipient email: analyticsrepo@gmail.com unless specified otherwise

    **Email Notification Types:**
    - claim_update: For claim status changes
    - policy_renewal: For policy renewal reminders
    - payment_reminder: For payment due notices
    - claim_verification: For approval requests
    - general: For general insurance communications

    **Approval Workflow (Human-in-the-Loop):**
    - Use request_claim_approval when you need to verify that a customer submitted a claim
    - This is a long-running tool that sends an email with approve/reject buttons
    - IMPORTANT: When calling request_claim_approval, you must provide:
      - claim_id: The claim ID to verify
      - customer_email: The email to send the approval request to
      - user_id: "customer001" (or the appropriate user ID)
      - session_id: "test_session_001" (or the appropriate session ID)
    - The agent will pause and wait for the customer to click approve or reject
    - Once the customer responds, the agent will resume and can proceed with next steps
    - After approval, send a final confirmation email using send_email_notification

    **Standard Workflow:**
    1. When asked about a claim, first use get_claim_status to retrieve details
    2. If verification is needed, use request_claim_approval to get customer confirmation
    3. Otherwise, send an email notification with the claim information
    4. For policy inquiries, use check_policy_status first
    5. Always confirm after sending an email notification

    Be proactive in sending notifications when you detect important updates or upcoming deadlines.
    """,
    tools=[
        send_email_notification,
        get_claim_status,
        check_policy_status,
        LongRunningFunctionTool(func=request_claim_approval)
    ],
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # Lower temperature for consistent, professional responses
    ),
)
