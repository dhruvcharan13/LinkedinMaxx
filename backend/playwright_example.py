"""
Example Playwright integration code for LinkedInMaxx.
Shows how to publish scraped profiles and consume instructions from Redis.
"""

import redis
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)


def publish_scraped_profile(profile_data: Dict[str, Any]) -> str:
    """
    Publish a scraped profile to Redis queue for agents to process.
    
    Args:
        profile_data: Scraped profile data with url, name, headline, bio, experience, education
        
    Returns:
        Task ID
    """
    queue_name = "profiles:scraped"
    task_id = f"{queue_name}:{datetime.now().isoformat()}"
    
    instruction = {
        "task_id": task_id,
        "queue": queue_name,
        "instruction": {
            "action": "process_profile",
            "profile_url": profile_data["url"],
            "profile_data": profile_data,
            "timestamp": datetime.now().isoformat()
        },
        "status": "pending"
    }
    
    # Push to queue
    redis_client.lpush(queue_name, json.dumps(instruction))
    print(f"✅ Published profile to queue: {profile_data['url']}")
    
    return task_id


def consume_post_instruction() -> Optional[Dict[str, Any]]:
    """
    Consume a post instruction from Redis queue.
    
    Returns:
        Instruction data or None if queue is empty
    """
    queue_name = "playwright:post"
    
    # Blocking pop (waits up to 5 seconds)
    result = redis_client.brpop(queue_name, timeout=5)
    
    if result:
        _, data = result
        instruction = json.loads(data)
        return instruction
    
    return None


def consume_message_instruction() -> Optional[Dict[str, Any]]:
    """
    Consume a message/connection instruction from Redis queue.
    
    Returns:
        Instruction data or None if queue is empty
    """
    queue_name = "playwright:message"
    
    # Blocking pop (waits up to 5 seconds)
    result = redis_client.brpop(queue_name, timeout=5)
    
    if result:
        _, data = result
        instruction = json.loads(data)
        return instruction
    
    return None


def get_queue_stats() -> Dict[str, int]:
    """Get queue statistics."""
    return {
        "profiles_scraped": redis_client.llen("profiles:scraped"),
        "playwright_post": redis_client.llen("playwright:post"),
        "playwright_message": redis_client.llen("playwright:message"),
    }


# Example usage with Playwright
async def example_playwright_integration():
    """
    Example of how to integrate with Playwright.
    Replace the Playwright-specific code with your actual implementation.
    """
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Login to LinkedIn (your login code here)
        # await page.goto("https://www.linkedin.com/login")
        # ... login logic ...
        
        # Start consuming instructions in background
        async def consume_instructions_loop():
            """Consume and execute instructions."""
            while True:
                # Consume post instructions
                post_instruction = consume_post_instruction()
                if post_instruction:
                    content = post_instruction["instruction"]["content"]
                    print(f"📝 Would publish post: {content[:100]}...")
                    # Your Playwright code to publish post
                    # await page.goto("https://www.linkedin.com/feed/")
                    # await page.fill('[data-testid="post-input"]', content)
                    # await page.click('[data-testid="post-submit"]')
                
                # Consume message instructions
                message_instruction = consume_message_instruction()
                if message_instruction:
                    inst = message_instruction["instruction"]
                    profile_url = inst["profile_url"]
                    action = inst["action"]
                    message = inst.get("message", "")
                    
                    print(f"📨 Would {action} for {profile_url}")
                    if message:
                        print(f"   Message: {message[:50]}...")
                    # Your Playwright code to send message/connect
                    # await page.goto(profile_url)
                    # ... connection/message logic ...
                
                await asyncio.sleep(1)  # Brief pause
        
        # Start consumer in background
        consumer_task = asyncio.create_task(consume_instructions_loop())
        
        # Scrape profiles and publish
        try:
            while True:
                # Your scraping logic here
                # profile_urls = await scrape_linkedin_feed(page)
                
                # Example: Scrape a profile
                # for url in profile_urls:
                #     profile_data = await scrape_profile(page, url)
                #     publish_scraped_profile(profile_data)
                
                # For testing, publish a test profile
                test_profile = {
                    "url": "https://www.linkedin.com/in/test/",
                    "scraped_at": datetime.now().isoformat(),
                    "name": "Test User",
                    "headline": "Test Headline",
                    "bio": "Test bio",
                    "experience": [],
                    "education": []
                }
                publish_scraped_profile(test_profile)
                
                await asyncio.sleep(10)  # Wait before next scrape
                
        except KeyboardInterrupt:
            print("Stopping...")
            consumer_task.cancel()
            await browser.close()


if __name__ == "__main__":
    # Test Redis connection
    try:
        redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        exit(1)
    
    # Show queue stats
    stats = get_queue_stats()
    print(f"Queue stats: {stats}")
    
    # Uncomment to run full integration example
    # asyncio.run(example_playwright_integration())

