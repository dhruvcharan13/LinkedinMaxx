"""
LinkedIn Poster - Create Posts with Text + Photo

Completely standalone module for posting to LinkedIn.
No dependency on scraping functionality.
"""

import time
import random
from pathlib import Path
from typing import Dict, Any
from patchright.sync_api import sync_playwright


class LinkedInPoster:
    """Posts text and images to LinkedIn."""
    
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
        
        # Fast typing for demo (reduced delays)
        words = text.split(' ')
        
        for i, word in enumerate(words):
            # Type each character in the word
            for char in word:
                self.page.keyboard.type(char)
                # Very fast typing within a word (reduced from 0.05-0.15 to 0.01-0.03)
                time.sleep(random.uniform(0.01, 0.03))
            
            # Add space after word (except last word)
            if i < len(words) - 1:
                self.page.keyboard.type(' ')
                # Shorter pause between words (reduced from 0.2-0.5 to 0.05-0.1)
                time.sleep(random.uniform(0.05, 0.1))
            
            # Occasional longer pause (reduced frequency and duration)
            if random.random() < 0.05:  # Reduced from 15% to 5% chance
                time.sleep(random.uniform(0.2, 0.4))  # Reduced from 0.5-1.2 to 0.2-0.4
        
        # Final pause after finishing typing (reduced from 1.0-2.0 to 0.3-0.5)
        time.sleep(random.uniform(0.3, 0.5))
    
    def __init__(self, headless: bool = False, user_data_dir: str = "../browser_data"):
        """
        Initialize LinkedIn Poster.
        
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
    
    def create_post(self, text: str, image_path: str = None):
        """
        Create a LinkedIn post with text and optional image.
        
        Args:
            text: Text content for the post
            image_path: Optional path to image file to attach
        """
        print("\n" + "="*60)
        print("CREATING LINKEDIN POST")
        print("="*60)
        
        # Navigate to feed if not already there (but keep same tab)
        if "linkedin.com/feed" not in self.page.url:
            print("→ Navigating to LinkedIn feed...")
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(2)
        else:
            # Already on feed, just refresh to ensure we're ready
            print("→ Already on feed, ensuring page is ready...")
            self.page.bring_to_front()
            time.sleep(1)
        
        # Click "Start a post" button
        print("→ Clicking 'Start a post' button...")
        try:
            # Try multiple selectors for the post button
            post_button_selectors = [
                'button:has-text("Start a post")',
                '[aria-label="Start a post"]',
                '.share-box-feed-entry__trigger',
                'button.share-box-feed-entry__trigger'
            ]
            
            clicked = False
            for selector in post_button_selectors:
                try:
                    self.page.click(selector, timeout=5000)
                    clicked = True
                    print("✓ Clicked post button")
                    break
                except:
                    continue
            
            if not clicked:
                print("❌ Could not find 'Start a post' button")
                print("Please click it manually, then press ENTER...")
                input()
            
            time.sleep(2)
        except Exception as e:
            print(f"⚠️  Error clicking post button: {e}")
            print("Please click 'Start a post' manually, then press ENTER...")
            input()
        
        # Validate text content before typing
        if not text or not text.strip():
            raise ValueError(f"Cannot create post with empty content. Content length: {len(text) if text else 0}")
        
        # Type the text content (human-like, character by character)
        print("→ Typing post text (human-like)...")
        print(f"  Content length: {len(text)} characters")
        try:
            # Find the text editor
            editor_selectors = [
                '[data-placeholder="What do you want to talk about?"]',
                '.ql-editor',
                '[contenteditable="true"]',
                'div[role="textbox"]'
            ]
            
            typed = False
            for selector in editor_selectors:
                try:
                    # Click to focus first
                    self.page.click(selector, timeout=5000)
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Type character by character
                    print(f"  Typing: {text[:50]}{'...' if len(text) > 50 else ''}")
                    self._human_type(selector, text)
                    
                    typed = True
                    print(f"✓ Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
                    break
                except Exception as e:
                    continue
            
            if not typed:
                print("❌ Could not find text editor")
                raise Exception("Failed to find text editor")
            
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            print(f"⚠️  Error typing text: {e}")
            raise
        
        # Upload image if provided
        if image_path:
            print(f"→ Uploading image: {image_path}...")
            try:
                # Click the media/image button
                media_button_selectors = [
                    '[aria-label="Add a photo"]',
                    '[aria-label="Add media"]',
                    'button:has-text("Add a photo")',
                    'button:has-text("Media")'
                ]
                
                clicked_media = False
                for selector in media_button_selectors:
                    try:
                        self.page.click(selector, timeout=5000)
                        clicked_media = True
                        print("✓ Clicked media button")
                        break
                    except:
                        continue
                
                if not clicked_media:
                    print("❌ Could not find media button")
                    if image_path:
                        print(f"⚠️  Skipping image upload: {image_path}")
                else:
                    time.sleep(random.uniform(0.5, 1.0))
                    
                    # Upload the file
                    file_path = Path(image_path).absolute()
                    if file_path.exists():
                        # Find file input and upload
                        try:
                            file_input = self.page.locator('input[type="file"]')
                            file_input.set_input_files(str(file_path))
                            print(f"✓ Uploaded: {file_path.name}")
                            time.sleep(random.uniform(2.0, 3.0))  # Wait for upload and editor to load
                            
                            # Click "Next" button in the image editor modal
                            print("→ Looking for 'Next' button in image editor...")
                            next_clicked = False
                            next_button_selectors = [
                                'button:has-text("Next")',
                                '[aria-label="Next"]',
                                'button.artdeco-button--primary:has-text("Next")'
                            ]
                            
                            for selector in next_button_selectors:
                                try:
                                    self.page.wait_for_selector(selector, state='visible', timeout=5000)
                                    if self.page.locator(selector).is_visible():
                                        print("  ✓ Found 'Next' button")
                                        time.sleep(random.uniform(0.5, 1.0))
                                        self.page.click(selector)
                                        next_clicked = True
                                        print("✓ Clicked 'Next' button")
                                        break
                                except:
                                    continue
                            
                            if not next_clicked:
                                print("⚠️  Could not find 'Next' button, continuing...")
                            
                            time.sleep(random.uniform(1.0, 2.0))  # Wait for editor to close
                            
                        except Exception as e:
                            print(f"❌ Could not upload file: {e}")
                            print(f"⚠️  Continuing without image...")
                    else:
                        print(f"❌ File not found: {file_path}")
                
            except Exception as e:
                print(f"⚠️  Error uploading image: {e}")
                print(f"⚠️  Continuing without image...")
        
        # Click the bottom "Post" button to publish directly
        print("→ Clicking bottom 'Post' button to publish...")
        try:
            # Target the bottom/primary Post button specifically
            post_button_selectors = [
                'button.share-actions__primary-action:has-text("Post")',
                'div.share-actions button[type="submit"]:has-text("Post")',
                'button.artdeco-button--primary:has-text("Post")',
                '[aria-label="Post"]',
                'button:has-text("Post")'
            ]
            
            posted = False
            for selector in post_button_selectors:
                try:
                    # Wait for button to be visible
                    self.page.wait_for_selector(selector, state='visible', timeout=5000)
                    
                    # Verify it's visible and clickable
                    if self.page.locator(selector).is_visible():
                        print(f"  ✓ Found 'Post' button")
                        time.sleep(random.uniform(0.5, 1.5))  # Human pause before clicking
                        self.page.click(selector)
                        posted = True
                        print("✓ Post published!")
                        break
                except:
                    continue
            
            # Manual fallback if automatic fails
            if not posted:
                raise Exception("Failed to find Post button")
            
            time.sleep(random.uniform(3.0, 5.0))  # Wait for post to publish
            
        except Exception as e:
            print(f"⚠️  Error publishing post: {e}")
            raise
        
        print("\n✅ Post submitted!")
        print("="*60)
        print("\n⏳ Waiting for LinkedIn to publish your post...")
        time.sleep(random.uniform(2.0, 4.0))  # Wait for post to appear
        print("✓ Post published!")
        print("="*60)
        
        # Stay on feed (don't navigate away) - browser stays open
        print("\n→ Staying on feed for next task...")
        time.sleep(1)
    
    def execute_post_task(self, instruction: Dict[str, Any]):
        """
        Execute a post task from Redis queue.
        
        Args:
            instruction: {
                "content": "...",
                "metadata": {...}
            }
        """
        content = instruction.get("content", "")
        metadata = instruction.get("metadata", {})
        image_path = metadata.get("image_path")
        
        # Validate content
        if not content or not content.strip():
            print("⚠️  ERROR: Post content is empty!")
            print(f"   Instruction keys: {list(instruction.keys())}")
            print(f"   Instruction: {instruction}")
            raise ValueError("Cannot post empty content. Post generation may have failed.")
        
        self.create_post(text=content, image_path=image_path)
    
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

