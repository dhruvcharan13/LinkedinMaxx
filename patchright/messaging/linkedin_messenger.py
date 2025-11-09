"""
LinkedIn Messenger - Send Messages and Connection Requests

Standalone module for messaging on LinkedIn.
Includes human-like typing and stealth measures.
"""

import time
import random
import json
from pathlib import Path
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
        
        input("\nPress ENTER to send the message... ")
        
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
                print("Please click 'Send' manually...")
                input("Press ENTER once sent... ")
            
            time.sleep(random.uniform(2.0, 3.0))
            
        except Exception as e:
            print(f"⚠️  Error sending message: {e}")
            print("Please click 'Send' manually...")
            input("Press ENTER once sent... ")
        
        # STEP 5: Return to home page
        print("\n→ Returning to home page...")
        try:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            print("✓ Back on home page")
        except Exception as e:
            print(f"⚠️  Error returning to home: {e}")
        
        print("\n✅ Message flow complete!")
        print("="*60)
        
        # Ask if user wants to keep browser open
        print("\n📌 Browser is still open for you to review.")
        print("You can check the message, respond, or browse LinkedIn.")
        close_browser = input("\nType 'close' to close the browser (or press ENTER to keep it open): ").strip().lower()
        
        if close_browser == 'close':
            print("✓ Will close browser...")
        else:
            print("\n✓ Keeping browser open.")
            print("When you're ready to close, come back here and press ENTER...")
            input()
            print("✓ Closing browser now...")
    
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
        
        input("\nPress ENTER once profile loads... ")
        
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
                print("Please click 'Connect' manually...")
            
            time.sleep(random.uniform(2.0, 3.0))
            
        except Exception as e:
            print(f"⚠️  Error: {e}")
        
        # If note provided, add it
        if note:
            print("\n→ Adding connection note...")
            print("Please add the note manually if needed:")
            print(f"   Note: {note}")
        
        input("\nPress ENTER to send connection request... ")
        
        # Click Send
        print("\n→ Sending connection request...")
        try:
            send_selectors = [
                'button:has-text("Send")',
                '[aria-label*="Send"]'
            ]
            
            for selector in send_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    print("✓ Connection request sent!")
                    break
                except:
                    continue
        except:
            print("Please click 'Send' manually...")
            input("Press ENTER once sent... ")
        
        print("\n✅ Connection request complete!")
        print("="*60)
    
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


def main():
    """Example usage of LinkedIn Messenger."""
    print("="*60)
    print("LINKEDIN MESSENGER")
    print("="*60)
    print("Send direct messages to LinkedIn profiles")
    print("="*60 + "\n")
    
    # Load test profile
    script_dir = Path(__file__).parent.absolute()
    test_file = script_dir / "test_profile.json"
    
    if test_file.exists():
        with open(test_file, 'r') as f:
            test_data = json.load(f)
        
        print(f"📋 Loaded test profile:")
        print(f"   Name: {test_data.get('name', 'Unknown')}")
        print(f"   URL: {test_data.get('profile_url', 'Unknown')}")
        print(f"   Message: {test_data.get('message', 'No message')[:60]}...")
        print()
        
        use_test = input("Use test profile? (y/n): ").strip().lower()
        if use_test == 'y':
            profile_url = test_data['profile_url']
            message = test_data['message']
        else:
            profile_url = input("\nEnter profile URL: ").strip()
            message = input("Enter message: ").strip()
    else:
        print("No test profile found. Enter profile details:")
        profile_url = input("\nProfile URL: ").strip()
        message = input("Message: ").strip()
    
    # Send message
    with LinkedInMessenger(headless=False) as messenger:
        messenger.login(manual=True)
        messenger.send_message(profile_url, message)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
