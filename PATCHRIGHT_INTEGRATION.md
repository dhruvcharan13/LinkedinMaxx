# Patchright Integration Guide

## Understanding Patchright Code

### Current Structure

```
patchright/
├── linkedin_scraper.py          # Main scraper class
├── find_waterloo_students.py    # Waterloo student finder script
├── example_usage.py             # Usage examples
├── stealth_utils.py             # Human-like behavior utilities
├── requirements.txt             # Dependencies (patchright, pandas, etc.)
├── scraped_data/                # Local storage (JSON, CSV, Excel)
└── browser_data/                # Persistent browser session
```

### How Patchright Works

1. **Uses Patchright** (stealth Playwright) for LinkedIn automation
2. **Persistent browser session** - Logs in once, reuses session
3. **Stealth mode** - Human-like delays, mouse movements, scrolling
4. **Scrapes profiles** from LinkedIn feed
5. **Saves locally** to `scraped_data/` folder (JSON, CSV, Excel)

### Key Components

#### `linkedin_scraper.py`
- `LinkedInScraper` class - Main scraper
- `scrape_profile(url)` - Scrapes a single profile
- `scrape_profiles_from_feed()` - Scrapes multiple profiles from feed
- `get_profile_urls_from_feed()` - Collects profile URLs
- `save_data()` - Saves to JSON/CSV/Excel

#### `find_waterloo_students.py`
- Scrolling script that finds Waterloo students
- Filters profiles by education (looks for "Waterloo")
- Saves results to session folder

#### `stealth_utils.py`
- Human-like delays
- Random mouse movements
- Human-like scrolling
- Profile visit simulation

## Integration with Backend Agents

### What Needs to Happen

**Current State:**
- Patchright scrapes profiles ✅
- Saves to local files ✅
- **Does NOT publish to Redis** ❌

**Required Integration:**
1. ✅ Backend agents are ready (consume from Redis)
2. ❌ Patchright needs to publish to Redis
3. ❌ Patchright needs to consume instructions from Redis

### Step 1: Add Redis Publishing to Patchright

**File: `patchright/linkedin_scraper.py`**

Add Redis integration:

```python
import redis
import json
from datetime import datetime

class LinkedInScraper:
    def __init__(self, ...):
        # ... existing code ...
        
        # Add Redis connection
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"⚠️  Redis not available: {e}")
            self.redis_client = None
    
    def publish_profile_to_redis(self, profile_data: Dict):
        """Publish scraped profile to Redis queue."""
        if not self.redis_client:
            print("⚠️  Redis not available, skipping publish")
            return None
        
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
        print(f"✅ Published to Redis: {profile_data.get('name', 'Unknown')}")
        return task_id
    
    def scrape_profile(self, profile_url: str) -> Dict:
        # ... existing scraping code ...
        
        # After scraping, publish to Redis
        if profile_data and "error" not in profile_data:
            self.publish_profile_to_redis(profile_data)
        
        return profile_data
```

**Update `patchright/requirements.txt`:**
```txt
patchright>=1.0.0
pandas>=2.0.0
openpyxl>=3.1.0
numpy>=1.24.0
redis>=5.0.0  # ADD THIS
```

### Step 2: Create Instruction Consumer

**File: `patchright/instruction_consumer.py` (NEW)**

```python
"""
Consumes instructions from Redis and executes with Playwright.
"""

import redis
import json
import time
from typing import Optional, Dict
from patchright.sync_api import sync_playwright
from linkedin_scraper import LinkedInScraper

class InstructionConsumer:
    """Consumes and executes instructions from Redis."""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.scraper = None
    
    def start(self):
        """Start browser and login."""
        print("🚀 Starting instruction consumer...")
        self.scraper = LinkedInScraper(headless=False)
        self.scraper.start()
        self.scraper.login(manual=True)
        print("✅ Ready to consume instructions")
    
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
        print(f"📝 Publishing post: {content[:50]}...")
        
        # Navigate to feed
        self.scraper.page.goto("https://www.linkedin.com/feed")
        time.sleep(2)
        
        # Find post input (update selectors as needed)
        # post_input = self.scraper.page.locator('[data-testid="post-input"]')
        # post_input.fill(content)
        # submit_button = self.scraper.page.locator('[data-testid="post-submit"]')
        # submit_button.click()
        
        print(f"✅ Post published: {instruction['task_id']}")
    
    def execute_message(self, instruction: Dict):
        """Execute a message/connection instruction."""
        inst = instruction["instruction"]
        profile_url = inst["profile_url"]
        action = inst["action"]
        message = inst.get("message", "")
        
        print(f"📨 Processing: {action} for {profile_url}")
        
        # Navigate to profile
        self.scraper.page.goto(profile_url)
        time.sleep(2)
        
        if action == "send_message":
            # Click Connect button
            # connect_btn = self.scraper.page.locator('button:has-text("Connect")')
            # connect_btn.click()
            # Wait for modal
            # message_input = self.scraper.page.locator('[data-testid="message-input"]')
            # message_input.fill(message)
            # send_btn = self.scraper.page.locator('[data-testid="send-button"]')
            # send_btn.click()
            print(f"✅ Sent message: {message[:50]}...")
        elif action == "connect_only":
            # Click Connect button (no message)
            # connect_btn = self.scraper.page.locator('button:has-text("Connect")')
            # connect_btn.click()
            print(f"✅ Sent connection request")
    
    def run(self):
        """Main loop to consume and execute instructions."""
        self.start()
        
        try:
            while True:
                # Consume post instructions
                post_inst = self.consume_post_instruction()
                if post_inst:
                    self.execute_post(post_inst)
                
                # Consume message instructions
                msg_inst = self.consume_message_instruction()
                if msg_inst:
                    self.execute_message(msg_inst)
                
                time.sleep(1)  # Brief pause
        except KeyboardInterrupt:
            print("\n👋 Stopping instruction consumer...")
            if self.scraper:
                self.scraper.close()

if __name__ == "__main__":
    consumer = InstructionConsumer()
    consumer.run()
```

### Step 3: Update find_waterloo_students.py

Modify to publish to Redis automatically:

```python
# In the main loop, after scraping a profile:
profile = scraper.scrape_profile(url)

# The scrape_profile method will now automatically publish to Redis
# (after we add the Redis integration)
```

## Data Flow

```
┌─────────────────────────────────────────┐
│         PATCHRIGHT (Scraper)            │
│  - Scrapes LinkedIn profiles            │
│  - Publishes to Redis: profiles:scraped │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│              REDIS QUEUES               │
│  • profiles:scraped (INPUT)             │
│  • playwright:post (OUTPUT)             │
│  • playwright:message (OUTPUT)          │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│       BACKEND (Agents)                  │
│  - Consumes from profiles:scraped       │
│  - Processes with MessagingAgent        │
│  - Routes to DatingAgent if Waterloo    │
│  - Publishes instructions to queues     │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│    PATCHRIGHT (Instruction Consumer)    │
│  - Consumes from playwright:post        │
│  - Consumes from playwright:message     │
│  - Executes with Playwright             │
└─────────────────────────────────────────┘
```

## Running the System

### Terminal 1: Backend (Agents)
```bash
cd backend
python3 main.py
```

### Terminal 2: Patchright (Scraper)
```bash
cd patchright
python3 find_waterloo_students.py
# This will scrape and publish to Redis automatically
```

### Terminal 3: Instruction Consumer (Optional)
```bash
cd patchright
python3 instruction_consumer.py
# This will consume and execute instructions
```

## Testing

1. **Test Redis connection from Patchright:**
   ```python
   import redis
   r = redis.Redis(host='localhost', port=6379)
   r.ping()  # Should return True
   ```

2. **Test publishing a profile:**
   ```python
   from linkedin_scraper import LinkedInScraper
   scraper = LinkedInScraper()
   scraper.start()
   # Scrape a profile
   profile = scraper.scrape_profile("https://www.linkedin.com/in/...")
   # Should automatically publish to Redis
   ```

3. **Check queues:**
   ```bash
   redis-cli LLEN profiles:scraped
   redis-cli LLEN playwright:post
   redis-cli LLEN playwright:message
   ```

## Key Points

1. **Patchright scrapes** → Publishes to `profiles:scraped`
2. **Backend processes** → Publishes to `playwright:post` and `playwright:message`
3. **Patchright consumes** → Executes instructions
4. **All communication** through Redis queues
5. **Terminal feedback** shows all actions in real-time

## Next Steps

1. ✅ Add Redis to `patchright/requirements.txt`
2. ✅ Add `publish_profile_to_redis()` to `LinkedInScraper`
3. ✅ Create `instruction_consumer.py`
4. ✅ Test Redis integration
5. ✅ Test end-to-end flow

