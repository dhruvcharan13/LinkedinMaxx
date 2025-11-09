"""
Main orchestrator for Playwright automation.
Consumes tasks from Redis queues and executes them.
"""

import time
import signal
import sys
import requests
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.absolute()
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from redis_client import PlaywrightRedisClient
from messaging.linkedin_messenger import LinkedInMessenger
from posting.linkedin_poster import LinkedInPoster
from commenting.linkedin_commenter import LinkedInCommenter
from scraping.feed_scraper import FeedScraper


class PlaywrightOrchestrator:
    """Orchestrates all Playwright tasks."""
    
    def __init__(self, headless: bool = False, user_data_dir: str = "./browser_data", backend_url: str = "http://localhost:8000"):
        """
        Initialize orchestrator.
        
        Args:
            headless: Run browser in headless mode
            user_data_dir: Directory to store browser data (for persistent login)
            backend_url: URL of the FastAPI backend
        """
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.backend_url = backend_url
        self.redis_client = None
        self.messenger = None
        self.poster = None
        self.commenter = None
        self.scraper = None
        self.running = False
    
    def start(self):
        """Start browser and initialize modules."""
        print("🚀 Starting Playwright Orchestrator...")
        
        # Initialize Redis client
        try:
            self.redis_client = PlaywrightRedisClient()
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("   Make sure Redis is running: docker run -d -p 6379:6379 redis:alpine")
            raise
        
        # Initialize messenger (will handle browser login)
        print("📱 Initializing LinkedIn Messenger...")
        try:
            self.messenger = LinkedInMessenger(headless=self.headless, user_data_dir=self.user_data_dir)
            self.messenger.start()
            print("✓ Browser started successfully")
            
            # Login (with error handling - browser stays open even if login fails)
            try:
                self.messenger.login(manual=True)  # Login once
            except Exception as e:
                print(f"⚠️  Login flow encountered an issue: {e}")
                print("   Browser will stay open - you can log in manually if needed")
                print("   Orchestrator will continue and check for tasks")
                # Continue anyway - browser is open, user can log in manually
        except Exception as e:
            print(f"❌ Error initializing browser: {e}")
            print("   Make sure you have Chrome/Chromium installed")
            raise
        
        # Initialize other modules (reuse browser context and playwright instance)
        print("📝 Initializing LinkedIn Poster...")
        self.poster = LinkedInPoster(headless=self.headless, user_data_dir=self.user_data_dir)
        self.poster.playwright = self.messenger.playwright
        self.poster.context = self.messenger.context
        self.poster.page = self.messenger.page
        
        print("💬 Initializing LinkedIn Commenter...")
        self.commenter = LinkedInCommenter(headless=self.headless, user_data_dir=self.user_data_dir)
        self.commenter.playwright = self.messenger.playwright
        self.commenter.context = self.messenger.context
        self.commenter.page = self.messenger.page
        
        print("🔍 Initializing Feed Scraper...")
        self.scraper = FeedScraper(page=self.messenger.page, redis_client=self.redis_client)
        
        self.running = True
        print("✅ Orchestrator started and ready to process tasks!")
        print("="*60)
        
        # Start backend workflow and trigger post generation
        print("\n📝 Starting backend workflow and triggering initial post generation...")
        try:
            # First, start the workflow if not already running
            workflow_response = requests.post(
                f"{self.backend_url}/api/start-scrolling",
                json={"generate_daily_post": False},  # We'll trigger post generation separately
                timeout=30
            )
            if workflow_response.status_code == 200:
                print("✅ Backend workflow started!")
            elif workflow_response.status_code == 400:
                # Workflow might already be running, that's okay
                print("ℹ️  Backend workflow already running")
            else:
                print(f"⚠️  Workflow start returned status {workflow_response.status_code}")
            
            # Now trigger post generation
            response = requests.post(
                f"{self.backend_url}/api/generate-daily-post",
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                print("✅ Post generation triggered!")
                print(f"   Task ID: {result.get('task_id', 'N/A')}")
                print("   → Post is queued for frontend approval")
                print("   → Once approved, it will appear in playwright:post queue")
                print("   → After posting, scraper will run automatically")
                print("   → Scraped profiles/posts will create messaging/commenting tasks")
            else:
                print(f"⚠️  Post generation request returned status {response.status_code}")
                try:
                    error_detail = response.json().get('detail', response.text[:200])
                    print(f"   Response: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Could not connect to backend at {self.backend_url}")
            print("   Make sure backend is running: cd backend && python3 main.py")
            print("   Workflow will start when backend is available")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not start workflow or trigger post generation: {e}")
            print("   Make sure backend is running: cd backend && python3 main.py")
    
    def run(self):
        """Main loop: consume tasks from Redis and execute."""
        print("🔄 Starting main loop...")
        print("   Waiting for tasks from Redis queues...")
        print("   Queues: playwright:post, playwright:message, playwright:comment")
        print("="*60 + "\n")
        
        task_count = 0
        loop_count = 0
        last_status_time = time.time()
        status_interval = 10  # Print status every 10 seconds
        
        while self.running:
            try:
                # Check for post tasks (non-blocking)
                post_task = self.redis_client.get_post_instruction(timeout=0)
                if post_task:
                    task_count += 1
                    print(f"\n📝 [{task_count}] Executing post task...")
                    try:
                        self.poster.execute_post_task(post_task)
                        print(f"✅ Post task completed!")
                        
                        # After post is completed, start scraping
                        print(f"\n🔍 Starting feed scraping after post...")
                        try:
                            scraped_profiles = self.scraper.scrape_feed_profiles(max_profiles=3, max_scrolls=10)
                            print(f"✅ Scraped {len(scraped_profiles)} profiles from feed")
                            print(f"   → Profiles published to Redis for agent processing")
                        except Exception as e:
                            print(f"⚠️  Error during feed scraping: {e}")
                            import traceback
                            traceback.print_exc()
                    except Exception as e:
                        print(f"❌ Error executing post task: {e}")
                        import traceback
                        traceback.print_exc()
                    continue  # Process one task at a time
                
                # Check for message tasks (non-blocking)
                message_task = self.redis_client.get_message_instruction(timeout=0)
                if message_task:
                    task_count += 1
                    print(f"\n💬 [{task_count}] Executing message task...")
                    print(f"   Profile: {message_task.get('name', 'Unknown')}")
                    print(f"   Action: {message_task.get('action', 'send_message')}")
                    try:
                        self.messenger.execute_message_task(message_task)
                        print(f"✅ Message task completed!")
                    except Exception as e:
                        print(f"❌ Error executing message task: {e}")
                        import traceback
                        traceback.print_exc()
                    continue  # Process one task at a time
                
                # Check for comment tasks (non-blocking)
                comment_task = self.redis_client.get_comment_instruction(timeout=0)
                if comment_task:
                    task_count += 1
                    print(f"\n💭 [{task_count}] Executing comment task...")
                    print(f"   Post: {comment_task.get('post_url', 'Unknown')[:60]}...")
                    try:
                        self.commenter.execute_comment_task(comment_task)
                        print(f"✅ Comment task completed!")
                    except Exception as e:
                        print(f"❌ Error executing comment task: {e}")
                        import traceback
                        traceback.print_exc()
                    continue  # Process one task at a time
                
                # No tasks found - show periodic status and wait
                loop_count += 1
                current_time = time.time()
                
                # Print status every N seconds
                if current_time - last_status_time >= status_interval:
                    # Get queue lengths for status
                    try:
                        post_q = self.redis_client.client.llen("playwright:post")
                        msg_q = self.redis_client.client.llen("playwright:message")
                        comment_q = self.redis_client.client.llen("playwright:comment")
                        pending_q = self.redis_client.client.llen("tasks:pending_approval")
                        
                        print(f"⏳ [{loop_count}] Still waiting for tasks... (Queue status: post={post_q}, message={msg_q}, comment={comment_q}, pending={pending_q})")
                        last_status_time = current_time
                    except Exception as e:
                        print(f"⏳ [{loop_count}] Still waiting for tasks... (Status check error: {e})")
                        last_status_time = current_time
                
                # Small sleep to prevent CPU spinning
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                self.stop()
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(1)
    
    def stop(self):
        """Stop orchestrator (but keep browser open for user to review)."""
        print("\n🛑 Stopping orchestrator...")
        self.running = False
        # Don't close browser - let user review and close manually
        # The browser context will stay open until user closes it
        print("👋 Orchestrator stopped")
        print("📌 Browser is still open - you can review tasks or close it manually")
        # Explicitly keep browser context alive
        if self.messenger and self.messenger.context:
            print("   Browser context will remain open until you close it manually")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Playwright Orchestrator for LinkedIn Automation")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--user-data-dir", default="./browser_data", help="Browser data directory")
    args = parser.parse_args()
    
    orchestrator = PlaywrightOrchestrator(
        headless=args.headless,
        user_data_dir=args.user_data_dir
    )
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\n⚠️  Received signal, stopping...")
        orchestrator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        orchestrator.start()
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        orchestrator.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  Error occurred, but keeping browser open for debugging...")
        orchestrator.stop()
        # Don't exit immediately - give user time to see the error
        print("\n📌 Browser is still open. Check the error above.")
        print("   You can close the browser manually when done.")


if __name__ == "__main__":
    main()

