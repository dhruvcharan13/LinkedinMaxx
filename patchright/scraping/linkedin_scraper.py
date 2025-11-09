"""
LinkedIn Scraper using Patchright
Scrapes LinkedIn profiles and feed with stealth capabilities.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
import pandas as pd
import random

from patchright.sync_api import sync_playwright
from stealth_utils import (
    human_delay,
    random_mouse_movement,
    scroll_to_load_feed,
    simulate_profile_visit,
    human_like_scroll,
    random_break
)

# Try to import Redis client (optional, for publishing scraped data)
try:
    import sys
    from pathlib import Path
    # Add parent directory to path to import redis_client
    parent_dir = Path(__file__).parent.parent.absolute()
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    from redis_client import PlaywrightRedisClient
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis client not available. Scraped profiles will only be saved to files.")


class LinkedInScraper:
    """LinkedIn scraper with stealth capabilities."""
    
    def __init__(self, user_data_dir: str = "./browser_data", headless: bool = False, debug: bool = False):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            user_data_dir: Directory to store browser session (for persistent login)
            headless: Run browser in headless mode (False recommended for LinkedIn)
            debug: Enable debug mode with verbose logging
        """
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Create data directory
        self.data_dir = Path("./scraped_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize Redis client if available
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = PlaywrightRedisClient()
            except Exception as e:
                print(f"⚠️  Could not initialize Redis client: {e}")
                self.redis_client = None
    
    def _debug_print(self, message: str):
        """Print debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")
    
    def save_page_html(self, filename: str = "page_debug.html"):
        """Save current page HTML for debugging."""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.page.content())
        print(f"[DEBUG] Page HTML saved to: {filepath}")
        return filepath
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start the browser with persistent context."""
        print("🚀 Starting Patchright browser...")
        self.playwright = sync_playwright().start()
        
        # Use persistent context to maintain login session
        # This allows you to log in manually once and reuse the session
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            channel="chrome",  # Use Chrome instead of Chromium for better stealth
            headless=self.headless,
            no_viewport=True,  # Important for stealth
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        # Get the first page (or create one if none exists)
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        print("✅ Browser started successfully!")
    
    def close(self):
        """Close the browser."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        print("👋 Browser closed.")
    
    def login(self, email: Optional[str] = None, password: Optional[str] = None, manual: bool = True):
        """
        Login to LinkedIn.
        
        Args:
            email: LinkedIn email (optional if manual=True)
            password: LinkedIn password (optional if manual=True)
            manual: If True, wait for manual login. If False, attempt automated login.
        """
        print("🔐 Logging in to LinkedIn...")
        print("   Navigating to login page...")
        
        try:
            self.page.goto("https://www.linkedin.com/login", wait_until="load", timeout=30000)
            self._debug_print(f"Current URL: {self.page.url}")
            human_delay(2, 4)
        except Exception as e:
            print(f"⚠️  Error navigating to login page: {e}")
            print("   Continuing anyway...")
        
        if manual:
            print("\n" + "="*60)
            print("⚠️  MANUAL LOGIN REQUIRED")
            print("="*60)
            print("Please log in to LinkedIn in the browser window.")
            print("The scraper will wait until you're logged in.")
            print("Press Enter here once you've logged in...")
            print("="*60 + "\n")
            
            # Wait for user to press Enter
            input()
            
            print("   Verifying login...")
            # Verify login by checking if we're on LinkedIn feed or profile
            try:
                self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
                self._debug_print(f"Current URL after login: {self.page.url}")
                human_delay(2, 3)
                
                if "feed" in self.page.url or "linkedin.com/in/" in self.page.url:
                    print("✅ Login successful!")
                else:
                    print(f"⚠️  Warning: Unexpected URL: {self.page.url}")
                    print("   Continuing anyway...")
            except Exception as e:
                print(f"⚠️  Error verifying login: {e}")
                print("   Continuing anyway...")
        else:
            # Automated login (less recommended, more likely to be detected)
            print("   Attempting automated login...")
            if not email or not password:
                raise ValueError("Email and password required for automated login")
            
            try:
                email_input = self.page.locator('input[name="session_key"]')
                password_input = self.page.locator('input[name="session_password"]')
                submit_button = self.page.locator('button[type="submit"]')
                
                email_input.fill(email)
                human_delay(1, 2)
                password_input.fill(password)
                human_delay(1, 2)
                submit_button.click()
                
                human_delay(5, 8)
                
                if "feed" in self.page.url:
                    print("✅ Login successful!")
                else:
                    print(f"⚠️  Login may have failed. Current URL: {self.page.url}")
            except Exception as e:
                print(f"⚠️  Automated login error: {e}")
                print("   Please log in manually in the browser.")
        
        print("   Adding human-like behavior...")
        random_mouse_movement(self.page)
        human_delay(2, 4)
        print("✅ Login process complete!")
    
    def scrape_profile(self, profile_url: str) -> Dict:
        """
        Scrape a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Dictionary with profile data
        """
        print(f"📄 Scraping profile: {profile_url}")
        print("   Navigating to profile...")
        
        try:
            self.page.goto(profile_url, wait_until="load", timeout=30000)
            self._debug_print(f"Current URL: {self.page.url}")
            human_delay(3, 5)
        except Exception as e:
            print(f"⚠️  Error navigating to profile: {e}")
            return {"url": profile_url, "error": str(e), "scraped_at": datetime.now().isoformat()}
        
        print("   Simulating human reading behavior...")
        # Simulate reading the profile
        simulate_profile_visit(self.page, min_time=15.0, max_time=30.0)
        
        profile_data = {
            "url": profile_url,
            "scraped_at": datetime.now().isoformat(),
        }
        
        print("   Extracting profile data...")
        try:
            # Extract name - try multiple selectors
            name_selectors = [
                'h1',  # H1 tags usually have the name
                'h1[class*="text-heading"]',
                '.text-heading-xlarge'
            ]
            for selector in name_selectors:
                try:
                    name_element = self.page.locator(selector).first
                    if name_element.is_visible(timeout=3000):
                        name_text = name_element.inner_text().strip()
                        if name_text and len(name_text) > 2:
                            profile_data["name"] = name_text
                            self._debug_print(f"Found name: {name_text}")
                            break
                except:
                    continue
            
            # Extract headline/title
            headline_selectors = [
                'div[class*="text-body-medium"]',
                '[class*="headline"]',
                '.pv-text-details__left-panel div:nth-child(2)'
            ]
            for selector in headline_selectors:
                try:
                    headline_element = self.page.locator(selector).first
                    if headline_element.is_visible(timeout=3000):
                        headline_text = headline_element.inner_text().strip()
                        if headline_text and len(headline_text) > 5:
                            profile_data["headline"] = headline_text
                            self._debug_print(f"Found headline: {headline_text[:50]}")
                            break
                except:
                    continue
            
            # Extract location
            location_selectors = [
                'span[class*="text-body-small"]',
                '.pv-text-details__left-panel span:has-text("·")',
            ]
            for selector in location_selectors:
                try:
                    location_element = self.page.locator(selector).first
                    if location_element.is_visible(timeout=3000):
                        location_text = location_element.inner_text().strip()
                        if location_text and '·' not in location_text:  # Filter out follower counts
                            profile_data["location"] = location_text
                            self._debug_print(f"Found location: {location_text}")
                            break
                except:
                    continue
            
            # Scroll to load all sections
            print("   Scrolling to load all sections...")
            for _ in range(3):
                human_like_scroll(self.page, scroll_amount=random.randint(400, 800))
                human_delay(1, 2)
            
            # Extract About/Bio section
            print("   Extracting bio...")
            about_selectors = [
                'section:has(#about) + div',  # Section after About header
                'div[id*="about"] ~ div',
                'section[data-section="summary"]',
                '[aria-labelledby*="about"]',
            ]
            for selector in about_selectors:
                try:
                    about_elements = self.page.locator(selector).all()
                    for about_elem in about_elements:
                        if about_elem.is_visible(timeout=2000):
                            about_text = about_elem.inner_text().strip()
                            if about_text and len(about_text) > 20 and "About" not in about_text[:20]:
                                profile_data["bio"] = about_text
                                self._debug_print(f"Found bio: {about_text[:100]}")
                                break
                    if profile_data.get("bio"):
                        break
                except:
                    continue
            
            # Extract Experience section
            print("   Extracting experience...")
            experience_selectors = [
                'section:has(#experience) + div li',
                'div[id*="experience"] ~ div li',
                'section[data-section="experience"] li',
            ]
            profile_data["experience"] = []
            for selector in experience_selectors:
                try:
                    exp_items = self.page.locator(selector).all()[:10]  # Get up to 10 experiences
                    for exp in exp_items:
                        try:
                            exp_text = exp.inner_text().strip()
                            # Filter out noise and get substantial sections
                            if exp_text and len(exp_text) > 30:
                                lines = [l.strip() for l in exp_text.split('\n') if l.strip()]
                                
                                # Parse experience into structured format
                                exp_entry = {}
                                
                                # Line 0: Usually job title
                                if len(lines) > 0:
                                    exp_entry['title'] = lines[0]
                                
                                # Line 1: Usually company (may have · Employment Type)
                                if len(lines) > 1:
                                    company_line = lines[1]
                                    # Remove employment type if present
                                    if '·' in company_line:
                                        exp_entry['company'] = company_line.split('·')[0].strip()
                                    else:
                                        exp_entry['company'] = company_line
                                
                                # Line 2: Usually dates (e.g., "Jan 2020 - Present · 5 yrs")
                                if len(lines) > 2:
                                    date_line = lines[2]
                                    # Check if this line contains date patterns
                                    if any(month in date_line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                                             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']) or \
                                       'Present' in date_line or 'yrs' in date_line or 'mos' in date_line:
                                        # Split by · to separate dates from duration
                                        if '·' in date_line:
                                            parts = date_line.split('·')
                                            exp_entry['dates'] = parts[0].strip()
                                            if len(parts) > 1:
                                                exp_entry['duration'] = parts[1].strip()
                                        else:
                                            exp_entry['dates'] = date_line.strip()
                                
                                # Line 3+: Could be location or description
                                if len(lines) > 3:
                                    # Check if line 3 is a location (usually short)
                                    if len(lines[3]) < 100:
                                        exp_entry['location'] = lines[3]
                                
                                # Only add if we have at least title and company
                                if exp_entry.get('title') and exp_entry.get('company'):
                                    profile_data["experience"].append(exp_entry)
                        except Exception as e:
                            self._debug_print(f"Error parsing experience: {e}")
                            pass
                    if profile_data["experience"]:
                        self._debug_print(f"Found {len(profile_data['experience'])} experiences")
                        break
                except:
                    continue
            
            # Extract Education section
            print("   Extracting education...")
            education_selectors = [
                'section:has(#education) + div li',
                'div[id*="education"] ~ div li',
                'section[data-section="education"] li',
            ]
            profile_data["education"] = []
            for selector in education_selectors:
                try:
                    edu_items = self.page.locator(selector).all()[:5]  # Get up to 5 education entries
                    for edu in edu_items:
                        try:
                            edu_text = edu.inner_text().strip()
                            # Get school name, degree, and dates
                            if edu_text and len(edu_text) > 10:
                                lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
                                
                                # Parse education into structured format
                                edu_entry = {}
                                
                                # Line 0: Usually school name
                                if len(lines) > 0:
                                    edu_entry['school'] = lines[0]
                                
                                # Line 1: Usually degree
                                if len(lines) > 1:
                                    edu_entry['degree'] = lines[1]
                                
                                # Line 2: Usually dates (e.g., "2018 - 2022")
                                if len(lines) > 2:
                                    date_line = lines[2]
                                    # Check if this line contains year patterns (4 digits)
                                    if any(char.isdigit() for char in date_line) and len(date_line) < 50:
                                        edu_entry['dates'] = date_line
                                    # Could also be activities/societies
                                    elif 'Activities' in date_line or 'societies' in date_line:
                                        edu_entry['activities'] = date_line
                                
                                # Line 3: Could be grade or activities
                                if len(lines) > 3 and len(lines[3]) < 100:
                                    if 'Grade' in lines[3] or 'GPA' in lines[3]:
                                        edu_entry['grade'] = lines[3]
                                
                                # Only add if we have at least school name
                                if edu_entry.get('school'):
                                    profile_data["education"].append(edu_entry)
                        except Exception as e:
                            self._debug_print(f"Error parsing education: {e}")
                            pass
                    if profile_data["education"]:
                        self._debug_print(f"Found {len(profile_data['education'])} education entries")
                        break
                except:
                    continue
            
        except Exception as e:
            print(f"⚠️  Error extracting profile data: {e}")
            profile_data["error"] = str(e)
        
        # Classify profile and add type field
        try:
            # Import from same directory (scraping module)
            from profile_classifier import ProfileClassifier
            profile_data = ProfileClassifier.add_type_to_profile(profile_data)
            # Also add 'type' field (lowercase) for consistency with backend
            if 'Type' in profile_data:
                profile_data['type'] = profile_data['Type'].lower()
            else:
                profile_data['type'] = 'other'
        except Exception as e:
            print(f"⚠️  Error classifying profile: {e}")
            profile_data["type"] = "other"
            profile_data["Type"] = "other"
        
        # Publish to Redis if available
        if self.redis_client and "error" not in profile_data:
            try:
                self.redis_client.publish_scraped_profile(profile_url, profile_data)
            except Exception as e:
                print(f"⚠️  Error publishing to Redis: {e}")
        
        return profile_data
    
    def scrape_profiles_from_feed(self, max_profiles: int = 10, stealth_mode: bool = True) -> List[Dict]:
        """
        Scrape profiles of people who post in the LinkedIn feed.
        Includes enhanced stealth measures to avoid detection.
        
        Args:
            max_profiles: Maximum number of profiles to scrape (recommended: 5-15)
            stealth_mode: Enable aggressive stealth measures (highly recommended)
            
        Returns:
            List of profile data dictionaries
        """
        # Rate limiting check
        if max_profiles > 15:
            print(f"⚠️  WARNING: Scraping {max_profiles} profiles may trigger detection!")
            print("   Recommended: 5-15 profiles per session with breaks between sessions.")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                print("   Aborting. Consider running multiple sessions with fewer profiles.")
                return []
        
        print(f"\n{'='*60}")
        print(f"PROFILE SCRAPING SESSION")
        print(f"{'='*60}")
        print(f"Target: {max_profiles} profiles")
        print(f"Stealth mode: {'ENABLED ✅' if stealth_mode else 'DISABLED ⚠️'}")
        print(f"{'='*60}\n")
        
        # Step 1: Collect profile URLs from feed
        print("STEP 1: Collecting profile URLs from feed...")
        profile_urls = self.get_profile_urls_from_feed(max_profiles=max_profiles)
        
        if not profile_urls:
            print("\n❌ No profile URLs found. Aborting.")
            return []
        
        print(f"\n✅ Found {len(profile_urls)} profiles to scrape\n")
        
        # Step 2: Scrape each profile with stealth
        print(f"STEP 2: Scraping {len(profile_urls)} profiles...")
        print("This will take some time due to stealth measures...\n")
        
        all_profiles = []
        session_start = time.time()
        
        for idx, profile_url in enumerate(profile_urls, 1):
            print(f"\n{'='*60}")
            print(f"Profile {idx}/{len(profile_urls)}")
            print(f"{'='*60}")
            
            # Scrape the profile
            profile_data = self.scrape_profile(profile_url)
            
            if profile_data and "error" not in profile_data:
                all_profiles.append(profile_data)
                print(f"✅ Successfully scraped: {profile_data.get('name', 'Unknown')}")
            else:
                print(f"⚠️  Failed to scrape profile")
            
            # STEALTH MEASURES
            if stealth_mode and idx < len(profile_urls):  # Don't delay after last profile
                # Calculate delay based on position in sequence
                if idx % 10 == 0:
                    # Long break every 10 profiles
                    delay = random.uniform(120, 300)  # 2-5 minutes
                    print(f"\n🛌 COOLING OFF PERIOD ({idx} profiles scraped)")
                    print(f"   Taking a {delay/60:.1f} minute break...")
                    print(f"   This helps avoid detection patterns.")
                    time.sleep(delay)
                elif idx % 5 == 0:
                    # Medium break every 5 profiles
                    delay = random.uniform(60, 120)  # 1-2 minutes
                    print(f"\n⏸️  Taking a {delay:.0f} second break...")
                    time.sleep(delay)
                else:
                    # Regular delay between profiles
                    delay = random.uniform(30, 90)  # 30-90 seconds
                    print(f"\n⏳ Waiting {delay:.0f} seconds before next profile...")
                    time.sleep(delay)
                
                # Random mouse movement between profiles
                try:
                    random_mouse_movement(self.page, min_moves=2, max_moves=5)
                except:
                    pass
        
        # Session summary
        session_duration = time.time() - session_start
        print(f"\n{'='*60}")
        print(f"SESSION COMPLETE")
        print(f"{'='*60}")
        print(f"✅ Successfully scraped: {len(all_profiles)}/{len(profile_urls)} profiles")
        print(f"⏱️  Total time: {session_duration/60:.1f} minutes")
        print(f"📊 Average time per profile: {session_duration/len(all_profiles) if all_profiles else 0:.0f} seconds")
        print(f"{'='*60}\n")
        
        if stealth_mode:
            print("💡 STEALTH TIP: Wait 30-60 minutes before starting another session.")
        
        return all_profiles
    
    def get_profile_urls_from_feed(self, max_profiles: int = 10) -> List[str]:
        """
        Get profile URLs from LinkedIn feed posts.
        
        Args:
            max_profiles: Maximum number of profile URLs to collect
            
        Returns:
            List of unique profile URLs
        """
        print(f"📰 Collecting profile URLs from LinkedIn feed (max {max_profiles} profiles)...")
        print("   Navigating to feed...")
        
        try:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            self._debug_print(f"Current URL: {self.page.url}")
            print("   Waiting for feed to load...")
            time.sleep(2)  # Quick wait for feed to load
        except Exception as e:
            print(f"⚠️  Error navigating to feed: {e}")
            return []
        
        profile_urls = []
        scroll_count = 0
        max_scrolls = max_profiles * 3  # Scroll more to find profiles
        seen_urls = set()  # Track unique profile URLs
        
        print(f"   Starting to collect profile URLs (will scroll up to {max_scrolls} times)...")
        
        # Debug: Save page HTML on first attempt
        if self.debug:
            self.save_page_html("linkedin_feed_debug.html")
            
            # Try to find ANY div elements
            all_divs = self.page.locator('div').all()
            print(f"[DEBUG] Total <div> elements on page: {len(all_divs)}")
            
            # Try to find elements with common LinkedIn classes
            test_selectors = [
                '[data-view-name="feed-full-update"]',  # NEW: The actual post selector!
                '[componentkey*="urn:li:activity"]',
                'div[data-view-name*="feed"]',
                'div[class*="feed"]',
                'div[class*="update"]',
                'article',
                'main',
                '[role="main"]',
            ]
            
            for selector in test_selectors:
                try:
                    elements = self.page.locator(selector).all()
                    if elements:
                        print(f"[DEBUG] Found {len(elements)} elements with: {selector}")
                        if len(elements) > 0 and len(elements) < 50:
                            # Print first element's classes
                            try:
                                first_elem = elements[0]
                                classes = first_elem.get_attribute('class')
                                print(f"[DEBUG]   First element classes: {classes}")
                            except:
                                pass
                except:
                    pass
        
        # Scroll and collect profile URLs
        while len(profile_urls) < max_profiles and scroll_count < max_scrolls:
            self._debug_print(f"Scroll {scroll_count + 1}/{max_scrolls}")
            
            # Find post elements - try multiple selectors
            try:
                # LinkedIn uses data attributes (more stable than obfuscated class names)
                post_selectors = [
                    '[data-view-name="feed-full-update"]',  # New LinkedIn layout
                    '[componentkey*="urn:li:activity"]',     # Activity posts
                    'div[data-view-name*="feed"]',           # Any feed view
                    '.feed-shared-update-v2',                # Old layout (fallback)
                    '[data-urn*="urn:li:activity"]',         # Old data-urn attribute
                ]
                
                post_elements = []
                for selector in post_selectors:
                    try:
                        elements = self.page.locator(selector).all()
                        if elements and len(elements) > 0:
                            post_elements = elements
                            self._debug_print(f"Found {len(elements)} elements with selector: {selector}")
                            break
                    except:
                        continue
                
                if not post_elements:
                    print(f"   ⚠️  No posts found on scroll {scroll_count + 1}, scrolling more...")
                else:
                    print(f"   Found {len(post_elements)} potential post elements...")
                
                # Process each post to extract profile URLs
                profiles_found_this_round = 0
                for i, post_elem in enumerate(post_elements):
                    if len(profile_urls) >= max_profiles:
                        break
                    
                    try:
                        # Extract profile URL from post author
                        profile_url = None
                        
                        # Try to find profile link
                        profile_link_selectors = [
                            'a[href*="/in/"][data-view-name*="actor"]',  # Actor link
                            'a[href*="/in/"]',  # Any profile link
                        ]
                        
                        for selector in profile_link_selectors:
                            try:
                                links = post_elem.locator(selector).all()
                                for link in links:
                                    href = link.get_attribute('href')
                                    if href and '/in/' in href:
                                        # Clean URL (remove query params)
                                        profile_url = href.split('?')[0]
                                        # Make sure it's a full URL
                                        if not profile_url.startswith('http'):
                                            profile_url = f"https://www.linkedin.com{profile_url}"
                                        break
                                if profile_url:
                                    break
                            except:
                                continue
                        
                        # Add unique profile URL
                        if profile_url and profile_url not in seen_urls:
                            seen_urls.add(profile_url)
                            profile_urls.append(profile_url)
                            profiles_found_this_round += 1
                            print(f"  ✓ Found profile {len(profile_urls)}/{max_profiles}: {profile_url}")
                            self._debug_print(f"Profile URL: {profile_url}")
                    
                    except Exception as e:
                        self._debug_print(f"Error extracting profile URL {i}: {e}")
                        continue
                
                if profiles_found_this_round == 0:
                    print(f"   No new profiles found in this scroll, continuing...")
            
            except Exception as e:
                print(f"   ⚠️  Error finding posts: {e}")
                self._debug_print(f"Full error: {e}")
            
            # Scroll to load more posts - FAST AND VISIBLE
            print(f"   Scrolling... ({scroll_count + 1}/{max_scrolls})")
            try:
                # Big visible scroll
                self.page.mouse.wheel(0, 800)
                time.sleep(0.3)
            except Exception as e:
                self._debug_print(f"Scroll error: {e}")
            
            scroll_count += 1
            
            # Short delay - just enough to load content
            time.sleep(0.5)
        
        print(f"✅ Collection complete! Found {len(profile_urls)} unique profile URLs")
        
        if len(profile_urls) == 0:
            print("\n⚠️  WARNING: No profile URLs were found!")
            print("   This could mean:")
            print("   1. LinkedIn's HTML structure has changed (selectors need updating)")
            print("   2. The feed didn't load properly")
            print("   3. You're not logged in correctly")
            print(f"   Current URL: {self.page.url}")
            print("\n   Try running with debug=True for more details:")
            print("   scraper = LinkedInScraper(debug=True)")
        
        return profile_urls
    
    def save_data(self, data: Union[List[Dict], Dict], filename: str, format: str = "json"):
        """
        Save scraped data to file.
        
        Args:
            data: Data to save (list of dicts or single dict)
            filename: Output filename (without extension)
            format: Output format ("json", "csv", "excel")
        """
        filepath = self.data_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "json":
            filepath = filepath.with_suffix(".json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            filepath = filepath.with_suffix(".csv")
            if isinstance(data, dict):
                data = [data]
            
            if data:
                df = pd.DataFrame(data)
                # Flatten nested lists/dicts
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
                df.to_csv(filepath, index=False, encoding="utf-8")
        
        elif format == "excel":
            filepath = filepath.with_suffix(".xlsx")
            if isinstance(data, dict):
                data = [data]
            
            if data:
                df = pd.DataFrame(data)
                # Flatten nested lists/dicts
                for col in df.columns:
                    if df[col].dtype == object:
                        df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
                df.to_excel(filepath, index=False, engine="openpyxl")
        
        print(f"💾 Data saved to: {filepath}")
        return filepath


def main():
    """Main function to run the scraper."""
    print("="*60)
    print("LinkedIn Profile Scraper with Patchright")
    print("="*60)
    print("This scraper collects profiles from people who post in your feed")
    print("and extracts: Bio, Experience, Education")
    print("="*60 + "\n")
    
    # Initialize scraper with debug mode (set debug=True for more detailed output)
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login (manual recommended)
        scraper.login(manual=True)
        
        # Scrape profiles from feed with stealth mode
        print("\n" + "="*60)
        print("Profile Scraping from Feed")
        print("="*60)
        
        # Scrape 5 profiles (recommended for first run)
        # Change max_profiles to scrape more (max 10-15 recommended per session)
        profiles = scraper.scrape_profiles_from_feed(
            max_profiles=5,
            stealth_mode=True  # HIGHLY RECOMMENDED - keeps you undetected
        )
        
        # Save in multiple formats
        if profiles:
            scraper.save_data(profiles, "linkedin_profiles", format="json")
            scraper.save_data(profiles, "linkedin_profiles", format="csv")
            scraper.save_data(profiles, "linkedin_profiles", format="excel")
            print(f"\n✅ Successfully saved {len(profiles)} profiles!")
            print(f"📁 Data saved in: ./scraped_data/")
            
            # Show sample of what was scraped
            print("\n" + "="*60)
            print("SAMPLE DATA (First Profile)")
            print("="*60)
            if profiles:
                sample = profiles[0]
                print(f"Name: {sample.get('name', 'N/A')}")
                print(f"Headline: {sample.get('headline', 'N/A')[:80]}...")
                print(f"Location: {sample.get('location', 'N/A')}")
                print(f"Bio: {sample.get('bio', 'N/A')[:100]}...")
                print(f"Experience entries: {len(sample.get('experience', []))}")
                print(f"Education entries: {len(sample.get('education', []))}")
                print(f"Profile URL: {sample.get('url', 'N/A')}")
        else:
            print("\n⚠️  No profiles scraped. Try running with debug=True to diagnose.")
            print("   To enable debug: edit main() and set debug=True")
    
    print("\n✅ Session complete!")
    print("\n" + "="*60)
    print("IMPORTANT TIPS")
    print("="*60)
    print("• Wait 30-60 minutes before running another session")
    print("• Keep sessions to 5-15 profiles maximum")
    print("• Use stealth_mode=True (already enabled)")
    print("• The slower the scraping, the safer from detection")
    print("="*60)


if __name__ == "__main__":
    main()

