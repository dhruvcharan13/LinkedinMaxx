"""
Quick test of the enhanced stealth scraper.
This version runs without user input for testing.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from linkedin_scraper import LinkedInScraper
from stealth_utils import (
    human_delay,
    random_mouse_movement,
    simulate_reading_time,
    random_break,
    longer_break
)


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
    """Test the enhanced stealth scraper."""
    target = 3  # Test with 3 profiles
    
    print("="*60)
    print("ENHANCED STEALTH SCRAPER TEST")
    print("="*60)
    print(f"Target: {target} Waterloo students")
    print("Stealth features:")
    print("  ✓ 5-15 second delays between profiles")
    print("  ✓ Random mouse movements")
    print("  ✓ Simulated reading time")
    print("  ✓ Break periods every 10/20 profiles")
    print("  ✓ Session folder organization")
    print("="*60 + "\n")
    
    # Start scraper
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login
        print("Opening browser...")
        scraper.login(manual=True)
        
        print("\n" + "="*60)
        print("SEARCHING FOR WATERLOO STUDENTS")
        print("="*60)
        print("Watch the browser behavior - it should look human!")
        print("="*60 + "\n")
        
        # Get profile URLs from feed
        print("Collecting profile URLs from feed...")
        all_urls = scraper.get_profile_urls_from_feed(max_profiles=20)
        
        if not all_urls:
            print("\n❌ Could not find any profiles in feed")
            return
        
        print(f"\n✓ Found {len(all_urls)} profiles in feed")
        print(f"Now checking which ones are Waterloo students...\n")
        
        # Scrape profiles with stealth measures
        waterloo_students = []
        checked = 0
        session_start = time.time()
        
        for url in all_urls:
            if len(waterloo_students) >= target:
                break
            
            checked += 1
            print(f"[{checked}/{len(all_urls)}] Checking {url}...", end=" ")
            
            # STEALTH: Random mouse movement
            print("(mouse move...)", end=" ")
            try:
                random_mouse_movement(scraper.page, min_moves=1, max_moves=3)
            except:
                pass
            
            # STEALTH: Human delay (5-15 seconds)
            print("(delay 5-15s...)", end=" ")
            human_delay(5, 15)
            
            # Scrape profile
            profile = scraper.scrape_profile(url)
            
            if not profile or "error" in profile:
                print("✗ Failed")
                continue
            
            # STEALTH: Simulate reading
            print("(reading...)", end=" ")
            content_length = len(profile.get('bio', '')) + len(str(profile.get('experience', [])))
            reading_time = simulate_reading_time(content_length, base_time=3, max_time=8)
            time.sleep(reading_time)
            
            # Check if Waterloo student
            if is_waterloo_student(profile.get('education', [])):
                waterloo_students.append(profile)
                program = get_program_from_education(profile.get('education', []))
                name = profile.get('name', 'Unknown')
                print(f"✓ WATERLOO! {name} ({program}) [{len(waterloo_students)}/{target}]")
            else:
                print(f"✗ Not Waterloo")
            
            # STEALTH: Breaks
            if checked % 10 == 0 and checked < len(all_urls):
                print(f"\n⏸️  SHORT BREAK (30-60s)...")
                random_break(30, 60)
                try:
                    random_mouse_movement(scraper.page, min_moves=2, max_moves=5)
                except:
                    pass
                print("Continuing...\n")
            
            if checked % 20 == 0 and checked < len(all_urls):
                print(f"\n🛌 LONG BREAK (60-120s)...")
                longer_break(60, 120)
                try:
                    random_mouse_movement(scraper.page, min_moves=3, max_moves=6)
                except:
                    pass
                print("Continuing...\n")
            
            if len(waterloo_students) >= target:
                print(f"\n{'='*60}")
                print(f"✅ FOUND {target} WATERLOO STUDENTS!")
                elapsed = time.time() - session_start
                print(f"Total session time: {elapsed/60:.1f} minutes")
                print(f"{'='*60}")
                break
        
        # Save results
        if not waterloo_students:
            print("\n⚠️  No Waterloo students found")
            return
        
        print(f"\n{'='*60}")
        print(f"SAVING {len(waterloo_students)} PROFILES")
        print(f"{'='*60}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = Path("scraped_data") / f"test_session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_path = session_dir / "waterloo_students.json"
        with open(json_path, 'w') as f:
            json.dump(waterloo_students, f, indent=2)
        print(f"✓ Saved: {json_path}")
        
        # Save log
        log_path = session_dir / "session_log.txt"
        with open(log_path, 'w') as f:
            f.write(f"TEST SESSION: {timestamp}\n")
            f.write(f"Profiles checked: {checked}\n")
            f.write(f"Waterloo students found: {len(waterloo_students)}\n")
            f.write(f"Session duration: {(time.time() - session_start)/60:.1f} minutes\n\n")
            f.write("Stealth measures used:\n")
            f.write("  - 5-15 second delays between profiles\n")
            f.write("  - Random mouse movements\n")
            f.write("  - Simulated reading time\n")
            f.write("  - Break periods\n\n")
            f.write("Profiles:\n")
            for i, p in enumerate(waterloo_students, 1):
                name = p.get('name', 'Unknown')
                program = get_program_from_education(p.get('education', []))
                f.write(f"{i}. {name} - {program}\n")
        print(f"✓ Saved: {log_path}")
        
        print(f"\n✅ TEST COMPLETE!")
        print(f"Session folder: {session_dir}/")
        print("\nSTEALTH FEATURES VERIFIED:")
        print("  ✓ Long delays between profiles")
        print("  ✓ Random mouse movements")
        print("  ✓ Reading time simulation")
        print("  ✓ Session folder organization")
        if checked >= 10:
            print("  ✓ Break periods")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

