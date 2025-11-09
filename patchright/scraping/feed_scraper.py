"""
Feed Scraper - Scrapes profiles and posts from LinkedIn feed.
Designed to work with the orchestrator's existing browser/page.
"""

import time
import random
import json
from typing import List, Dict, Set, Optional
from datetime import datetime
from pathlib import Path

# Profile classifier will be imported when needed


class FeedScraper:
    """Scraper that uses an existing Playwright page to scrape profiles from feed."""
    
    def __init__(self, page, redis_client=None):
        """
        Initialize feed scraper.
        
        Args:
            page: Playwright page object (from orchestrator)
            redis_client: Optional Redis client for publishing scraped data
        """
        self.page = page
        self.redis_client = redis_client
        self.scraped_profiles: List[Dict] = []
        self.scraped_posts: List[Dict] = []
        self.seen_urls: Set[str] = set()
    
    def scrape_profile_from_url(self, profile_url: str) -> Optional[Dict]:
        """
        Scrape a single profile from its URL.
        Reuses the orchestrator's page.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Profile data dictionary or None if failed
        """
        try:
            print(f"   📄 Scraping profile: {profile_url}")
            self.page.goto(profile_url, wait_until="load", timeout=30000)
            time.sleep(random.uniform(2.0, 3.0))
            
            # Extract basic profile data
            profile_data = {
                "url": profile_url,
                "scraped_at": datetime.now().isoformat(),
            }
            
            # Extract name
            try:
                name_selectors = ['h1', 'h1[class*="text-heading"]', '.text-heading-xlarge']
                for selector in name_selectors:
                    try:
                        name_elem = self.page.locator(selector).first
                        if name_elem.is_visible(timeout=3000):
                            name_text = name_elem.inner_text().strip()
                            if name_text and len(name_text) > 2:
                                profile_data["name"] = name_text
                                break
                    except:
                        continue
            except:
                pass
            
            # Extract headline
            try:
                headline_selectors = ['div[class*="text-body-medium"]', '[class*="headline"]']
                for selector in headline_selectors:
                    try:
                        headline_elem = self.page.locator(selector).first
                        if headline_elem.is_visible(timeout=3000):
                            headline_text = headline_elem.inner_text().strip()
                            if headline_text and len(headline_text) > 5:
                                profile_data["headline"] = headline_text
                                break
                    except:
                        continue
            except:
                pass
            
            # Scroll to load all sections
            try:
                for _ in range(3):
                    self.page.evaluate('window.scrollBy(0, 500)')
                    time.sleep(random.uniform(0.5, 1.0))
            except:
                pass
            
            # Extract bio/about
            try:
                about_selectors = [
                    'section[data-section="summary"]',
                    'div[data-view-name="profile-component-about"]',
                    'div[id*="about"]',
                ]
                for selector in about_selectors:
                    try:
                        about_elem = self.page.locator(selector).first
                        if about_elem.is_visible(timeout=3000):
                            about_text = about_elem.inner_text().strip()
                            # Filter out "About" header and get actual content
                            if about_text and len(about_text) > 20:
                                # Remove "About" if it's at the start
                                if about_text.startswith("About"):
                                    about_text = about_text[5:].strip()
                                if about_text:
                                    profile_data["bio"] = about_text[:1000]  # Limit length
                                    break
                    except:
                        continue
            except:
                pass
            
            # Extract experience (simplified - just first few)
            try:
                experience_items = []
                exp_selectors = [
                    'section[data-section="experience"] li',
                    'div[id*="experience"] li',
                ]
                for selector in exp_selectors:
                    try:
                        exp_elems = self.page.locator(selector).all()[:5]  # Get first 5
                        for exp_elem in exp_elems:
                            try:
                                exp_text = exp_elem.inner_text().strip()
                                if exp_text and len(exp_text) > 30:
                                    experience_items.append(exp_text)
                            except:
                                pass
                        if experience_items:
                            profile_data["experience"] = experience_items
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract education (simplified)
            try:
                education_items = []
                edu_selectors = [
                    'section[data-section="education"] li',
                    'div[id*="education"] li',
                ]
                for selector in edu_selectors:
                    try:
                        edu_elems = self.page.locator(selector).all()[:3]  # Get first 3
                        for edu_elem in edu_elems:
                            try:
                                edu_text = edu_elem.inner_text().strip()
                                if edu_text and len(edu_text) > 10:
                                    education_items.append(edu_text)
                            except:
                                pass
                        if education_items:
                            profile_data["education"] = education_items
                            break
                    except:
                        continue
            except:
                pass
            
            # Classify profile and add type
            try:
                # Import profile classifier (try multiple import paths)
                try:
                    from scraping.profile_classifier import ProfileClassifier
                except ImportError:
                    try:
                        from profile_classifier import ProfileClassifier
                    except ImportError:
                        # If in scraping directory, import directly
                        import sys
                        from pathlib import Path
                        scraping_dir = Path(__file__).parent.absolute()
                        if str(scraping_dir) not in sys.path:
                            sys.path.insert(0, str(scraping_dir))
                        from profile_classifier import ProfileClassifier
                
                profile_type = ProfileClassifier.classify_profile(profile_data)
                profile_data['type'] = profile_type.lower() if profile_type else 'other'
                profile_data['Type'] = profile_type or 'other'
            except Exception as e:
                print(f"   ⚠️  Error classifying profile: {e}")
                profile_data['type'] = 'other'
                profile_data['Type'] = 'other'
            
            # Publish to Redis if available
            if self.redis_client:
                try:
                    self.redis_client.publish_scraped_profile(profile_url, profile_data)
                    print(f"   ✅ Published to Redis: {profile_data.get('name', 'Unknown')} ({profile_data.get('type', 'unknown')})")
                except Exception as e:
                    print(f"   ⚠️  Error publishing to Redis: {e}")
            
            return profile_data
            
        except Exception as e:
            print(f"   ❌ Error scraping profile {profile_url}: {e}")
            return None
    
    def collect_profile_urls_from_feed(self, max_scrolls: int = 5) -> List[str]:
        """
        Scroll the feed and collect profile URLs.
        
        Args:
            max_scrolls: Maximum number of scrolls to perform
            
        Returns:
            List of profile URLs found
        """
        profile_urls = []
        
        print(f"\n   📜 Scrolling feed to discover profiles ({max_scrolls} scrolls)...")
        
        # Ensure we're on the feed
        if "linkedin.com/feed" not in self.page.url:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(2)
        
        # Bring page to front to ensure scrolling is visible
        self.page.bring_to_front()
        time.sleep(0.5)
        
        for i in range(max_scrolls):
            try:
                # Find posts on current screen
                post_selectors = [
                    '[data-view-name="feed-full-update"]',
                    '[componentkey*="urn:li:activity"]',
                ]
                
                for selector in post_selectors:
                    try:
                        elements = self.page.locator(selector).all()
                        if elements:
                            for elem in elements:
                                try:
                                    links = elem.locator('a[href*="/in/"]').all()
                                    for link in links:
                                        href = link.get_attribute('href')
                                        if href and '/in/' in href:
                                            # Parse URL properly
                                            if href.startswith('http'):
                                                url = href.split('?')[0]
                                            else:
                                                url = f"https://www.linkedin.com{href.split('?')[0]}"
                                            
                                            # Ensure it's a profile URL (not a post or other page)
                                            if '/in/' in url and url not in self.seen_urls:
                                                if url not in profile_urls:
                                                    profile_urls.append(url)
                                                    self.seen_urls.add(url)
                                except:
                                    pass
                            break
                    except:
                        pass
                
                # Show progress during scrolling
                print(f"   → Scroll {i+1}/{max_scrolls}... {len(profile_urls)} profiles found so far", end='\r')
                
                # Smooth scroll with visible animation
                scroll_amount = random.randint(400, 600)
                self.page.evaluate(f'''
                    const scrollAmount = {scroll_amount};
                    
                    // Try multiple scroll containers for maximum compatibility
                    let container = document.querySelector('.scaffold-layout__main');
                    if (container) {{
                        container.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                    }}
                    
                    let main = document.querySelector('main');
                    if (main) {{
                        main.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                    }}
                    
                    window.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                ''')
                
                # Wait for smooth scroll animation to complete (longer wait makes it more visible)
                time.sleep(random.uniform(1.5, 2.0))
                
                # Additional pause for human-like behavior
                delay = random.uniform(0.8, 1.5)
                # Occasional longer pause (simulating reading)
                if random.random() < 0.15:  # 15% chance
                    delay += random.uniform(1.0, 2.0)
                time.sleep(delay)
                
            except Exception as e:
                print(f"   ⚠️  Scroll error: {e}")
                time.sleep(1)
        
        # Clear the progress line and print final result
        print(f"\n   ✅ Collected {len(profile_urls)} profile URLs")
        return profile_urls
    
    def scrape_feed_profiles(self, max_profiles: int = 5, max_scrolls: int = 10) -> List[Dict]:
        """
        Scrape profiles from the LinkedIn feed.
        
        Args:
            max_profiles: Maximum number of profiles to scrape
            max_scrolls: Maximum number of scrolls to perform
            
        Returns:
            List of scraped profile data
        """
        print(f"\n{'='*60}")
        print(f"🔍 SCRAPING FEED PROFILES")
        print(f"{'='*60}")
        print(f"Target: {max_profiles} profiles")
        print(f"Max scrolls: {max_scrolls}")
        print(f"{'='*60}\n")
        
        # Collect profile URLs
        profile_urls = self.collect_profile_urls_from_feed(max_scrolls=max_scrolls)
        
        if not profile_urls:
            print("⚠️  No profile URLs found in feed")
            return []
        
        # Scrape profiles (limit to max_profiles)
        scraped = []
        for i, url in enumerate(profile_urls[:max_profiles], 1):
            print(f"\n[{i}/{min(len(profile_urls), max_profiles)}] Processing profile...")
            profile = self.scrape_profile_from_url(url)
            if profile:
                scraped.append(profile)
                self.scraped_profiles.append(profile)
                time.sleep(random.uniform(1.0, 2.0))
        
        print(f"\n✅ Scraped {len(scraped)} profiles")
        return scraped
    
    def collect_post_urls_from_feed(self, max_scrolls: int = 5) -> List[str]:
        """
        Collect post URLs from the feed.
        
        Args:
            max_scrolls: Maximum number of scrolls to perform
            
        Returns:
            List of post URLs
        """
        post_urls = []
        
        print(f"   📜 Collecting post URLs ({max_scrolls} scrolls)...")
        
        # Ensure we're on the feed
        if "linkedin.com/feed" not in self.page.url:
            self.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
            time.sleep(2)
        
        for i in range(max_scrolls):
            try:
                # Find post links
                post_links = self.page.locator('a[href*="/feed/update/"]').all()
                for link in post_links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/feed/update/' in href:
                            url = href.split('?')[0]
                            if url and url not in self.seen_urls:
                                post_urls.append(url)
                                self.seen_urls.add(url)
                    except:
                        pass
                
                # Scroll down
                scroll_amount = random.randint(400, 600)
                self.page.evaluate(f'''
                    const scrollAmount = {scroll_amount};
                    let container = document.querySelector('.scaffold-layout__main');
                    if (container) container.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                ''')
                
                time.sleep(random.uniform(1.5, 2.5))
                
            except Exception as e:
                print(f"   ⚠️  Scroll error: {e}")
                time.sleep(1)
        
        print(f"   ✅ Collected {len(post_urls)} post URLs")
        return post_urls

