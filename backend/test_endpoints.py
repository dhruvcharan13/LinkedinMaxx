"""
Test script for FastAPI endpoints and communication flow.
Run this after starting the backend server.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"


def test_health_check():
    """Test health check endpoint."""
    print("1. Testing GET /health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"   ✅ Health check passed")
        print(f"   Redis connected: {data.get('redis_connected', False)}")
        print(f"   Server running: {data.get('is_running', False)}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Backend not running on {BASE_URL}")
        print(f"   Start it with: cd backend && python3 main.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_get_pending_tasks():
    """Test getting pending tasks."""
    print("\n2. Testing GET /api/tasks/pending")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks/pending", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "success", "Expected success status"
        tasks = data.get("tasks", [])
        print(f"   ✅ Got {len(tasks)} pending tasks")
        for i, task in enumerate(tasks[:3], 1):
            print(f"   Task {i}:")
            print(f"     - Type: {task.get('type')}")
            print(f"     - Agent: {task.get('agent_name')}")
            print(f"     - Content: {task.get('content', '')[:50]}...")
            print(f"     - Task ID: {task.get('task_id')}")
        return tasks
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def test_approve_task(task_id, edited_content=None):
    """Test approving a task."""
    print(f"\n3. Testing POST /api/tasks/approve")
    print(f"   Task ID: {task_id}")
    if edited_content:
        print(f"   Edited content: {edited_content[:50]}...")
    try:
        payload = {"task_id": task_id}
        if edited_content:
            payload["edited_content"] = edited_content
        
        response = requests.post(
            f"{BASE_URL}/api/tasks/approve",
            json=payload,
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "success", "Expected success status"
        print(f"   ✅ Task approved successfully")
        print(f"   Message: {data.get('message')}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_reject_task(task_id):
    """Test rejecting a task."""
    print(f"\n4. Testing POST /api/tasks/reject")
    print(f"   Task ID: {task_id}")
    try:
        payload = {"task_id": task_id}
        response = requests.post(
            f"{BASE_URL}/api/tasks/reject",
            json=payload,
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("status") == "success", "Expected success status"
        print(f"   ✅ Task rejected successfully")
        print(f"   Message: {data.get('message')}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_queue_stats():
    """Test queue statistics endpoint."""
    print("\n5. Testing GET /api/queue-stats")
    try:
        response = requests.get(f"{BASE_URL}/api/queue-stats", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"   ✅ Queue stats:")
        print(f"     - Pending approval: {data.get('pending_approval', 0)}")
        print(f"     - Playwright post: {data.get('playwright_post', 0)}")
        print(f"     - Playwright message: {data.get('playwright_message', 0)}")
        print(f"     - Profiles scraped: {data.get('profiles_scraped', 0)}")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing FastAPI Endpoints")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Backend is not running. Please start it first:")
        print("   cd backend && python3 main.py")
        sys.exit(1)
    
    # Test 2: Get pending tasks
    tasks = test_get_pending_tasks()
    
    # Test 3: Approve a task (if available)
    if tasks:
        task = tasks[0]
        task_id = task.get("task_id")
        if task_id:
            # Test approval with edited content
            test_approve_task(task_id, "Edited content from API test")
            time.sleep(1)  # Wait for processing
    else:
        print("\n⚠️  No pending tasks to test approval")
        print("   Generate a task first using an agent")
    
    # Test 4: Queue stats
    test_queue_stats()
    
    print("\n" + "=" * 60)
    print("✅ All endpoint tests completed!")
    print("\nTo test with real tasks:")
    print("1. Generate a task using an agent")
    print("2. Run this test script again")
    print("3. Or test from the frontend at http://localhost:3000")


if __name__ == "__main__":
    main()

