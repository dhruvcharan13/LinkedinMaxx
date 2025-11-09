"""
LinkedIn Commenter - Post Comments on LinkedIn Posts

Standalone module for commenting on LinkedIn posts with stealth measures.
Includes human-like typing, reading simulation, and comprehensive edge case handling.
"""

import time
import random
import json
from pathlib import Path
from typing import Dict, Any
from patchright.sync_api import sync_playwright


class LinkedInCommenter:
    """Comment on LinkedIn posts with human-like behavior and stealth."""
    
    def _human_type(self, selector: str, text: str):
        """
        Type text using keyboard simulation with realistic pauses.
        
        Args:
            selector: CSS selector for the input element
            text: Text to type
        """
        # Click element to focus
        self.page.click(selector)
        time.sleep(random.uniform(0.5, 1.0))
        
        # Split into words for more realistic pausing
        words = text.split(' ')
        
        for i, word in enumerate(words):
            # Type each character in the word
            for char in word:
                self.page.keyboard.type(char)
                # Fast typing within a word
                time.sleep(random.uniform(0.05, 0.15))
            
            # Add space after word (except last word)
            if i < len(words) - 1:
                self.page.keyboard.type(' ')
                # Longer pause between words (thinking/reading)
                time.sleep(random.uniform(0.2, 0.5))
            
            # Occasional longer pause (simulating thinking)
            if random.random() < 0.15:  # 15% chance
                time.sleep(random.uniform(0.5, 1.2))
        
        # Final pause after finishing typing
        time.sleep(random.uniform(1.0, 2.0))
    
    def __init__(self, headless: bool = False, user_data_dir: str = "../browser_data"):
        """
        Initialize LinkedIn Commenter.
        
        Args:
            headless: Run browser in headless mode
            user_data_dir: Directory to store browser data (for persistent login)
        """
        self.headless = headless
        self.user_data_dir = Path(user_data_dir).absolute()
        self.browser = None
        self.context = None
        self.page = None
    
    def start(self):
        """Start the browser."""
        print("Starting browser...")
        
        self.playwright = sync_playwright().start()
        
        # Launch with persistent context (keeps login)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            channel="chrome",
            no_viewport=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        # Get or create page
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        print("✓ Browser started")
    
    def login(self, manual: bool = True):
        """
        Login to LinkedIn (manual by default).
        
        Args:
            manual: If True, waits for user to log in manually
        """
        print("\nNavigating to LinkedIn...")
        self.page.goto("https://www.linkedin.com", timeout=30000)
        
        if manual:
            print("\n" + "="*60)
            print("MANUAL LOGIN")
            print("="*60)
            print("Please log into LinkedIn in the browser window.")
            print("Once logged in and on the home page, come back here.")
            input("\nPress ENTER when you're logged in... ")
            print("✓ Login confirmed")
    
    def post_comment(self, post_url: str, comment: str):
        """
        Post a comment on a LinkedIn post.
        
        Workflow:
        1. Navigate to post URL
        2. Simulate reading (scroll down, pause, scroll up)
        3. Click "Comment" button
        4. Type comment with human-like behavior
        5. Click "Post" button
        6. Return to home page
        
        Args:
            post_url: LinkedIn post URL
            comment: Comment text to post
        """
        print("\n" + "="*60)
        print("POSTING LINKEDIN COMMENT")
        print("="*60)
        
        # STEP 1: Navigate to post
        print(f"\n→ Navigating to post...")
        print(f"   URL: {post_url[:80]}...")
        try:
            self.page.bring_to_front()
            self.page.goto(post_url, wait_until="load", timeout=30000)
            print("✓ Post loaded")
            
            # Wait for full page load
            print("   Waiting for post content to load...")
            time.sleep(3.0)
            
        except Exception as e:
            print(f"⚠️  Error navigating to post: {e}")
            print("Please navigate manually if needed...")
        
        # STEP 2: Simulate reading the post
        print("\n→ Simulating reading post...")
        try:
            self.page.bring_to_front()
            
            # Scroll down to "read" the post
            scroll_amount = random.randint(200, 400)
            print(f"   Scrolling down {scroll_amount}px...")
            self.page.evaluate(f'''
                window.scrollBy({{top: {scroll_amount}, behavior: "smooth"}});
            ''')
            
            # Pause to "read"
            read_time = random.uniform(1.5, 2.5)
            print(f"   Reading for {read_time:.1f}s...")
            time.sleep(read_time)
            
            # Scroll back to top for Comment button
            print("   Scrolling back to top...")
            self.page.evaluate('''
                window.scrollTo({top: 0, behavior: "smooth"});
            ''')
            time.sleep(1.0)
            
        except Exception as e:
            print(f"⚠️  Error simulating reading: {e}")
        
        # STEP 3: Click "Comment" button
        print("\n→ Opening comment box...")
        self.page.bring_to_front()
        
        try:
            # Wait before clicking (human-like)
            time.sleep(random.uniform(0.5, 1.0))
            
            comment_button_selectors = [
                'button[aria-label*="Comment"]',
                'button:has-text("Comment")',
                '.comment-button',
                '[data-control-name="comment"]'
            ]
            
            clicked = False
            for selector in comment_button_selectors:
                try:
                    # Wait for button to exist
                    self.page.wait_for_selector(selector, timeout=5000)
                    print(f"  ✓ Found Comment button")
                    
                    time.sleep(random.uniform(0.3, 0.7))
                    
                    # Force click to bypass visibility checks
                    self.page.click(selector, force=True)
                    clicked = True
                    print("✓ Comment box opened!")
                    break
                except Exception as e:
                    continue
            
            if not clicked:
                print("⚠️  Could not find Comment button")
                print("Please click 'Comment' manually...")
            
            # Wait for comment box to appear
            time.sleep(random.uniform(1.0, 2.0))
            
        except Exception as e:
            print(f"⚠️  Error opening comment box: {e}")
            print("Continuing to typing step...")
            time.sleep(1.0)
        
        # STEP 4: Type the comment
        print(f"\n→ Typing comment (human-like)...")
        print(f"   Comment: {comment[:60]}{'...' if len(comment) > 60 else ''}")
        
        try:
            # Find the comment input field
            comment_input_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[contenteditable="true"]',
                '.ql-editor',
                '[data-placeholder*="comment"]',
                'div[aria-label*="comment" i]'
            ]
            
            typed = False
            for selector in comment_input_selectors:
                try:
                    self.page.bring_to_front()
                    self.page.wait_for_selector(selector, timeout=5000)
                    
                    print(f"  ✓ Found comment input")
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Type character by character
                    self._human_type(selector, comment)
                    
                    typed = True
                    print(f"✓ Typed comment")
                    break
                except Exception as e:
                    continue
            
            if not typed:
                print("⚠️  Could not find comment input")
                raise Exception("Failed to find comment input")
            
        except Exception as e:
            print(f"⚠️  Error typing comment: {e}")
            raise
        
        # STEP 5: Click "Post" button
        print("\n→ Posting comment...")
        self.page.bring_to_front()
        
        try:
            # Wait before clicking
            time.sleep(random.uniform(0.8, 1.5))
            
            # Use specific selector to avoid clicking "repost" button
            comment_submit_selectors = [
                'button.comments-comment-box__submit-button--cr',
                'button.comments-comment-box__submit-button',
                'button[type="submit"].artdeco-button--primary:has-text("Comment")'
            ]
            
            posted = False
            for selector in comment_submit_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    print(f"  ✓ Found Comment submit button")
                    
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Force click
                    self.page.click(selector, force=True)
                    posted = True
                    print("✓ Clicked Comment button!")
                    break
                except Exception as e:
                    continue
            
            if not posted:
                raise Exception("Failed to find Comment submit button")
            
            # Wait for comment to post
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Comment posted!")
            
        except Exception as e:
            print(f"⚠️  Error posting comment: {e}")
            raise
        
        # STEP 6: Return to home page (keep browser open)
        print("\n→ Returning to home page...")
        try:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Back on home page")
        except Exception as e:
            print(f"⚠️  Error returning to home: {e}")
        
        print("\n✅ Comment flow complete!")
        print("="*60)
        print("→ Browser staying open for next task...")
    
    def execute_comment_task(self, instruction: Dict[str, Any]):
        """
        Execute a comment task from Redis queue.
        
        Args:
            instruction: {
                "post_url": "...",
                "comment": "..."
            }
        """
        post_url = instruction["post_url"]
        comment = instruction["comment"]
        self.post_comment(post_url, comment)
    
    def close(self):
        """Close the browser."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("✓ Browser closed")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

