"""
Simple Waterloo Student Finder

Automatically scrolls LinkedIn feed and finds Waterloo students.
Browser does all the scrolling - you just watch!
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from linkedin_scraper import LinkedInScraper


def is_waterloo_student(education_list):
    """Check if someone went to Waterloo."""
    if not education_list:
        return False
    
    for edu in education_list:
        edu_str = str(edu).lower()
        if 'waterloo' in edu_str:
            return True
    return False


def get_program_from_education(education_list):
    """Extract program name from education."""
    for edu in education_list:
        if isinstance(edu, dict):
            degree = edu.get('degree', '').lower()
            if 'waterloo' in str(edu).lower():
                if 'software engineering' in degree:
                    return 'Software Engineering'
                elif 'computer science' in degree:
                    return 'Computer Science'
                elif 'math' in degree:
                    return 'Mathematics'
                elif 'engineering' in degree:
                    return 'Engineering'
                else:
                    return 'Waterloo Student'
    return 'Unknown Program'


def main():
    """Find Waterloo students from LinkedIn feed."""
    print("="*60)
    print("WATERLOO STUDENT FINDER")
    print("="*60)
    print("This will automatically scroll your LinkedIn feed")
    print("and find profiles of Waterloo students.")
    print("="*60)
    
    # Get target number
    target = 5
    change = input(f"\nFind how many Waterloo students? (default: {target}): ").strip()
    if change and change.isdigit():
        target = int(change)
    
    print(f"\n✓ Will search for {target} Waterloo students")
    print("The browser will scroll automatically until it finds them.")
    print("This may take a few minutes...")
    
    print("\n" + "="*60)
    print("STARTING")
    print("="*60 + "\n")
    
    # Start scraper
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login
        print("Opening browser...")
        scraper.login(manual=True)
        
        print("\n" + "="*60)
        print("SEARCHING FOR WATERLOO STUDENTS")
        print("="*60)
        print("Will scroll → check profile → repeat until 5 Waterloo students found")
        print("Watch the browser scroll!")
        print("="*60 + "\n")
        
        # Create session folder NOW (so we can save files as we go)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = Path("scraped_data") / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Session folder: {session_dir}\n")
        
        # Navigate to feed
        print("📍 Navigating to LinkedIn feed...")
        scraper.page.goto("https://www.linkedin.com/feed", wait_until="load", timeout=30000)
        print("✓ On LinkedIn feed: https://www.linkedin.com/feed")
        print("⏳ Waiting for page to fully load...")
        time.sleep(2)
        print("✓ Page loaded!\n")
        
        print("="*60)
        print("HOW THIS WORKS - READ THIS FIRST")
        print("="*60)
        print("1. LinkedIn shows 3-5 posts when you first load the feed")
        print("2. Script reads those posts and extracts profile URLs")
        print("3. Checks each profile → Is it a Waterloo student?")
        print("4. If found 5 Waterloo students → DONE!")
        print("5. If NOT found 5 yet → Scrolls down to load MORE posts")
        print("6. Repeat steps 2-5 until 5 Waterloo students found")
        print("="*60)
        print("\n⏸️  PAUSED - Look at the browser window!")
        print("You should see your LinkedIn feed with some posts visible.")
        input("Press ENTER when ready to start scraping those visible posts... ")
        
        # Scrape-as-we-scroll logic
        waterloo_students = []
        checked = 0
        session_start = time.time()
        seen_urls = set()
        max_scrolls = 100  # Safety limit
        scroll_count = 0
        
        print("\n" + "="*60)
        print("STARTING PROFILE DISCOVERY")
        print("="*60)
        
        while len(waterloo_students) < target and scroll_count < max_scrolls:
            # Find profile URLs on current view
            print(f"\n{'='*60}")
            print(f"🔍 STEP {scroll_count + 1}: Looking at feed CURRENTLY visible on screen")
            print(f"{'='*60}")
            print(f"→ Reading HTML of posts that are visible RIGHT NOW...")
            
            try:
                # Show what selectors we're using
                post_selectors = [
                    '[data-view-name="feed-full-update"]',
                    '[componentkey*="urn:li:activity"]',
                ]
                print(f"→ Using CSS selector: {post_selectors[0]}")
                
                profile_urls_in_view = []
                posts_found = 0
                
                for selector in post_selectors:
                    try:
                        elements = scraper.page.locator(selector).all()
                        if elements:
                            posts_found = len(elements)
                            print(f"→ ✓ Found {posts_found} posts currently visible")
                            print(f"→ Now extracting profile URLs from each post...")
                            
                            for idx, elem in enumerate(elements, 1):
                                try:
                                    # Find profile link in this post
                                    links = elem.locator('a[href*="/in/"]').all()
                                    for link in links:
                                        href = link.get_attribute('href')
                                        if href and '/in/' in href:
                                            url = href.split('?')[0]
                                            if url not in seen_urls:
                                                profile_urls_in_view.append(url)
                                                seen_urls.add(url)
                                                print(f"   ✓ Post #{idx}: {url}")
                                                # SLOW: Pause after each URL so user can see them appear
                                                time.sleep(random.uniform(0.3, 0.7))
                                                break  # Just get first profile per post
                                            else:
                                                print(f"   ⊘ Post #{idx}: Already checked this profile")
                                except:
                                    pass
                            break
                    except:
                        pass
                
                if not profile_urls_in_view:
                    print(f"\n⚠️  No NEW profiles found in these posts (all already checked)")
                    print(f"→ Will scroll to load MORE posts...")
                else:
                    print(f"\n✓ Found {len(profile_urls_in_view)} NEW profiles to check")
                    # SLOW: Pause so user can see what was found
                    pause = random.uniform(1, 2)
                    print(f"→ Pausing {pause:.1f}s to show you what was found...")
                    time.sleep(pause)
                
                # Check each profile found in this view
                if profile_urls_in_view:
                    print(f"\n{'='*60}")
                    print(f"👤 NOW CHECKING EACH PROFILE")
                    print(f"{'='*60}")
                    # SLOW: Pause before starting to check profiles
                    pause = random.uniform(1, 2)
                    print(f"→ Starting profile checks in {pause:.1f}s...")
                    time.sleep(pause)
                
                for url in profile_urls_in_view:
                    if len(waterloo_students) >= target:
                        break
                    
                    checked += 1
                    print(f"\n   [{checked}] {url}")
                    print(f"       → Navigating to profile...")
                    
                    # Quick check: scrape profile
                    profile = scraper.scrape_profile(url)
                    
                    if not profile or "error" in profile:
                        print(f"       ✗ Failed to scrape")
                        continue
                    
                    print(f"       → Scraped: {profile.get('name', 'Unknown')}")
                    print(f"       → Checking education for 'Waterloo'...", end=" ")
                    
                    # Check if Waterloo
                    if is_waterloo_student(profile.get('education', [])):
                        program = get_program_from_education(profile.get('education', []))
                        name = profile.get('name', 'Unknown')
                        print(f"✓ YES!")
                        print(f"       🎓 WATERLOO STUDENT FOUND!")
                        print(f"       Name: {name}")
                        print(f"       Program: {program}")
                        print(f"       Progress: [{len(waterloo_students) + 1}/{target}]")
                        
                        waterloo_students.append(profile)
                        
                        # SAVE IMMEDIATELY as individual file
                        filename = f"linkedin_account_{len(waterloo_students)}.json"
                        filepath = session_dir / filename
                        with open(filepath, 'w') as f:
                            json.dump(profile, f, indent=2)
                        print(f"       💾 Saved: {filename}")
                        
                        # FAST: Shorter delay after finding Waterloo (still random)
                        if len(waterloo_students) < target:
                            delay = random.uniform(1, 3)
                            print(f"       ⏳ Waiting {delay:.1f}s before continuing...")
                            time.sleep(delay)
                    else:
                        print(f"✗ No")
                    
                    # FAST: Shorter delay between profiles (still random)
                    time.sleep(random.uniform(0.5, 1))
                    
                    if len(waterloo_students) >= target:
                        break
                
                # Done? Stop!
                if len(waterloo_students) >= target:
                    print(f"\n{'='*60}")
                    print(f"✅ FOUND {target} WATERLOO STUDENTS!")
                    elapsed = time.time() - session_start
                    print(f"Profiles checked: {checked}")
                    print(f"Session time: {elapsed/60:.1f} minutes")
                    print(f"{'='*60}")
                    break
                
                # Scroll to load more
                if len(waterloo_students) < target:
                    print(f"\n{'='*60}")
                    print(f"📜 SCROLLING TO LOAD MORE POSTS")
                    print(f"{'='*60}")
                    print(f"→ Only found {len(waterloo_students)}/{target} Waterloo students so far")
                    print(f"→ Scrolling down to make NEW posts appear on screen...")
                    scraper.page.mouse.wheel(0, 800)
                    # SLOW: Longer pause after scrolling so user can SEE it
                    pause = random.uniform(1.5, 2.5)
                    print(f"→ ✓ Scrolled! Waiting {pause:.1f}s for new posts to load...")
                    time.sleep(pause)
                    scroll_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                # Try scrolling anyway
                scraper.page.mouse.wheel(0, 800)
                time.sleep(0.5)
                scroll_count += 1
        
        # Save results
        if not waterloo_students:
            print("\n⚠️  No Waterloo students found in feed")
            print("Try again later or check different connections")
            return
        
        print(f"\n{'='*60}")
        print(f"CREATING SUMMARY FILE")
        print(f"{'='*60}")
        
        # Save summary JSON (all profiles together)
        json_path = session_dir / f"summary_all_profiles.json"
        with open(json_path, 'w') as f:
            json.dump(waterloo_students, f, indent=2)
        print(f"✓ Saved: {json_path}")
        
        # Save CSV
        try:
            import pandas as pd
            
            csv_data = []
            for p in waterloo_students:
                program = get_program_from_education(p.get('education', []))
                csv_data.append({
                    'Name': p.get('name', 'Unknown'),
                    'Program': program,
                    'Headline': p.get('headline', 'N/A'),
                    'Location': p.get('location', 'N/A'),
                    'Bio': (p.get('bio', 'N/A')[:200] + '...') if p.get('bio') else 'N/A',
                    'Experience Count': len(p.get('experience', [])),
                    'Education Count': len(p.get('education', [])),
                    'Profile URL': p.get('url', 'N/A')
                })
            
            df = pd.DataFrame(csv_data)
            
            csv_path = session_dir / f"summary_all_profiles.csv"
            df.to_csv(csv_path, index=False)
            print(f"✓ Saved: {csv_path}")
            
            excel_path = session_dir / f"summary_all_profiles.xlsx"
            df.to_excel(excel_path, index=False)
            print(f"✓ Saved: {excel_path}")
        except Exception as e:
            print(f"⚠️  Could not save CSV/Excel: {e}")
        
        # Show summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Profiles checked: {checked}")
        print(f"Waterloo students found: {len(waterloo_students)}")
        print(f"\nProfiles:")
        for i, p in enumerate(waterloo_students, 1):
            name = p.get('name', 'Unknown')
            program = get_program_from_education(p.get('education', []))
            print(f"{i}. {name} - {program}")
        print(f"{'='*60}")
        
        # Save session log
        log_path = session_dir / "session_log.txt"
        with open(log_path, 'w') as f:
            f.write(f"Session: {timestamp}\n")
            f.write(f"Profiles checked: {checked}\n")
            f.write(f"Waterloo students found: {len(waterloo_students)}\n\n")
            f.write("Profiles:\n")
            for i, p in enumerate(waterloo_students, 1):
                name = p.get('name', 'Unknown')
                program = get_program_from_education(p.get('education', []))
                f.write(f"{i}. {name} - {program}\n")
        print(f"✓ Saved: {log_path}")
        
        print(f"\n✅ DONE!")
        print(f"\n📁 All files saved in: {session_dir}/")
        print(f"\nIndividual files:")
        for i in range(1, len(waterloo_students) + 1):
            print(f"   - linkedin_account_{i}.json")
        print(f"\nSummary files:")
        print(f"   - summary_all_profiles.json")
        print(f"   - summary_all_profiles.csv")
        print(f"   - summary_all_profiles.xlsx")
        print(f"   - session_log.txt")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

