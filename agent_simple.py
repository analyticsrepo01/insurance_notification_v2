#!/usr/bin/env python3
"""
Simplified Insurance Notification Agent - ADK HITL Mechanics Demo

This is a minimal example showing the core ADK Human-in-the-Loop pattern.
Stripped of all email/HTML complexity to focus on the mechanics.

Based on: https://github.com/Shaveen12/HumanInTheLoop
"""

import os
import sys
from google.genai.types import Tool, FunctionDeclaration, Schema, Type
from google.adk.agents import Agent
from google.adk.sessions.in_memory_session_service import InMemorySessionService


# =============================================================================
# Simple In-Memory Storage (replaces approval_manager.py)
# =============================================================================

class SimpleApprovalStore:
    """Minimal approval storage - just a dict"""
    def __init__(self):
        self.approvals = {}

    def create(self, ticket_id, claim_id, status="pending"):
        self.approvals[ticket_id] = {
            "ticket_id": ticket_id,
            "claim_id": claim_id,
            "status": status
        }
        return self.approvals[ticket_id]

    def update(self, ticket_id, status):
        if ticket_id in self.approvals:
            self.approvals[ticket_id]["status"] = status
            return True
        return False

    def get(self, ticket_id):
        return self.approvals.get(ticket_id)

# Global store
approval_store = SimpleApprovalStore()


# =============================================================================
# Simple Tool Function (replaces complex email logic)
# =============================================================================

def request_approval(claim_id: str, tool_context=None) -> dict:
    """
    Minimal HITL approval tool.

    Instead of sending emails, just prints a message with approval URL.
    The key HITL mechanic: returns status="pending" and waits.

    Args:
        claim_id: ID of claim to approve
        tool_context: Injected by ADK (contains session info)

    Returns:
        dict with status="pending" and approval info
    """
    import uuid

    # Generate simple ticket ID
    ticket_id = f"TICKET-{uuid.uuid4().hex[:8].upper()}"

    # Extract session info from tool_context (ADK provides this)
    session_id = None
    if tool_context and hasattr(tool_context, '_invocation_context'):
        inv_ctx = tool_context._invocation_context
        if hasattr(inv_ctx, 'session') and hasattr(inv_ctx.session, 'id'):
            session_id = inv_ctx.session.id

    # Store approval request
    approval_store.create(ticket_id, claim_id, status="pending")

    # Print approval info (in real app, this would send email)
    print("\n" + "="*80, file=sys.stderr)
    print("🔔 APPROVAL REQUEST", file=sys.stderr)
    print("="*80, file=sys.stderr)
    print(f"Ticket ID: {ticket_id}", file=sys.stderr)
    print(f"Claim ID: {claim_id}", file=sys.stderr)
    print(f"Session ID: {session_id}", file=sys.stderr)
    print(f"\nApprove: GET /api/approve/{ticket_id}", file=sys.stderr)
    print(f"Reject:  GET /api/reject/{ticket_id}", file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    # KEY HITL MECHANIC: Return status="pending"
    # This tells ADK the tool is waiting for external input
    return {
        "status": "pending",
        "ticket_id": ticket_id,
        "claim_id": claim_id,
        "message": f"Approval request created. Waiting for response on ticket {ticket_id}"
    }


# =============================================================================
# Simple Data Lookup Tools
# =============================================================================

def get_claim_status(claim_id: str) -> dict:
    """Simple claim lookup - hardcoded data"""
    claims = {
        "CLM-001": {
            "claim_id": "CLM-001",
            "status": "approved",
            "amount": 4500,
            "type": "auto_accident"
        },
        "CLM-002": {
            "claim_id": "CLM-002",
            "status": "pending",
            "amount": 12000,
            "type": "property_damage"
        }
    }

    claim = claims.get(claim_id)
    if claim:
        return {"status": "found", "claim": claim}
    else:
        return {"status": "not_found", "claim_id": claim_id}


# =============================================================================
# Agent Configuration
# =============================================================================

# Define tools for the agent
tools = [
    Tool(
        function_declarations=[
            FunctionDeclaration(
                name="get_claim_status",
                description="Retrieve the current status of an insurance claim",
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "claim_id": Schema(
                            type=Type.STRING,
                            description="The claim ID to look up (e.g., CLM-001)"
                        )
                    },
                    required=["claim_id"]
                )
            ),
            FunctionDeclaration(
                name="request_approval",
                description=(
                    "Request human approval for a claim. "
                    "This is a LONG-RUNNING tool that pauses execution. "
                    "Use this when you need explicit user confirmation."
                ),
                parameters=Schema(
                    type=Type.OBJECT,
                    properties={
                        "claim_id": Schema(
                            type=Type.STRING,
                            description="The claim ID requiring approval"
                        )
                    },
                    required=["claim_id"]
                )
            )
        ]
    )
]

# Create the agent
agent = Agent(
    model="gemini-2.0-flash-exp",
    instruction=(
        "You are a simple insurance assistant. "
        "You can check claim status and request approvals. "
        "When asked to approve a claim, use the request_approval tool. "
        "Be concise in your responses."
    ),
    tools=tools,
    session_service=InMemorySessionService(),
    # KEY HITL CONFIG: Map tool to function and mark as long-running
    tool_choice={
        "get_claim_status": get_claim_status,
        "request_approval": {
            "function": request_approval,
            "is_long_running": True  # This enables HITL behavior
        }
    }
)


# =============================================================================
# Main Entry Point (for testing)
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("Simple HITL Agent - Interactive Demo")
    print("="*80)
    print("\nExample queries:")
    print("  - What is the status of claim CLM-001?")
    print("  - I need approval for claim CLM-001")
    print("\nType 'quit' to exit\n")

    session_id = "demo_session_001"

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            # Send message to agent
            response = agent.add_user_message(
                user_id="demo_user",
                session_id=session_id,
                message=user_input
            )

            # Print agent response
            if hasattr(response, 'text') and response.text:
                print(f"\nAgent: {response.text}")
            else:
                print(f"\nAgent: [Response received]")

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
