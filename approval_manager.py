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
Approval Manager for Human-in-the-Loop workflows.
Tracks pending approvals and manages approval state.
Uses file-based persistence to share state across processes.
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import fcntl


@dataclass
class ApprovalRequest:
    """Represents a pending approval request."""
    ticket_id: str
    claim_id: str
    user_email: str
    request_type: str  # "claim_verification", "claim_approval", etc.
    status: str  # "pending", "approved", "rejected"
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    function_call_id: Optional[str] = None  # For resuming agent execution


class ApprovalManager:
    """Manages approval requests and their lifecycle with file-based persistence."""

    def __init__(self, storage_file: str = "/tmp/approval_requests.json"):
        self.storage_file = storage_file
        self.approval_callbacks: Dict[str, asyncio.Future] = {}
        # Ensure storage file exists
        if not os.path.exists(self.storage_file):
            self._save_to_file({})

    def _load_from_file(self) -> Dict[str, dict]:
        """Load approval requests from file with file locking."""
        try:
            with open(self.storage_file, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_to_file(self, data: Dict[str, dict]):
        """Save approval requests to file with file locking."""
        with open(self.storage_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def create_approval_request(
        self,
        claim_id: str,
        user_email: str,
        request_type: str = "claim_verification",
        metadata: Optional[Dict[str, Any]] = None,
        function_call_id: Optional[str] = None
    ) -> ApprovalRequest:
        """Create a new approval request."""
        ticket_id = f"APPROVAL-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow().isoformat()

        request = ApprovalRequest(
            ticket_id=ticket_id,
            claim_id=claim_id,
            user_email=user_email,
            request_type=request_type,
            status="pending",
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            function_call_id=function_call_id
        )

        # Save to file
        data = self._load_from_file()
        data[ticket_id] = asdict(request)
        self._save_to_file(data)

        return request

    def get_approval(self, ticket_id: str) -> Optional[ApprovalRequest]:
        """Get an approval request by ticket ID."""
        data = self._load_from_file()
        request_data = data.get(ticket_id)
        if request_data:
            return ApprovalRequest(**request_data)
        return None

    def approve(self, ticket_id: str, approver_notes: str = "") -> Dict[str, Any]:
        """Approve a request."""
        data = self._load_from_file()
        request_data = data.get(ticket_id)

        if not request_data:
            return {"status": "error", "message": f"Ticket {ticket_id} not found"}

        if request_data["status"] != "pending":
            return {
                "status": "error",
                "message": f"Ticket {ticket_id} already {request_data['status']}"
            }

        request_data["status"] = "approved"
        request_data["updated_at"] = datetime.utcnow().isoformat()
        request_data["metadata"]["approver_notes"] = approver_notes

        # Save updated data
        data[ticket_id] = request_data
        self._save_to_file(data)

        # Notify any waiting callbacks
        if ticket_id in self.approval_callbacks:
            future = self.approval_callbacks[ticket_id]
            if not future.done():
                future.set_result({"status": "approved", "ticket_id": ticket_id})

        return {
            "status": "success",
            "message": "Approval granted",
            "ticket_id": ticket_id,
            "claim_id": request_data["claim_id"],
            "approval_status": "approved"
        }

    def reject(self, ticket_id: str, rejection_reason: str = "") -> Dict[str, Any]:
        """Reject a request."""
        data = self._load_from_file()
        request_data = data.get(ticket_id)

        if not request_data:
            return {"status": "error", "message": f"Ticket {ticket_id} not found"}

        if request_data["status"] != "pending":
            return {
                "status": "error",
                "message": f"Ticket {ticket_id} already {request_data['status']}"
            }

        request_data["status"] = "rejected"
        request_data["updated_at"] = datetime.utcnow().isoformat()
        request_data["metadata"]["rejection_reason"] = rejection_reason

        # Save updated data
        data[ticket_id] = request_data
        self._save_to_file(data)

        # Notify any waiting callbacks
        if ticket_id in self.approval_callbacks:
            future = self.approval_callbacks[ticket_id]
            if not future.done():
                future.set_result({"status": "rejected", "ticket_id": ticket_id})

        return {
            "status": "success",
            "message": "Request rejected",
            "ticket_id": ticket_id,
            "claim_id": request_data["claim_id"],
            "approval_status": "rejected"
        }

    async def wait_for_approval(self, ticket_id: str, timeout: int = 3600) -> Dict[str, Any]:
        """Wait for an approval decision (async)."""
        data = self._load_from_file()
        request_data = data.get(ticket_id)

        if not request_data:
            return {"status": "error", "message": "Ticket not found"}

        if request_data["status"] != "pending":
            return request_data

        # Create a future to wait on
        future = asyncio.Future()
        self.approval_callbacks[ticket_id] = future

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "message": f"Approval request timed out after {timeout} seconds",
                "ticket_id": ticket_id
            }
        finally:
            # Clean up
            if ticket_id in self.approval_callbacks:
                del self.approval_callbacks[ticket_id]

    def get_all_pending(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        data = self._load_from_file()
        return [
            ApprovalRequest(**req_data)
            for req_data in data.values()
            if req_data["status"] == "pending"
        ]

    def cleanup_old_requests(self, max_age_hours: int = 24):
        """Remove old completed/rejected requests."""
        now = datetime.utcnow()
        data = self._load_from_file()
        to_remove = []

        for ticket_id, request_data in data.items():
            if request_data["status"] != "pending":
                created = datetime.fromisoformat(request_data["created_at"])
                age_hours = (now - created).total_seconds() / 3600
                if age_hours > max_age_hours:
                    to_remove.append(ticket_id)

        for ticket_id in to_remove:
            del data[ticket_id]

        if to_remove:
            self._save_to_file(data)


# Global approval manager instance
approval_manager = ApprovalManager()
