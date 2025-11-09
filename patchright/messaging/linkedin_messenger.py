"""
LinkedIn Messenger - Send Messages and Connection Requests

Standalone module for messaging on LinkedIn.
Includes human-like typing and stealth measures.
"""

import time
import random
import json
from pathlib import Path
from typing import Dict, Any
from patchright.sync_api import sync_playwright


class LinkedInMessenger:
    """Send messages and connection requests on LinkedIn with stealth."""
    
    def _human_type(self, selector: str, text: str):
        """
        Type text using keyboard simulation with realistic pauses.
        Copied from posting module for consistency.
        
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
        Initialize LinkedIn Messenger.
        
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
        Checks if already logged in and skips prompt if so.
        
        Args:
            manual: If True, waits for user to log in manually
        """
        print("\nNavigating to LinkedIn...")
        self.page.goto("https://www.linkedin.com", timeout=30000)
        time.sleep(2)  # Wait for page to load
        
        # Check if already logged in
        current_url = self.page.url
        is_logged_in = False
        
        # Check URL patterns that indicate login
        if "linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url:
            is_logged_in = True
            print("✓ Already logged in (detected feed or profile page)")
        else:
            # Check for login indicators on the page
            try:
                # Look for feed-specific elements or navigation that only appears when logged in
                feed_indicator = self.page.locator('nav[aria-label="Main"]').count() > 0
                if feed_indicator:
                    is_logged_in = True
                    print("✓ Already logged in (detected navigation)")
            except:
                pass
        
        if manual and not is_logged_in:
            print("\n" + "="*60)
            print("MANUAL LOGIN")
            print("="*60)
            print("Please log into LinkedIn in the browser window.")
            print("Once logged in and on the home page, come back here.")
            print("="*60)
            
            # Wait for user to log in (with error handling)
            try:
                # Give user time to see the message and log in
                print("\n⏳ Waiting for login... (you have 5 minutes)")
                print("   Tip: After logging in, navigate to https://www.linkedin.com/feed")
                print("   Then press ENTER in this terminal...")
                
                # Use a more robust input method
                import sys
                if sys.stdin.isatty():
                    # Interactive terminal - can use input()
                    input("\nPress ENTER when you're logged in and on the feed page... ")
                else:
                    # Non-interactive - wait and check periodically
                    print("   Non-interactive terminal detected. Checking login status every 10 seconds...")
                    for i in range(30):  # Check for 5 minutes (30 * 10 seconds)
                        time.sleep(10)
                        self.page.reload(wait_until="load", timeout=30000)
                        current_url = self.page.url
                        if "linkedin.com/feed" in current_url:
                            print("✓ Login detected automatically!")
                            break
                        print(f"   Still waiting... ({i+1}/30)")
                    else:
                        print("⚠️  Timeout waiting for login. Continuing anyway...")
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  Input interrupted. Checking if already logged in...")
                # Check one more time
                time.sleep(2)
                self.page.reload(wait_until="load", timeout=30000)
                current_url = self.page.url
                if "linkedin.com/feed" in current_url or "linkedin.com/in/" in current_url:
                    print("✓ Login detected! Continuing...")
                else:
                    print("⚠️  Not logged in yet. Browser will stay open.")
                    print("   You can log in manually and the orchestrator will continue.")
        
        # Navigate to feed if not already there
        if "linkedin.com/feed" not in self.page.url:
            print("\n→ Navigating to feed...")
            try:
                self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
                time.sleep(2)
                print("✓ On LinkedIn feed")
            except Exception as e:
                print(f"⚠️  Could not navigate to feed: {e}")
                print("   You may need to log in manually in the browser")
        
        print("✓ Login flow complete")
    
    def send_message(self, profile_url: str, message: str):
        """
        Send a direct message to a LinkedIn profile.
        
        Workflow:
        1. Navigate to profile
        2. Click "Message" button to open modal
        3. Type message with human-like typing
        4. Click "Send"
        5. Return to home page
        
        Args:
            profile_url: LinkedIn profile URL
            message: Message text to send
        """
        print("\n" + "="*60)
        print("SENDING LINKEDIN MESSAGE")
        print("="*60)
        
        # STEP 1: Navigate to profile
        print(f"\n→ Navigating to profile...")
        print(f"   URL: {profile_url}")
        try:
            self.page.bring_to_front()
            self.page.goto(profile_url, wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Profile loaded")
            
            # Wait for profile to fully load
            print("   Waiting for profile to load completely...")
            time.sleep(3.0)  # Wait 3 seconds for page to fully load
            
            # Scroll to top of page to ensure Message button is visible
            print("   Scrolling to top...")
            self.page.evaluate('''
                const container = document.querySelector('.scaffold-layout__main');
                if (container) container.scrollTop = 0;
                document.body.scrollTop = 0;
                document.documentElement.scrollTop = 0;
                window.scrollTo(0, 0);
            ''')
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            print(f"⚠️  Error navigating to profile: {e}")
            print("Please navigate manually if needed...")
        
        # STEP 2: Click "Message" button to open modal
        print("\n→ Opening message modal...")
        self.page.bring_to_front()
        
        try:
            # Wait for and click the Message button
            # Button has aria-label like "Message Dhruv"
            print("   Looking for Message button...")
            
            # Try the most specific selector first
            selector = 'button[aria-label^="Message "]'
            self.page.wait_for_selector(selector, timeout=5000)  # Just wait for it to exist
            
            print("   ✓ Found Message button!")
            time.sleep(random.uniform(0.5, 1.0))
            
            # Force click it (ignore visibility check)
            self.page.click(selector, force=True)
            print("✓ Message modal opened!")
            time.sleep(random.uniform(0.8, 1.2))
            
        except Exception as e:
            print(f"⚠️  Could not find/click Message button: {e}")
            print("Trying alternative method...")
            
            # Fallback: try with has-text
            try:
                self.page.click('button:has-text("Message")', force=True, timeout=5000)
                print("✓ Message modal opened (fallback method)!")
                time.sleep(random.uniform(0.8, 1.2))
            except:
                print("⚠️  Please click 'Message' button manually...")
                time.sleep(1.0)
        
        # STEP 3: Type the message
        print(f"\n→ Typing message (human-like)...")
        print(f"   Message: {message[:50]}{'...' if len(message) > 50 else ''}")
        try:
            # Find the message input field
            message_input_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div.msg-form__contenteditable',
                '[placeholder*="Write a message"]',
                'div[aria-label*="Write a message"]'
            ]
            
            typed = False
            for selector in message_input_selectors:
                try:
                    self.page.bring_to_front()
                    self.page.wait_for_selector(selector, state='visible', timeout=5000)
                    if self.page.locator(selector).is_visible():
                        print(f"  ✓ Found message input")
                        time.sleep(random.uniform(0.5, 1.0))
                        
                        # Type character by character
                        self._human_type(selector, message)
                        
                        typed = True
                        print(f"✓ Typed message")
                        break
                except:
                    continue
            
            if not typed:
                print("⚠️  Could not find message input")
                print(f"Please type this message manually: {message}")
            
        except Exception as e:
            print(f"⚠️  Error typing message: {e}")
            print(f"Please type manually: {message}")
        
        # STEP 4: Click "Send" button
        print("\n→ Sending message...")
        try:
            send_button_selectors = [
                'button:has-text("Send")',
                '[aria-label*="Send"]',
                'button.msg-form__send-button',
                'button[type="submit"]:has-text("Send")'
            ]
            
            sent = False
            for selector in send_button_selectors:
                try:
                    self.page.bring_to_front()
                    time.sleep(random.uniform(0.5, 1.0))
                    self.page.wait_for_selector(selector, timeout=5000)
                    
                    print(f"  ✓ Found 'Send' button")
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Force click to bypass visibility checks
                    self.page.click(selector, force=True)
                    sent = True
                    print("✓ Message sent!")
                    break
                except Exception as e:
                    print(f"  ✗ Selector failed: {str(e)[:30]}")
                    continue
            
            if not sent:
                print("⚠️  Could not find 'Send' button")
                raise Exception("Failed to send message")
            
            time.sleep(random.uniform(2.0, 3.0))
            
        except Exception as e:
            print(f"⚠️  Error sending message: {e}")
            raise
        
        # STEP 5: Return to home page (keep browser open)
        print("\n→ Returning to home page...")
        try:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Back on home page")
        except Exception as e:
            print(f"⚠️  Error returning to home: {e}")
        
        print("\n✅ Message flow complete!")
        print("="*60)
        print("→ Browser staying open for next task...")
    
    def send_connection_request(self, profile_url: str, note: str = None):
        """
        Send a connection request to a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL  
            note: Optional connection note
        """
        print("\n" + "="*60)
        print("SENDING CONNECTION REQUEST")
        print("="*60)
        
        # Navigate to profile
        print(f"\n→ Navigating to profile...")
        print(f"   URL: {profile_url}")
        try:
            self.page.bring_to_front()
            self.page.goto(profile_url, wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Profile loaded")
        except Exception as e:
            print(f"⚠️  Error navigating: {e}")
        
        time.sleep(random.uniform(2.0, 3.0))
        
        # Click "Connect" button
        print("\n→ Looking for 'Connect' button...")
        try:
            connect_button_selectors = [
                'button:has-text("Connect")',
                '[aria-label*="Connect"]',
                'button.artdeco-button:has-text("Connect")'
            ]
            
            clicked = False
            for selector in connect_button_selectors:
                try:
                    self.page.bring_to_front()
                    time.sleep(random.uniform(0.5, 1.0))
                    self.page.wait_for_selector(selector, state='visible', timeout=5000)
                    if self.page.locator(selector).is_visible():
                        print(f"  ✓ Found 'Connect' button")
                        time.sleep(random.uniform(0.5, 1.5))
                        self.page.click(selector)
                        clicked = True
                        print("✓ Clicked 'Connect' button")
                        break
                except:
                    continue
            
            if not clicked:
                print("⚠️  Could not find 'Connect' button")
                raise Exception("Failed to click Connect button")
            
            time.sleep(random.uniform(2.0, 3.0))
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
            raise
        
        # If note provided, add it
        if note:
            print("\n→ Adding connection note...")
            # Try to find and fill note field
            try:
                note_selectors = [
                    'textarea[name="message"]',
                    'textarea[placeholder*="Add a note"]',
                    'div[contenteditable="true"][role="textbox"]'
                ]
                for selector in note_selectors:
                    try:
                        self.page.wait_for_selector(selector, timeout=3000)
                        self.page.fill(selector, note)
                        print(f"✓ Added note: {note[:50]}...")
                        time.sleep(random.uniform(1.0, 2.0))
                        break
                    except:
                        continue
            except:
                print(f"⚠️  Could not add note automatically: {note}")
        
        # Click Send
        print("\n→ Sending connection request...")
        try:
            send_selectors = [
                'button:has-text("Send")',
                '[aria-label*="Send"]',
                'button.artdeco-button--primary:has-text("Send")'
            ]
            
            sent = False
            for selector in send_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.page.click(selector)
                    sent = True
                    print("✓ Connection request sent!")
                    break
                except:
                    continue
            
            if not sent:
                raise Exception("Failed to send connection request")
                
            time.sleep(random.uniform(2.0, 3.0))
        except Exception as e:
            print(f"⚠️  Error sending connection request: {e}")
            raise
        
        print("\n✅ Connection request complete!")
        print("="*60)
    
    def execute_message_task(self, instruction: Dict[str, Any]):
        """
        Execute a message task from Redis queue.
        
        Args:
            instruction: {
                "profile_url": "...",
                "name": "...",
                "message": "...",
                "action": "send_message" | "connect_only"
            }
        """
        profile_url = instruction["profile_url"]
        action = instruction.get("action", "send_message")
        
        if action == "send_message":
            message = instruction.get("message", "")
            if not message:
                print("⚠️  No message provided, sending connection request instead")
                self.send_connection_request(profile_url)
            else:
                self.send_message(profile_url, message)
        elif action == "connect_only":
            self.send_connection_request(profile_url)
        else:
            raise ValueError(f"Unknown action: {action}")
    
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
