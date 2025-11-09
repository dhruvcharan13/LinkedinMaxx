"""
LinkedIn Poster - Create Posts with Text + Photo

Completely standalone module for posting to LinkedIn.
No dependency on scraping functionality.
"""

import time
import random
from pathlib import Path
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
        
        # Navigate to feed if not already there
        if "linkedin.com/feed" not in self.page.url:
            print("→ Navigating to LinkedIn feed...")
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(2)
        
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
        
        # Type the text content (human-like, character by character)
        print("→ Typing post text (human-like)...")
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
                print(f"Please type this manually: {text}")
                input("Press ENTER when done...")
            
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"⚠️  Error typing text: {e}")
            print(f"Please type this manually: {text}")
            input("Press ENTER when done...")
        
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
                    print("Please click 'Add a photo' manually and upload the image")
                    print(f"Image path: {image_path}")
                    input("Press ENTER when done...")
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
                                print("⚠️  Could not find 'Next' button")
                                print("Please click 'Next' in the image editor manually...")
                                input("Press ENTER when done...")
                            
                            time.sleep(random.uniform(1.0, 2.0))  # Wait for editor to close
                            
                        except Exception as e:
                            print(f"❌ Could not upload file: {e}")
                            print(f"Please upload manually: {file_path}")
                            input("Press ENTER when done...")
                    else:
                        print(f"❌ File not found: {file_path}")
                
            except Exception as e:
                print(f"⚠️  Error uploading image: {e}")
                print(f"Please upload image manually: {image_path}")
                input("Press ENTER when done...")
        
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
                print("\n" + "="*60)
                print("⚠️  MANUAL INTERVENTION NEEDED")
                print("="*60)
                print("Could not find the 'Post' button at the bottom.")
                print("Please look at the browser window:")
                print("  1. Find the 'Post' button at the BOTTOM of the modal")
                print("  2. Click it to publish your post")
                print("  3. Come back here and press ENTER")
                input("\nPress ENTER after clicking 'Post'... ")
                print("✓ Manual Post confirmation received")
            
            time.sleep(random.uniform(3.0, 5.0))  # Wait for post to publish
            
        except Exception as e:
            print(f"⚠️  Error publishing post: {e}")
            print("Please click the bottom 'Post' button manually...")
            input("Press ENTER when done...")
        
        print("\n✅ Post submitted!")
        print("="*60)
        print("\n⏳ Waiting for LinkedIn to publish your post...")
        print("Please check your feed to confirm the post appears.")
        print("(This may take a few seconds)")
        input("\n✓ Press ENTER once you've confirmed your post is visible... ")
        print("✓ Post confirmed!")
        print("="*60)
        
        # Ask user if they want to keep browser open
        print("\n📌 Browser is still open for you to review.")
        print("You can check your post, edit it, or browse LinkedIn.")
        close_browser = input("\nType 'close' to close the browser (or press ENTER to keep it open): ").strip().lower()
        
        if close_browser == 'close':
            print("✓ Will close browser...")
        else:
            print("\n✓ Keeping browser open.")
            print("When you're ready to close, come back here and press ENTER...")
            input()
            print("✓ Closing browser now...")
    
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
    """Example usage of LinkedIn Poster."""
    print("="*60)
    print("LINKEDIN POSTER")
    print("="*60)
    print("Post text and images to LinkedIn")
    print("="*60 + "\n")
    
    # Get post content
    text = input("Enter your post text: ").strip()
    if not text:
        text = "Test post from automation script!"
    
    # Get the directory where THIS script is located
    script_dir = Path(__file__).parent.absolute()
    print(f"\n📁 Script directory: {script_dir}")
    print("   (Images will be looked up relative to this directory)")
    
    image_path = input("\nEnter image path (or press ENTER to skip): ").strip()
    if image_path:
        # Try to resolve the path
        image_path_obj = Path(image_path)
        
        # If it's not absolute, look relative to the script directory
        if not image_path_obj.is_absolute():
            full_path = (script_dir / image_path).absolute()
        else:
            full_path = image_path_obj.absolute()
        
        if not full_path.exists():
            print(f"\n❌ Image not found!")
            print(f"   Looking for: {full_path}")
            print(f"\n💡 Tips:")
            print(f"   - Put image in script directory: {script_dir}")
            print(f"   - Or use full path: /Users/username/Desktop/image.png")
            print(f"   - Or drag & drop the file into this terminal")
            image_path = None
        else:
            print(f"✓ Found image: {full_path.name}")
            image_path = str(full_path)
    
    # Create post
    with LinkedInPoster(headless=False) as poster:
        poster.login(manual=True)
        poster.create_post(text=text, image_path=image_path if image_path else None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

