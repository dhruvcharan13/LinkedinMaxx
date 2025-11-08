# Patchright ↔ Backend Integration Guide

## Overview

This guide explains how to integrate the Patchright scraper (`../patchright/`) with the backend agents.

## How Patchright Works

The Patchright code in `../patchright/`:

1. **Scrapes LinkedIn profiles** using stealth browser automation
2. **Saves data locally** to `scraped_data/` folder
3. **Does NOT currently publish to Redis** - needs integration

## Integration Steps

### Step 1: Update Patchright to Publish to Redis

Modify `../patchright/linkedin_scraper.py` to publish scraped profiles to Redis:

```python
import redis
import json
from datetime import datetime

# Add Redis connection at the top of LinkedInScraper class
def __init__(self, ...):
    # ... existing code ...
    
    # Add Redis connection
    self.redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )

# Add method to publish profile to Redis
def publish_profile_to_redis(self, profile_data: Dict):
    """Publish scraped profile to Redis queue for agents to process."""
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
    
    self.redis_client.lpush(queue_name, json.dumps(instruction))
    print(f"✅ Published profile to Redis: {profile_data.get('name', 'Unknown')}")
    return task_id

# Modify scrape_profile method to also publish to Redis
def scrape_profile(self, profile_url: str) -> Dict:
    # ... existing scraping code ...
    
    # After scraping, publish to Redis
    if profile_data and "error" not in profile_data:
        self.publish_profile_to_redis(profile_data)
    
    return profile_data
```

### Step 2: Add Instruction Consumers to Patchright

Create a new file `../patchright/instruction_consumer.py`:

```python
"""
Consume instructions from Redis and execute with Playwright.
"""

import redis
import json
import asyncio
from typing import Optional, Dict
from patchright.sync_api import sync_playwright

class InstructionConsumer:
    """Consumes and executes instructions from Redis."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.playwright = None
        self.browser = None
        self.page = None
    
    def start_browser(self):
        """Start browser for executing instructions."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()
        
        # Login to LinkedIn (reuse existing login logic)
        # ... login code ...
    
    def consume_post_instruction(self) -> Optional[Dict]:
        """Consume a post instruction from Redis."""
        result = self.redis_client.brpop("playwright:post", timeout=5)
        if result:
            _, data = result
            return json.loads(data)
        return None
    
    def consume_message_instruction(self) -> Optional[Dict]:
        """Consume a message/connection instruction from Redis."""
        result = self.redis_client.brpop("playwright:message", timeout=5)
        if result:
            _, data = result
            return json.loads(data)
        return None
    
    def execute_post(self, instruction: Dict):
        """Execute a post instruction."""
        content = instruction["instruction"]["content"]
        # Your Playwright code to publish post
        # self.page.goto("https://www.linkedin.com/feed/")
        # self.page.fill('[data-testid="post-input"]', content)
        # self.page.click('[data-testid="post-submit"]')
        print(f"✅ Posted: {content[:50]}...")
    
    def execute_message(self, instruction: Dict):
        """Execute a message/connection instruction."""
        inst = instruction["instruction"]
        profile_url = inst["profile_url"]
        action = inst["action"]
        message = inst.get("message", "")
        
        # Navigate to profile
        self.page.goto(profile_url)
        
        if action == "send_message":
            # Send connection request with message
            # ... your Playwright code ...
            print(f"✅ Sent message to {profile_url}")
        elif action == "connect_only":
            # Send connection request without message
            # ... your Playwright code ...
            print(f"✅ Connected to {profile_url}")
    
    def run(self):
        """Main loop to consume and execute instructions."""
        self.start_browser()
        
        while True:
            # Consume post instructions
            post_inst = self.consume_post_instruction()
            if post_inst:
                self.execute_post(post_inst)
            
            # Consume message instructions
            msg_inst = self.consume_message_instruction()
            if msg_inst:
                self.execute_message(msg_inst)
            
            # Brief pause
            import time
            time.sleep(1)
```

### Step 3: Run Both Systems

**Terminal 1 - Backend (Agents):**
```bash
cd backend
python3 main.py
```

**Terminal 2 - Patchright (Scraper):**
```bash
cd patchright
python3 find_waterloo_students.py
# or
python3 linkedin_scraper.py
```

**Terminal 3 - Instruction Consumer (Optional):**
```bash
cd patchright
python3 instruction_consumer.py
```

## Data Flow

```
1. Patchright scrapes profile
   ↓
2. Publishes to Redis: profiles:scraped
   ↓
3. Backend agents process profile
   ↓
4. Agents publish instructions to Redis:
   - playwright:post (for posts)
   - playwright:message (for messages/connections)
   ↓
5. Patchright consumes instructions
   ↓
6. Executes with Playwright
```

## Queue Formats

### Input: `profiles:scraped`

```json
{
  "task_id": "profiles:scraped:2025-11-08T16:47:09",
  "queue": "profiles:scraped",
  "instruction": {
    "action": "process_profile",
    "profile_url": "https://www.linkedin.com/in/...",
    "profile_data": {
      "url": "...",
      "name": "...",
      "headline": "...",
      "bio": "...",
      "experience": [...],
      "education": [...]
    }
  }
}
```

### Output: `playwright:post`

```json
{
  "task_id": "playwright:post:...",
  "instruction": {
    "action": "publish_post",
    "content": "Just finished building...",
    "metadata": {...}
  }
}
```

### Output: `playwright:message`

```json
{
  "task_id": "playwright:message:...",
  "instruction": {
    "action": "send_message",  // or "connect_only"
    "profile_url": "https://www.linkedin.com/in/...",
    "message": "Hey! Saw you're in 2A too..."
  }
}
```

## Quick Integration Checklist

- [ ] Add Redis dependency to `patchright/requirements.txt`
- [ ] Add `publish_profile_to_redis()` method to `LinkedInScraper`
- [ ] Modify `scrape_profile()` to publish after scraping
- [ ] Create `instruction_consumer.py` for consuming instructions
- [ ] Test Redis connection from Patchright
- [ ] Test publishing a profile to Redis
- [ ] Test consuming an instruction from Redis

## Testing

1. **Test Redis connection:**
   ```python
   import redis
   r = redis.Redis(host='localhost', port=6379, db=0)
   r.ping()  # Should return True
   ```

2. **Test publishing:**
   ```python
   # From Patchright
   test_profile = {"url": "https://...", "name": "Test", ...}
   scraper.publish_profile_to_redis(test_profile)
   ```

3. **Check queue:**
   ```bash
   redis-cli LLEN profiles:scraped
   redis-cli LLEN playwright:post
   redis-cli LLEN playwright:message
   ```

## Next Steps

1. Integrate Redis publishing into Patchright scraper
2. Create instruction consumer in Patchright
3. Test end-to-end flow
4. Add error handling and retries
5. Add rate limiting
