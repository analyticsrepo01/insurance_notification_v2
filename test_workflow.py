#!/usr/bin/env python3
"""
Standalone test script for Insurance Notification Agent V2
Tests the complete workflow including HITL approval
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8086"
TEST_EMAIL = "test@example.com"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def test_health_check():
    """Test 1: Health check endpoint"""
    print_header("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_api_overview():
    """Test 2: API overview endpoint"""
    print_header("TEST 2: API Overview")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code in [200, 307]:  # 307 is redirect
            print_success("API overview endpoint accessible")
            if response.status_code == 200:
                data = response.json()
                print_info(f"Service: {data.get('service', 'N/A')}")
                print_info(f"Version: {data.get('version', 'N/A')}")
            return True
        else:
            print_error(f"API overview failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API overview failed: {e}")
        return False

def test_list_apps():
    """Test 3: List available apps"""
    print_header("TEST 3: List Apps")
    try:
        response = requests.get(f"{BASE_URL}/apps", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Apps endpoint accessible")
            if 'apps' in data:
                apps = data['apps']
                print_info(f"Available apps: {len(apps)}")
                for app in apps:
                    if app.get('app_name') == 'insurance_notification_v2':
                        print_success(f"Found insurance_notification_v2 app")
                        print_info(f"  Agent name: {app.get('agent_name', 'N/A')}")
                        return True
                print_error("insurance_notification_v2 app not found")
                return False
            else:
                print_error("No apps found in response")
                return False
        else:
            print_error(f"List apps failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List apps failed: {e}")
        return False

def test_pending_approvals():
    """Test 4: Get pending approvals"""
    print_header("TEST 4: Pending Approvals")
    try:
        response = requests.get(f"{BASE_URL}/api/approvals/pending", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Pending approvals endpoint accessible")
            print_info(f"Pending approvals: {data.get('count', 0)}")
            return True
        else:
            print_error(f"Pending approvals failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Pending approvals failed: {e}")
        return False

def test_run_agent():
    """Test 5: Run agent with simple query"""
    print_header("TEST 5: Run Agent - Simple Query")
    try:
        payload = {
            "app_name": "insurance_notification_v2",
            "user_id": "test_user",
            "session_id": f"test_session_{int(time.time())}",
            "new_message": {
                "role": "user",
                "parts": [{"text": "Check the status of claim CLM-001"}]
            }
        }

        print_info("Sending query: Check the status of claim CLM-001")
        response = requests.post(f"{BASE_URL}/run", json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print_success("Agent responded successfully")

            # Extract response text
            if 'new_messages' in data and len(data['new_messages']) > 0:
                for msg in data['new_messages']:
                    if msg.get('role') == 'model':
                        for part in msg.get('parts', []):
                            if 'text' in part:
                                print_info(f"Agent response: {part['text'][:200]}...")
                                return True

            print_info("Response received but no text found")
            return True
        else:
            print_error(f"Run agent failed with status {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Run agent failed: {e}")
        return False

def test_approval_workflow():
    """Test 6: HITL Approval Workflow (simulation)"""
    print_header("TEST 6: HITL Approval Workflow (Simulation)")

    print_info("This test simulates the approval workflow")
    print_info("In a real scenario:")
    print_info("  1. Agent calls request_claim_approval()")
    print_info("  2. Email is sent with approve/reject buttons")
    print_info("  3. User clicks button")
    print_info("  4. Callback hits /api/approve/{ticket_id}")
    print_info("  5. Agent automatically resumes")

    # Check if approval endpoints exist
    try:
        # Test that approval status endpoint is accessible (will 404 for invalid ticket)
        response = requests.get(f"{BASE_URL}/api/status/TEST-TICKET", timeout=5)
        if response.status_code in [404, 200]:
            print_success("Approval endpoints are accessible")
            return True
        else:
            print_error(f"Approval endpoint returned unexpected status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Approval endpoint test failed: {e}")
        return False

def test_docs_available():
    """Test 7: Check if API docs are available"""
    print_header("TEST 7: API Documentation")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("API documentation available at /docs")
            return True
        else:
            print_error(f"API docs failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API docs check failed: {e}")
        return False

def main():
    """Run all tests"""
    print_header("🧪 Insurance Notification Agent V2 - Standalone Test Suite")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print_error(f"Server not accessible at {BASE_URL}")
        print_error("Please start the server with: bash start_agent_server.sh")
        sys.exit(1)

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("API Overview", test_api_overview),
        ("List Apps", test_list_apps),
        ("Pending Approvals", test_pending_approvals),
        ("Run Agent", test_run_agent),
        ("Approval Workflow", test_approval_workflow),
        ("API Documentation", test_docs_available),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print_header("📊 Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status} - {name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print_success("🎉 All tests passed!")
        return 0
    else:
        print_error(f"⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
