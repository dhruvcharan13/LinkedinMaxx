"""
LinkedIn Profile Finder with Dual Targets

Finds Waterloo students AND recruiters/founders separately.
Tracks each type and saves them with appropriate naming.
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from linkedin_scraper import LinkedInScraper
from profile_classifier import ProfileClassifier


def main():
    """Find Waterloo students and recruiters from LinkedIn feed."""
    print("="*60)
    print("LINKEDIN DUAL-TARGET PROFILE FINDER")
    print("="*60)
    print("Finds Waterloo students AND recruiters/founders")
    print("="*60)
    
    # Get targets
    target_waterloo = 5
    target_recruiters = 3
    
    print(f"\nHow many profiles to find?")
    waterloo_input = input(f"Waterloo students (default: {target_waterloo}): ").strip()
    if waterloo_input and waterloo_input.isdigit():
        target_waterloo = int(waterloo_input)
    
    recruiter_input = input(f"Recruiters/Founders (default: {target_recruiters}): ").strip()
    if recruiter_input and recruiter_input.isdigit():
        target_recruiters = int(recruiter_input)
    
    print(f"\n✓ Target: {target_waterloo} Waterloo + {target_recruiters} Recruiters")
    print("Will continue scraping until BOTH targets are met!")
    print("="*60 + "\n")
    
    # Start scraper
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login
        print("Opening browser...")
        scraper.login(manual=True)
        
        # Create session folder in the same directory as this script
        script_dir = Path(__file__).parent.absolute()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = script_dir / "scraped_data" / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Session folder: {session_dir}\n")
        
        # Navigate to feed
        print("📍 Navigating to LinkedIn feed...")
        scraper.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
        print("✓ On LinkedIn feed")
        
        # Wait for feed to load and click on it to ensure it's focused
        print("Waiting for feed content to load...")
        try:
            scraper.page.wait_for_selector('[data-view-name="feed-full-update"]', timeout=10000)
            # Click on the feed area to ensure focus
            scraper.page.evaluate('document.body.click()')
            time.sleep(2)
            print("✓ Feed ready")
        except:
            time.sleep(3)
            print("✓ Continuing...")
        
        print("\n" + "="*60)
        print("HOW THIS WORKS")
        print("="*60)
        print("1. Scrolls feed and checks profiles one-by-one")
        print("2. Classifies each as: Waterloo, Recruiter, or Other")
        print("3. Stops when BOTH targets met")
        print("   (Won't stop at 5 Waterloo if still need recruiters!)")
        print("="*60)
        input("\nPress ENTER to start... ")
        
        # Tracking
        waterloo_profiles = []
        recruiter_profiles = []
        checked = 0
        session_start = time.time()
        seen_urls = set()
        max_scrolls = 100
        scroll_count = 0
        
        print("\n" + "="*60)
        print("STARTING PROFILE SEARCH")
        print("="*60)
        
        batch_number = 0
        
        while scroll_count < max_scrolls:
            # Check if both targets met
            if len(waterloo_profiles) >= target_waterloo and len(recruiter_profiles) >= target_recruiters:
                print(f"\n{'='*60}")
                print(f"✅ BOTH TARGETS MET!")
                print(f"Waterloo: {len(waterloo_profiles)}/{target_waterloo}")
                print(f"Recruiters: {len(recruiter_profiles)}/{target_recruiters}")
                print(f"{'='*60}")
                break
            
            batch_number += 1
            print(f"\n{'='*60}")
            print(f"BATCH {batch_number}")
            print(f"{'='*60}")
            print(f"Progress: Waterloo {len(waterloo_profiles)}/{target_waterloo}, Recruiters {len(recruiter_profiles)}/{target_recruiters}")
            
            # PHASE 1: Scroll and collect URLs (VISIBLE)
            print(f"\n📜 Scrolling feed to discover profiles...")
            profile_urls_batch = []
            scrolls_per_batch = random.randint(5, 8)  # Random 5-8 scrolls per batch
            
            for i in range(scrolls_per_batch):
                if scroll_count >= max_scrolls:
                    break
                
                try:
                    # Find posts on current screen
                    post_selectors = [
                        '[data-view-name="feed-full-update"]',
                        '[componentkey*="urn:li:activity"]',
                    ]
                    
                    for selector in post_selectors:
                        try:
                            elements = scraper.page.locator(selector).all()
                            if elements:
                                for elem in elements:
                                    try:
                                        links = elem.locator('a[href*="/in/"]').all()
                                        for link in links:
                                            href = link.get_attribute('href')
                                            if href and '/in/' in href:
                                                url = href.split('?')[0]
                                                if url not in seen_urls and url not in profile_urls_batch:
                                                    profile_urls_batch.append(url)
                                                    seen_urls.add(url)
                                                    break
                                    except:
                                        pass
                                break
                        except:
                            pass
                    
                    # Show progress
                    print(f"   Scroll {i+1}/{scrolls_per_batch}... {len(profile_urls_batch)} profiles found")
                    
                    # Smooth scroll with smaller increments
                    scroll_amount = random.randint(400, 600)  # Smaller scrolls for smoother feel
                    scraper.page.bring_to_front()  # Ensure page is focused
                    
                    # Only use smooth scrollBy (no instant scrollTop)
                    scraper.page.evaluate(f'''
                        const scrollAmount = {scroll_amount};
                        
                        // Try .scaffold-layout__main container with smooth behavior only
                        let container = document.querySelector('.scaffold-layout__main');
                        if (container) {{
                            container.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                        }}
                        
                        // Try main element
                        let main = document.querySelector('main');
                        if (main) {{
                            main.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                        }}
                        
                        // Try window
                        window.scrollBy({{top: scrollAmount, behavior: "smooth"}});
                    ''')
                    
                    # Wait longer for smooth scroll animation to complete
                    time.sleep(random.uniform(1.5, 2.0))
                    
                    # Additional pause between scrolls for more human-like behavior
                    delay = random.uniform(0.8, 1.5)
                    # Occasional longer pause (reading something)
                    if random.random() < 0.15:  # 15% chance
                        delay += random.uniform(1.5, 3.0)
                        print(f"      (pausing to 'read'...)")
                    time.sleep(delay)
                    scroll_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Scroll error: {e}")
                    # Try all scroll methods even in error case
                    scraper.page.evaluate('''
                        const scrollAmount = 800;
                        let container = document.querySelector('.scaffold-layout__main');
                        if (container) container.scrollTop += scrollAmount;
                        let main = document.querySelector('main');
                        if (main) main.scrollTop += scrollAmount;
                        document.body.scrollTop += scrollAmount;
                        document.documentElement.scrollTop += scrollAmount;
                        window.scrollBy({top: scrollAmount, behavior: "smooth"});
                    ''')
                    time.sleep(1)
                    scroll_count += 1
            
            print(f"✓ Collected {len(profile_urls_batch)} new profile URLs\n")
            
            if not profile_urls_batch:
                print("⚠️  No new profiles found, scrolling more...")
                continue
            
            # PHASE 2: Check collected profiles
            print(f"🔍 Analyzing {len(profile_urls_batch)} profiles...")
            print()
            
            for url in profile_urls_batch:
                checked += 1
                print(f"   [{checked}] {url}... ", end="", flush=True)
                
                try:
                    # Scrape profile (this automatically publishes to Redis if available)
                    profile = scraper.scrape_profile(url)
                    
                    if not profile or "error" in profile:
                        print("✗ Failed")
                        time.sleep(random.uniform(0.3, 0.7))
                        continue
                    
                    # Classify profile (scrape_profile already adds type field, but we classify again for consistency)
                    profile_type = ProfileClassifier.classify_profile(profile)
                    
                    # Ensure type field is set (scrape_profile should have done this, but double-check)
                    if 'type' not in profile and 'Type' in profile:
                        profile['type'] = profile['Type'].lower()
                    elif 'type' not in profile:
                        profile['type'] = profile_type or 'other'
                        profile['Type'] = profile_type or 'other'
                    
                    if profile_type == "waterloo":
                        if len(waterloo_profiles) < target_waterloo:
                            profile['Type'] = 'waterloo'
                            waterloo_profiles.append(profile)
                            
                            # Save immediately
                            filename = f"waterloo_{len(waterloo_profiles)}.json"
                            with open(session_dir / filename, 'w') as f:
                                json.dump(profile, f, indent=2)
                            
                            name = profile.get('name', 'Unknown')
                            print(f"✓ WATERLOO! {name} [{len(waterloo_profiles)}/{target_waterloo}]")
                            print(f"       💾 Saved: {filename}")
                            time.sleep(random.uniform(1.0, 2.0))
                        else:
                            print(f"✓ Waterloo (target met, skipping)")
                            time.sleep(random.uniform(0.3, 0.7))
                    
                    elif profile_type == "recruiter":
                        if len(recruiter_profiles) < target_recruiters:
                            profile['Type'] = 'recruiter'
                            recruiter_profiles.append(profile)
                            
                            # Save immediately
                            filename = f"recruiter_{len(recruiter_profiles)}.json"
                            with open(session_dir / filename, 'w') as f:
                                json.dump(profile, f, indent=2)
                            
                            name = profile.get('name', 'Unknown')
                            print(f"✓ RECRUITER! {name} [{len(recruiter_profiles)}/{target_recruiters}]")
                            print(f"       💾 Saved: {filename}")
                            time.sleep(random.uniform(1.0, 2.0))
                        else:
                            print(f"✓ Recruiter (target met, skipping)")
                            time.sleep(random.uniform(0.3, 0.7))
                    
                    else:
                        print(f"✗ Other")
                        time.sleep(random.uniform(0.5, 1.0))
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
                    time.sleep(random.uniform(0.5, 1.0))
                
                # Check if both targets met
                if len(waterloo_profiles) >= target_waterloo and len(recruiter_profiles) >= target_recruiters:
                    break
            
            # Show batch summary
            print(f"\n{'='*60}")
            print(f"BATCH {batch_number} COMPLETE")
            print(f"Waterloo: {len(waterloo_profiles)}/{target_waterloo}")
            print(f"Recruiters: {len(recruiter_profiles)}/{target_recruiters}")
            print(f"{'='*60}")
            
            # Navigate back to feed for next batch
            if len(waterloo_profiles) < target_waterloo or len(recruiter_profiles) < target_recruiters:
                print(f"\n📍 Returning to LinkedIn feed for next batch...")
                scraper.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
                try:
                    scraper.page.wait_for_selector('[data-view-name="feed-full-update"]', timeout=10000)
                    scraper.page.evaluate('document.body.click()')  # Focus the page
                    time.sleep(random.uniform(2.0, 3.0))
                    print("✓ Back on feed, ready to scroll")
                except:
                    time.sleep(3)
                    print("✓ Back on feed")
        
        # Save summary
        print(f"\n{'='*60}")
        print("CREATING SUMMARY FILES")
        print(f"{'='*60}")
        
        all_profiles = waterloo_profiles + recruiter_profiles
        summary = {
            "waterloo": waterloo_profiles,
            "recruiters": recruiter_profiles,
            "counts": {
                "waterloo": len(waterloo_profiles),
                "recruiters": len(recruiter_profiles),
                "total_checked": checked
            }
        }
        
        with open(session_dir / "summary_all.json", 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Saved: summary_all.json")
        
        # Save log
        with open(session_dir / "session_log.txt", 'w') as f:
            f.write(f"Session: {timestamp}\n")
            f.write(f"Profiles checked: {checked}\n")
            f.write(f"Waterloo students: {len(waterloo_profiles)}/{target_waterloo}\n")
            f.write(f"Recruiters: {len(recruiter_profiles)}/{target_recruiters}\n")
            f.write(f"Duration: {(time.time() - session_start)/60:.1f} minutes\n\n")
            f.write("Waterloo Students:\n")
            for i, p in enumerate(waterloo_profiles, 1):
                f.write(f"{i}. {p.get('name', 'Unknown')}\n")
            f.write("\nRecruiters:\n")
            for i, p in enumerate(recruiter_profiles, 1):
                f.write(f"{i}. {p.get('name', 'Unknown')}\n")
        print(f"✓ Saved: session_log.txt")
        
        print(f"\n✅ COMPLETE!")
        print(f"Session folder: {session_dir}/")
        print(f"\nIndividual files:")
        for i in range(1, len(waterloo_profiles) + 1):
            print(f"   - waterloo_{i}.json")
        for i in range(1, len(recruiter_profiles) + 1):
            print(f"   - recruiter_{i}.json")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

