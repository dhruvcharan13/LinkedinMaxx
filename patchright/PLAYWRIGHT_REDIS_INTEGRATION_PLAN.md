# Playwright-Redis Integration Plan

## Current State Analysis

### What Playwright Does:

1. **Messaging (`messaging/linkedin_messenger.py`)**:
   - Reads from `test_profile.json` or terminal input
   - Has `send_message(profile_url, message)` and `send_connection_request(profile_url, note)`
   - Uses `input()` prompts for user interaction
   - Format: `{"profile_url": "...", "name": "...", "message": "..."}`

2. **Posting (`posting/linkedin_poster.py`)**:
   - Reads from terminal input (`input()`)
   - Has `create_post(text, image_path=None)` method
   - Uses manual input prompts

3. **Commenting (`commenting/linkedin_commenter.py`)**:
   - Reads from `test_comment.json` or terminal input
   - Has `post_comment(post_url, comment)` method
   - Uses manual input prompts
   - Format: `{"post_url": "...", "comment": "..."}`

4. **Scraping (`scraping/linkedin_scraper.py`)**:
   - Saves scraped data to files in `scraped_data/` directory
   - Has profile scraping methods
   - Uses `profile_classifier.py` to add `type` field ("waterloo" or "recruiter")
   - Needs to publish to Redis queue `profiles:scraped`

### What Needs to Change:

1. **Remove Terminal Input**:
   - Replace `input()` prompts with Redis queue consumption
   - Remove file-based input (`test_profile.json`, `test_comment.json`)
   - Make all modules work in headless/automated mode

2. **Add Redis Integration**:
   - Consume from execution queues: `playwright:post`, `playwright:message`, `playwright:comment`
   - Publish scraped data to: `profiles:scraped`
   - Handle queue polling and task execution

3. **Create Orchestrator**:
   - Main script that runs all Playwright tasks
   - Manages browser lifecycle
   - Coordinates scraping, posting, messaging, commenting

## Implementation Plan

### Phase 1: Redis Client for Playwright

**File: `patchright/redis_client.py`** (NEW)

```python
"""
Redis client for Playwright to consume and publish tasks.
"""

import redis
import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class PlaywrightRedisClient:
    """Redis client for Playwright automation."""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.client = redis.Redis(host=self.host, port=self.port, decode_responses=True)
    
    def get_post_instruction(self) -> Optional[Dict[str, Any]]:
        """Get next post instruction from queue."""
        # Blocking pop from playwright:post queue
        data = self.client.brpop("playwright:post", timeout=1)
        if data:
            _, instruction_json = data
            return json.loads(instruction_json)
        return None
    
    def get_message_instruction(self) -> Optional[Dict[str, Any]]:
        """Get next message instruction from queue."""
        # Blocking pop from playwright:message queue
        data = self.client.brpop("playwright:message", timeout=1)
        if data:
            _, instruction_json = data
            return json.loads(instruction_json)
        return None
    
    def get_comment_instruction(self) -> Optional[Dict[str, Any]]:
        """Get next comment instruction from queue."""
        # Blocking pop from playwright:comment queue
        data = self.client.brpop("playwright:comment", timeout=1)
        if data:
            _, instruction_json = data
            return json.loads(instruction_json)
        return None
    
    def publish_scraped_profile(self, profile_url: str, profile_data: Dict[str, Any]):
        """Publish scraped profile to Redis queue."""
        instruction = {
            "profile_url": profile_url,
            "profile_data": profile_data,
            "timestamp": datetime.now().isoformat()
        }
        self.client.lpush("profiles:scraped", json.dumps(instruction))
    
    def publish_scraped_post(self, post_url: str, post_data: Dict[str, Any]):
        """Publish scraped post to Redis queue."""
        instruction = {
            "post_url": post_url,
            "post_data": post_data,
            "timestamp": datetime.now().isoformat()
        }
        self.client.lpush("posts:scraped", json.dumps(instruction))
```

### Phase 2: Update Messaging Module

**File: `patchright/messaging/linkedin_messenger.py`**

**Changes:**
1. Remove `input()` prompts
2. Remove file reading (`test_profile.json`)
3. Add method to handle both `send_message` and `connect_only` actions
4. Remove manual confirmation prompts

**New Method:**
```python
def execute_message_task(self, instruction: Dict[str, Any]):
    """Execute a message task from Redis queue.
    
    Args:
        instruction: {
            "profile_url": "...",
            "name": "...",
            "message": "...",
            "action": "send_message" | "connect_only"
        }
    """
    profile_url = instruction["profile_url"]
    action = instruction.get("action", "send_message")
    
    if action == "send_message":
        message = instruction.get("message", "")
        self.send_message(profile_url, message)
    elif action == "connect_only":
        self.send_connection_request(profile_url)
```

**Changes to `send_message()`:**
- Remove `input("Press ENTER to send the message... ")`
- Remove `input("Press ENTER once sent... ")`
- Remove manual browser close prompts
- Make it fully automated

**Changes to `send_connection_request()`:**
- Remove `input("Press ENTER once profile loads... ")`
- Remove `input("Press ENTER to send connection request... ")`
- Make it fully automated

### Phase 3: Update Posting Module

**File: `patchright/posting/linkedin_poster.py`**

**Changes:**
1. Remove `input()` prompts
2. Remove terminal input for post text
3. Remove manual confirmation prompts

**Changes to `create_post()`:**
- Remove `input("Press ENTER when done...")`
- Remove `input("Press ENTER once you've confirmed your post is visible... ")`
- Remove manual browser close prompts
- Make it fully automated

**New Method:**
```python
def execute_post_task(self, instruction: Dict[str, Any]):
    """Execute a post task from Redis queue.
    
    Args:
        instruction: {
            "content": "...",
            "metadata": {...}
        }
    """
    content = instruction["content"]
    # Image path from metadata if available
    image_path = instruction.get("metadata", {}).get("image_path")
    self.create_post(text=content, image_path=image_path)
```

### Phase 4: Update Commenting Module

**File: `patchright/commenting/linkedin_commenter.py`**

**Changes:**
1. Remove `input()` prompts
2. Remove file reading (`test_comment.json`)
3. Remove manual confirmation prompts

**Changes to `post_comment()`:**
- Remove `input("Press ENTER to post the comment... ")`
- Remove `input("Press ENTER once you've confirmed your comment is visible... ")`
- Remove manual browser close prompts
- Make it fully automated

**New Method:**
```python
def execute_comment_task(self, instruction: Dict[str, Any]):
    """Execute a comment task from Redis queue.
    
    Args:
        instruction: {
            "post_url": "...",
            "comment": "..."
        }
    """
    post_url = instruction["post_url"]
    comment = instruction["comment"]
    self.post_comment(post_url, comment)
```

### Phase 5: Update Scraping Module

**File: `patchright/scraping/linkedin_scraper.py`**

**Changes:**
1. Add Redis client
2. Publish scraped profiles to `profiles:scraped` queue
3. Publish scraped posts to `posts:scraped` queue (if needed)
4. Keep file saving as backup

**New Method:**
```python
def scrape_and_publish_profile(self, profile_url: str):
    """Scrape profile and publish to Redis.
    
    Args:
        profile_url: LinkedIn profile URL
    """
    # Scrape profile (existing method)
    profile_data = self.scrape_profile(profile_url)
    
    # Classify profile (add type field)
    from profile_classifier import ProfileClassifier
    profile_data = ProfileClassifier.add_type_to_profile(profile_data)
    
    # Publish to Redis
    redis_client.publish_scraped_profile(profile_url, profile_data)
    
    # Also save to file (backup)
    self.save_profile(profile_data)
    
    return profile_data
```

### Phase 6: Create Main Orchestrator

**File: `patchright/playwright_orchestrator.py`** (NEW)

```python
"""
Main orchestrator for Playwright automation.
Consumes tasks from Redis queues and executes them.
"""

import time
import signal
import sys
from typing import Optional
from redis_client import PlaywrightRedisClient
from messaging.linkedin_messenger import LinkedInMessenger
from posting.linkedin_poster import LinkedInPoster
from commenting.linkedin_commenter import LinkedInCommenter
from scraping.linkedin_scraper import LinkedInScraper

class PlaywrightOrchestrator:
    """Orchestrates all Playwright tasks."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.redis_client = PlaywrightRedisClient()
        self.messenger = None
        self.poster = None
        self.commenter = None
        self.scraper = None
        self.running = False
    
    def start(self):
        """Start browser and initialize modules."""
        print("🚀 Starting Playwright Orchestrator...")
        
        # Initialize all modules with shared browser context
        # (They can share the same browser session)
        self.messenger = LinkedInMessenger(headless=self.headless)
        self.messenger.start()
        self.messenger.login(manual=True)  # Login once
        
        # Reuse browser context for other modules
        self.poster = LinkedInPoster(headless=self.headless)
        self.poster.context = self.messenger.context
        self.poster.page = self.messenger.page
        
        self.commenter = LinkedInCommenter(headless=self.headless)
        self.commenter.context = self.messenger.context
        self.commenter.page = self.messenger.page
        
        self.scraper = LinkedInScraper(headless=self.headless)
        self.scraper.context = self.messenger.context
        self.scraper.page = self.messenger.page
        
        self.running = True
        print("✅ Orchestrator started")
    
    def run(self):
        """Main loop: consume tasks from Redis and execute."""
        print("🔄 Starting main loop...")
        
        while self.running:
            try:
                # Check for post tasks
                post_task = self.redis_client.get_post_instruction()
                if post_task:
                    print(f"📝 Executing post task...")
                    self.poster.execute_post_task(post_task)
                
                # Check for message tasks
                message_task = self.redis_client.get_message_instruction()
                if message_task:
                    print(f"💬 Executing message task...")
                    self.messenger.execute_message_task(message_task)
                
                # Check for comment tasks
                comment_task = self.redis_client.get_comment_instruction()
                if comment_task:
                    print(f"💭 Executing comment task...")
                    self.commenter.execute_comment_task(comment_task)
                
                # Small delay to prevent busy waiting
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n⚠️  Interrupted by user")
                self.stop()
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop orchestrator and close browser."""
        self.running = False
        if self.messenger:
            self.messenger.close()
        print("👋 Orchestrator stopped")

def main():
    """Main entry point."""
    orchestrator = PlaywrightOrchestrator(headless=False)
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\n⚠️  Received signal, stopping...")
        orchestrator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        orchestrator.start()
        orchestrator.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        orchestrator.stop()

if __name__ == "__main__":
    main()
```

## Data Flow

### 1. Scraping Flow:
```
Playwright Scraper
  ↓
Scrape Profile
  ↓
Classify Profile (add type field)
  ↓
Publish to Redis: profiles:scraped
  ↓
Backend Agents consume and process
```

### 2. Execution Flow:
```
Backend Agents
  ↓
Approve Task
  ↓
Publish to Redis: playwright:post, playwright:message, playwright:comment
  ↓
Playwright Orchestrator consumes
  ↓
Execute Task (post/message/comment)
```

## Queue Formats

### Input Queues (Playwright Consumes):

**`playwright:post`:**
```json
{
  "action": "publish_post",
  "content": "Post text...",
  "metadata": {...},
  "timestamp": "..."
}
```

**`playwright:message`:**
```json
{
  "profile_url": "https://linkedin.com/in/...",
  "name": "Person Name",
  "message": "Message text",
  "action": "send_message" | "connect_only",
  "timestamp": "..."
}
```

**`playwright:comment`:**
```json
{
  "post_url": "https://linkedin.com/feed/update/...",
  "comment": "Comment text",
  "timestamp": "..."
}
```

### Output Queues (Playwright Publishes):

**`profiles:scraped`:**
```json
{
  "profile_url": "https://linkedin.com/in/...",
  "profile_data": {
    "name": "...",
    "headline": "...",
    "bio": "...",
    "experience": [...],
    "education": [...],
    "type": "waterloo" | "recruiter" | "other"
  },
  "timestamp": "..."
}
```

**`posts:scraped`** (if needed):
```json
{
  "post_url": "https://linkedin.com/feed/update/...",
  "post_data": {
    "body": "...",
    "author": "...",
    "engagement": "..."
  },
  "timestamp": "..."
}
```

## Implementation Steps

1. ✅ Create Redis client for Playwright
2. ✅ Update messaging module (remove input prompts)
3. ✅ Update posting module (remove input prompts)
4. ✅ Update commenting module (remove input prompts)
5. ✅ Update scraping module (publish to Redis)
6. ✅ Create main orchestrator
7. ✅ Test end-to-end flow

## Testing Strategy

1. **Unit Tests:**
   - Test Redis client methods
   - Test task execution methods
   - Test profile scraping and publishing

2. **Integration Tests:**
   - Test full flow: scrape → publish → agent processes → approve → execute
   - Test all task types: post, message, comment
   - Test error handling and retries

3. **End-to-End Tests:**
   - Start orchestrator
   - Generate tasks from backend
   - Verify execution
   - Check Redis queues

## Error Handling

1. **Redis Connection Errors:**
   - Retry with exponential backoff
   - Log errors and continue

2. **Task Execution Errors:**
   - Log error and continue to next task
   - Don't crash orchestrator
   - Optionally publish failed tasks to error queue

3. **Browser Errors:**
   - Restart browser if needed
   - Handle LinkedIn rate limits
   - Add delays between tasks

## Next Steps

1. Implement Redis client
2. Update each module one by one
3. Create orchestrator
4. Test with real tasks
5. Add error handling and logging


