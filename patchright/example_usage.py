"""
Simple example of how to use the LinkedIn Profile Scraper.
"""

from linkedin_scraper import LinkedInScraper

# Example 1: Scrape Profiles from Feed (RECOMMENDED)
def scrape_profiles_example():
    """Example: Scrape profiles of people who post in the feed."""
    # Set debug=True to see detailed logging
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login (manual - you'll log in through the browser)
        scraper.login(manual=True)
        
        # Scrape profiles with stealth mode
        profiles = scraper.scrape_profiles_from_feed(
            max_profiles=5,  # Recommended: 5-15 per session
            stealth_mode=True  # Keep this enabled!
        )
        
        # Save data in multiple formats
        if profiles:
            scraper.save_data(profiles, "linkedin_profiles", format="json")
            scraper.save_data(profiles, "linkedin_profiles", format="csv")
            scraper.save_data(profiles, "linkedin_profiles", format="excel")
            print(f"✅ Scraped {len(profiles)} profiles")
            print(f"📁 Data saved in: {scraper.data_dir}")
        else:
            print("⚠️  No profiles scraped. Try enabling debug mode.")


# Example 2: Scrape Specific Profile URL
def scrape_single_profile_example():
    """Example: Scrape a specific LinkedIn profile by URL."""
    # Replace with an actual LinkedIn profile URL
    profile_url = "https://www.linkedin.com/in/example-profile"
    
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login (manual - you'll log in through the browser)
        scraper.login(manual=True)
        
        # Scrape profile
        print(f"Scraping profile: {profile_url}")
        profile_data = scraper.scrape_profile(profile_url)
        
        # Save data
        if profile_data and "error" not in profile_data:
            scraper.save_data(profile_data, "linkedin_profile", format="json")
            scraper.save_data(profile_data, "linkedin_profile", format="excel")
            print("✅ Profile scraped successfully")
            print(f"📁 Data saved in: {scraper.data_dir}")
        else:
            print("⚠️  Failed to scrape profile")


# Example 3: Scrape More Profiles with Custom Settings
def scrape_more_profiles_example():
    """Example: Scrape more profiles with custom settings."""
    
    with LinkedInScraper(headless=False, debug=False) as scraper:
        # Login once
        scraper.login(manual=True)
        
        # Scrape more profiles (10 is still safe)
        profiles = scraper.scrape_profiles_from_feed(
            max_profiles=10,  # Can go up to 15 per session
            stealth_mode=True
        )
        
        # Save all profiles
        if profiles:
            scraper.save_data(profiles, "linkedin_profiles_batch", format="json")
            scraper.save_data(profiles, "linkedin_profiles_batch", format="excel")
            print(f"\n✅ Scraped {len(profiles)} profiles")
            print(f"📁 Data saved in: {scraper.data_dir}")


# Example 4: Get Just Profile URLs (No Scraping)
def get_profile_urls_example():
    """Example: Just collect profile URLs from feed without scraping."""
    
    with LinkedInScraper(headless=False, debug=False) as scraper:
        scraper.login(manual=True)
        
        # Just get URLs
        profile_urls = scraper.get_profile_urls_from_feed(max_profiles=20)
        
        print(f"\n✅ Found {len(profile_urls)} profile URLs:")
        for url in profile_urls:
            print(f"  - {url}")
        
        # Save URLs to file
        import json
        with open('scraped_data/profile_urls.json', 'w') as f:
            json.dump(profile_urls, f, indent=2)


if __name__ == "__main__":
    # Run the profile scraping example
    print("="*60)
    print("LinkedIn Profile Scraper - Examples")
    print("="*60)
    
    # RECOMMENDED: Scrape profiles from feed with stealth
    scrape_profiles_example()
    
    # Uncomment to run other examples:
    # scrape_single_profile_example()
    # scrape_more_profiles_example()
    # get_profile_urls_example()

