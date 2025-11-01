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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict


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
