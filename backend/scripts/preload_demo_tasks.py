#!/usr/bin/env python3
"""
Preload Demo Tasks for Frontend Approval

This script pre-populates the tasks:pending_approval Redis queue with demo tasks
for the LinkedInMaxx demo. It creates:
- 2 message tasks (1 dating match, 1 recruiter)
- 2 comment tasks (predefined posts)

Usage:
    python3 scripts/preload_demo_tasks.py
    python3 scripts/preload_demo_tasks.py --clear
    python3 scripts/preload_demo_tasks.py --config scripts/demo_tasks_config.json
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.redis_client import RedisClient
from utils.logger import feedback, logger


# Default demo task data
DEFAULT_DEMO_TASKS = {
    "messages": [
        {
            "url": "https://www.linkedin.com/in/elrich-chen/",
            "name": "Elrich Chen",
            "content": "You clearly value seeking out a higher level of challenge and pushing boundaries—I admire that drive. Let's grab a coffee and see if we can challenge each other with some great conversation?",
            "agent_name": "Dating Agent",
            "agent_emoji": "💕",
            "metadata": {
                "action": "send_message",
                "classification": "waterloo_student",
                "estimated_stream": "2A",
                "user_stream": "2A",
                "same_stream": True,
                "confidence": 0.95,
                "reasoning": "Profile shows 2A Computer Science at University of Waterloo"
            }
        },
        {
            "url": "https://www.linkedin.com/in/dhruv-charan-89b1b5194/",
            "name": "Dhruv Charan",
            "content": "Hi Dhruv, I'm a Peace and Conflict Studies student at the University of Waterloo and I noticed you're recruiting for software engineering roles. I'd love to connect and learn more about opportunities at your company!",
            "agent_name": "Messaging Agent",
            "agent_emoji": "💬",
            "metadata": {
                "action": "send_message",
                "classification": "recruiter",
                "confidence": 0.90,
                "reasoning": "Profile shows Talent Acquisition role with focus on software engineering"
            }
        }
    ],
    "comments": [
        {
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:7387235233458302976/?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base%3BDo0J4LpfSMa0epC3uM77JQ%3D%3D",
            "name": "GoOnHacks Post",
            "content": "This is honestly such a needed event! It reminds me of the time I GoOn'd so hard on my personal project that it basically blew my HackTheNorth submission out of the water. Apply to GoOnHacks, and maybe you'll eventually build something as innovative as I did.",
            "agent_name": "Comment Agent",
            "agent_emoji": "💬",
            "metadata": {
                "action": "send_comment",
                "classification": "relevant",
                "confidence": 0.85,
                "reasoning": "Post is about AI/tech, relevant to CS student interests"
            }
        },
        {
            "url": "https://www.linkedin.com/feed/update/urn:li:activity:7350214725693005825/",
            "name": "Career Advice Post",
            "content": "That is seriously inspiring. It reminds me of the time I pulled a 3-day all-nighter to fix an obscure memory leak in my co-op project—I totally get that feeling of earned peace, except mine was after I shipped to production. It sounds like you're just starting to catch up to the grind we master here at Waterloo.",
            "agent_name": "Comment Agent",
            "agent_emoji": "💬",
            "metadata": {
                "action": "send_comment",
                "classification": "relevant",
                "confidence": 0.90,
                "reasoning": "Post is about career advice, highly relevant to students"
            }
        }
    ]
}


def load_config(config_path: str) -> dict:
    """Load demo tasks from JSON config file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        raise


def clear_queue(redis_client: RedisClient):
    """Clear all pending tasks from the queue."""
    queue_name = "tasks:pending_approval"
    try:
        # Clear list queue
        redis_client.client.delete(queue_name)
        # Clear hash storage
        redis_client.client.delete(f"{queue_name}:tasks")
        logger.info(f"Cleared {queue_name} queue")
        feedback.agent_action("Preload Script", f"Cleared {queue_name} queue")
    except Exception as e:
        logger.error(f"Failed to clear queue: {e}")
        raise


def preload_tasks(redis_client: RedisClient, demo_tasks: dict, clear: bool = False):
    """Preload demo tasks into Redis queue.
    
    Args:
        redis_client: Redis client instance
        demo_tasks: Dictionary with 'messages' and 'comments' lists
        clear: Whether to clear queue before preloading
    """
    if clear:
        clear_queue(redis_client)
    
    task_ids = []
    
    # Preload message tasks
    feedback.agent_action("Preload Script", f"Preloading {len(demo_tasks['messages'])} message tasks...")
    for i, msg_task in enumerate(demo_tasks['messages'], 1):
        task_data = {
            "type": "message",
            "content": msg_task["content"],
            "url": msg_task["url"],
            "name": msg_task["name"],
            "agent_name": msg_task["agent_name"],
            "agent_emoji": msg_task["agent_emoji"],
            "metadata": msg_task["metadata"]
        }
        task_id = redis_client.queue_pending_task(task_data)
        task_ids.append(task_id)
        logger.info(f"Queued message task {i}: {msg_task['name']} ({msg_task['url'][:50]}...)")
        print(f"  ✅ Message {i}: {msg_task['name']} - {msg_task['agent_name']}")
    
    # Preload comment tasks
    feedback.agent_action("Preload Script", f"Preloading {len(demo_tasks['comments'])} comment tasks...")
    for i, comment_task in enumerate(demo_tasks['comments'], 1):
        task_data = {
            "type": "comment",
            "content": comment_task["content"],
            "url": comment_task["url"],
            "name": comment_task["name"],
            "agent_name": comment_task["agent_name"],
            "agent_emoji": comment_task["agent_emoji"],
            "metadata": comment_task["metadata"]
        }
        task_id = redis_client.queue_pending_task(task_data)
        task_ids.append(task_id)
        logger.info(f"Queued comment task {i}: {comment_task['name']} ({comment_task['url'][:50]}...)")
        print(f"  ✅ Comment {i}: {comment_task['name']} - {comment_task['agent_name']}")
    
    # Verify all tasks were queued
    queue_length = redis_client.client.llen("tasks:pending_approval")
    hash_length = redis_client.client.hlen("tasks:pending_approval:tasks")
    
    print(f"\n📊 Queue Status:")
    print(f"   List queue: {queue_length} tasks")
    print(f"   Hash storage: {hash_length} tasks")
    print(f"   Total queued: {len(task_ids)} tasks")
    
    if queue_length == len(task_ids) and hash_length == len(task_ids):
        feedback.agent_action("Preload Script", f"✅ Successfully preloaded {len(task_ids)} demo tasks")
        print(f"\n✅ Successfully preloaded {len(task_ids)} demo tasks!")
        print(f"   - {len(demo_tasks['messages'])} message tasks")
        print(f"   - {len(demo_tasks['comments'])} comment tasks")
        print(f"\n💡 These tasks will appear in the frontend for approval.")
    else:
        feedback.error("Preload Script", f"Queue length mismatch: expected {len(task_ids)}, got {queue_length}")
        print(f"\n⚠️  Warning: Queue length mismatch!")
        print(f"   Expected: {len(task_ids)} tasks")
        print(f"   Got: {queue_length} tasks in list, {hash_length} tasks in hash")
    
    return task_ids


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Preload demo tasks for LinkedInMaxx frontend approval",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preload with default demo data
  python3 scripts/preload_demo_tasks.py
  
  # Clear queue and preload
  python3 scripts/preload_demo_tasks.py --clear
  
  # Use custom config file
  python3 scripts/preload_demo_tasks.py --config scripts/demo_tasks_config.json
        """
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to JSON config file with demo tasks"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing tasks before preloading"
    )
    
    args = parser.parse_args()
    
    # Load demo tasks
    if args.config:
        print(f"📋 Loading demo tasks from config: {args.config}")
        demo_tasks = load_config(args.config)
    else:
        print("📋 Using default demo tasks")
        demo_tasks = DEFAULT_DEMO_TASKS
    
    # Validate demo tasks structure
    if "messages" not in demo_tasks or "comments" not in demo_tasks:
        print("❌ Error: Config must have 'messages' and 'comments' keys")
        sys.exit(1)
    
    # Connect to Redis
    print("\n🔌 Connecting to Redis...")
    try:
        redis_client = RedisClient()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("   Make sure Redis is running: redis-server")
        sys.exit(1)
    
    # Preload tasks
    print(f"\n📤 Preloading demo tasks...")
    if args.clear:
        print("   (Clearing existing tasks first)")
    
    try:
        task_ids = preload_tasks(redis_client, demo_tasks, clear=args.clear)
        print(f"\n🎉 Demo tasks preloaded successfully!")
        print(f"\n📋 Task IDs:")
        for i, task_id in enumerate(task_ids, 1):
            print(f"   {i}. {task_id}")
    except Exception as e:
        print(f"\n❌ Failed to preload tasks: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
