#!/usr/bin/env python3
"""
Task Approval Script - Manually approve tasks and send them to Playwright queues.
Use this when the frontend is not ready or for testing.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add backend to path to import RedisClient
backend_dir = Path(__file__).parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from utils.redis_client import RedisClient


def print_task(task: Dict[str, Any], index: int = None):
    """Print a task in a readable format."""
    task_id = task.get("task_id", "Unknown")
    task_type = task.get("type", "unknown")
    content = task.get("content", "")
    url = task.get("url", "")
    name = task.get("name", "Unknown")
    agent = task.get("agent_name", "Unknown Agent")
    emoji = task.get("agent_emoji", "🤖")
    
    prefix = f"[{index}] " if index is not None else ""
    print(f"\n{prefix}{'='*60}")
    print(f"{prefix}Task ID: {task_id}")
    print(f"{prefix}Type: {task_type.upper()}")
    print(f"{prefix}Agent: {emoji} {agent}")
    print(f"{prefix}Name: {name}")
    if url:
        print(f"{prefix}URL: {url}")
    print(f"{prefix}Content:")
    print(f"{prefix}  {content[:200]}{'...' if len(content) > 200 else ''}")
    print(f"{prefix}{'='*60}")


def approve_task_interactive(redis_client: RedisClient, task: Dict[str, Any]) -> bool:
    """Interactively approve a task."""
    task_id = task.get("task_id")
    task_type = task.get("type", "unknown")
    content = task.get("content", "")
    
    print_task(task)
    
    print("\nOptions:")
    print("  [a] Approve as-is")
    print("  [e] Edit then approve")
    print("  [r] Reject")
    print("  [s] Skip (approve later)")
    print("  [q] Quit")
    
    choice = input("\nYour choice: ").strip().lower()
    
    if choice == "a":
        # Approve as-is
        success = redis_client.approve_task(task_id)
        if success:
            print(f"✅ Approved task: {task_id}")
            return True
        else:
            print(f"❌ Failed to approve task: {task_id}")
            return False
    
    elif choice == "e":
        # Edit then approve
        print(f"\nCurrent content:\n{content}")
        print("\nEnter new content (or press ENTER to keep current):")
        new_content = input("> ").strip()
        if not new_content:
            new_content = content
        
        success = redis_client.approve_task(task_id, new_content)
        if success:
            print(f"✅ Approved task with edited content: {task_id}")
            return True
        else:
            print(f"❌ Failed to approve task: {task_id}")
            return False
    
    elif choice == "r":
        # Reject
        success = redis_client.reject_task(task_id)
        if success:
            print(f"❌ Rejected task: {task_id}")
            return True
        else:
            print(f"⚠️  Failed to reject task: {task_id}")
            return False
    
    elif choice == "s":
        # Skip
        print(f"⏭️  Skipped task: {task_id}")
        return False
    
    elif choice == "q":
        # Quit
        print("👋 Exiting...")
        return None
    
    else:
        print("⚠️  Invalid choice. Skipping...")
        return False


def approve_all_tasks(redis_client: RedisClient, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Auto-approve all tasks."""
    stats = {"approved": 0, "rejected": 0, "failed": 0}
    
    for task in tasks:
        task_id = task.get("task_id")
        print(f"\n✅ Auto-approving task: {task_id}")
        print_task(task)
        
        success = redis_client.approve_task(task_id)
        if success:
            stats["approved"] += 1
            print(f"✅ Approved!")
        else:
            stats["failed"] += 1
            print(f"❌ Failed to approve")
    
    return stats


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Approve pending tasks and send to Playwright")
    parser.add_argument("--auto", action="store_true", help="Auto-approve all tasks")
    parser.add_argument("--watch", action="store_true", help="Watch for new tasks continuously")
    parser.add_argument("--interval", type=int, default=5, help="Watch interval in seconds (default: 5)")
    args = parser.parse_args()
    
    print("🔍 Connecting to Redis...")
    redis_client = RedisClient()
    
    if not redis_client.is_connected():
        print("❌ Failed to connect to Redis")
        print("   Make sure Redis is running: redis-cli ping")
        sys.exit(1)
    
    print("✅ Connected to Redis\n")
    
    if args.watch:
        # Watch mode - continuously check for new tasks
        print(f"👀 Watching for new tasks (checking every {args.interval} seconds)...")
        print("   Press Ctrl+C to stop\n")
        
        import time
        seen_task_ids = set()
        
        try:
            while True:
                tasks = redis_client.get_pending_tasks()
                new_tasks = [t for t in tasks if t.get("task_id") not in seen_task_ids]
                
                if new_tasks:
                    print(f"\n📬 Found {len(new_tasks)} new task(s)!")
                    for task in new_tasks:
                        task_id = task.get("task_id")
                        seen_task_ids.add(task_id)
                        
                        if args.auto:
                            redis_client.approve_task(task_id)
                            print(f"✅ Auto-approved: {task_id}")
                        else:
                            result = approve_task_interactive(redis_client, task)
                            if result is None:  # Quit
                                break
                else:
                    print(f"⏳ No new tasks... (checked {len(tasks)} pending)")
                
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n👋 Stopped watching")
    else:
        # One-time check
        tasks = redis_client.get_pending_tasks()
        
        if not tasks:
            print("✅ No pending tasks!")
            return
        
        print(f"📋 Found {len(tasks)} pending task(s):\n")
        
        if args.auto:
            # Auto-approve all
            print("🚀 Auto-approving all tasks...\n")
            stats = approve_all_tasks(redis_client, tasks)
            print(f"\n📊 Summary:")
            print(f"   Approved: {stats['approved']}")
            print(f"   Failed: {stats['failed']}")
        else:
            # Interactive approval
            print("💡 Tip: Use --auto to auto-approve all tasks")
            print("💡 Tip: Use --watch to continuously watch for new tasks\n")
            
            for i, task in enumerate(tasks, 1):
                result = approve_task_interactive(redis_client, task)
                if result is None:  # Quit
                    break
                print()


if __name__ == "__main__":
    main()

