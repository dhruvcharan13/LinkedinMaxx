# Playwright ↔ Backend Agent Integration Guide

## Overview

This document explains how to integrate your Playwright scraping code with the LinkedInMaxx backend agents. The communication happens through **Redis queues**.

## Architecture

```
┌─────────────────┐
│   Playwright    │
│   (Scraping)    │
└────────┬────────┘
         │
         │ 1. Publish scraped profiles
         ▼
┌─────────────────────────────────────┐
│         Redis Queues                │
│  • profiles:scraped (INPUT)         │
│  • playwright:post (OUTPUT)         │
│  • playwright:message (OUTPUT)      │
└────────┬────────────────────────────┘
         │
         │ 2. Agents process profiles
         │ 3. Publish instructions
         ▼
┌─────────────────┐
│  Python Backend │
│  (Agents)       │
└─────────────────┘
```

## Redis Queues

### 1. Input Queue: `profiles:scraped`

**Purpose:** Playwright publishes scraped profile data here for agents to process.

**Format:**
```json
{
  "task_id": "profiles:scraped:2025-11-08T16:47:09.871850",
  "queue": "profiles:scraped",
  "instruction": {
    "action": "process_profile",
    "profile_url": "https://www.linkedin.com/in/elrich-chen/",
    "profile_data": {
      "url": "https://www.linkedin.com/in/elrich-chen/",
      "scraped_at": "2025-11-08T16:47:09.871850",
      "name": "Elrich Chen",
      "headline": "CS @ UWaterloo | AI automations...",
      "location": "He/Him",
      "bio": "...",
      "experience": [
        {
          "title": "AI automation",
          "company": "DoneMaker",
          "location": "Internship"
        }
      ],
      "education": [
        {
          "school": "University of Waterloo",
          "degree": "CS"
        }
      ]
    },
    "timestamp": "2025-11-08T16:47:09.871850"
  },
  "status": "pending"
}
```

**Playwright Code (Python):**
```python
import redis
import json
from datetime import datetime

# Connect to Redis
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def publish_scraped_profile(profile_data):
    """Publish scraped profile to Redis queue."""
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

# Example usage after scraping
scraped_profile = {
    "url": "https://www.linkedin.com/in/elrich-chen/",
    "scraped_at": datetime.now().isoformat(),
    "name": "Elrich Chen",
    "headline": "CS @ UWaterloo...",
    "bio": "...",
    "experience": [...],
    "education": [...]
}

publish_scraped_profile(scraped_profile)
```

**Playwright Code (Node.js/TypeScript):**
```typescript
import Redis from 'ioredis';
import { DateTime } from 'luxon';

const redis = new Redis({
  host: 'localhost',
  port: 6379,
  db: 0,
});

async function publishScrapedProfile(profileData: any) {
  const queueName = 'profiles:scraped';
  const taskId = `${queueName}:${DateTime.now().toISO()}`;
  
  const instruction = {
    task_id: taskId,
    queue: queueName,
    instruction: {
      action: 'process_profile',
      profile_url: profileData.url,
      profile_data: profileData,
      timestamp: DateTime.now().toISO(),
    },
    status: 'pending',
  };
  
  await redis.lpush(queueName, JSON.stringify(instruction));
  console.log(`✅ Published profile to queue: ${profileData.url}`);
  
  return taskId;
}
```

---

### 2. Output Queue: `playwright:post`

**Purpose:** Backend agents publish post instructions here for Playwright to execute.

**Format:**
```json
{
  "task_id": "playwright:post:2025-11-08T16:54:07.029355",
  "queue": "playwright:post",
  "instruction": {
    "action": "publish_post",
    "content": "Just finished building an AI agent system...",
    "metadata": {
      "generated_at": "2025-11-08T16:54:07.029355",
      "model": "gemini-pro",
      "agent": "daily_post_agent"
    },
    "timestamp": "2025-11-08T16:54:07.029355"
  },
  "status": "pending"
}
```

**Playwright Code (Python):**
```python
def consume_post_instructions():
    """Consume post instructions from Redis queue."""
    queue_name = "playwright:post"
    
    while True:
        # Blocking pop (waits for new instructions)
        result = redis_client.brpop(queue_name, timeout=5)
        
        if result:
            _, data = result
            instruction = json.loads(data)
            
            # Execute the post
            post_content = instruction["instruction"]["content"]
            print(f"📝 Publishing post: {post_content[:100]}...")
            
            # Your Playwright code to publish the post
            # await page.fill('[data-testid="post-input"]', post_content)
            # await page.click('[data-testid="post-submit"]')
            
            print(f"✅ Post published: {instruction['task_id']}")
```

**Playwright Code (Node.js/TypeScript):**
```typescript
async function consumePostInstructions() {
  const queueName = 'playwright:post';
  
  while (true) {
    const result = await redis.brpop(queueName, 5); // 5 second timeout
    
    if (result) {
      const instruction = JSON.parse(result[1]);
      const postContent = instruction.instruction.content;
      
      console.log(`📝 Publishing post: ${postContent.substring(0, 100)}...`);
      
      // Your Playwright code to publish the post
      // await page.fill('[data-testid="post-input"]', postContent);
      // await page.click('[data-testid="post-submit"]');
      
      console.log(`✅ Post published: ${instruction.task_id}`);
    }
  }
}
```

---

### 3. Output Queue: `playwright:message`

**Purpose:** Backend agents publish message/connection instructions here for Playwright to execute.

**Format:**
```json
{
  "task_id": "playwright:message:2025-11-08T16:54:07.771611",
  "queue": "playwright:message",
  "instruction": {
    "action": "send_message",  // or "connect_only"
    "profile_url": "https://www.linkedin.com/in/elrich-chen/",
    "message": "Hey Elrich! Saw you're in 2A too...",  // Empty if connect_only
    "timestamp": "2025-11-08T16:54:07.771611"
  },
  "status": "pending"
}
```

**Actions:**
- `send_message`: Send a connection request WITH a message
- `connect_only`: Send a connection request WITHOUT a message

**Playwright Code (Python):**
```python
def consume_message_instructions():
    """Consume message/connection instructions from Redis queue."""
    queue_name = "playwright:message"
    
    while True:
        # Blocking pop (waits for new instructions)
        result = redis_client.brpop(queue_name, timeout=5)
        
        if result:
            _, data = result
            instruction = json.loads(data)
            inst = instruction["instruction"]
            
            profile_url = inst["profile_url"]
            action = inst["action"]
            message = inst.get("message", "")
            
            print(f"📨 Processing: {action} for {profile_url}")
            
            # Navigate to profile
            # await page.goto(profile_url)
            
            if action == "send_message":
                # Click "Connect" button
                # await page.click('[data-testid="connect-button"]')
                # Wait for message modal
                # await page.fill('[data-testid="message-input"]', message)
                # await page.click('[data-testid="send-button"]')
                print(f"✅ Sent message: {message[:50]}...")
            elif action == "connect_only":
                # Click "Connect" button (no message)
                # await page.click('[data-testid="connect-button"]')
                # Click "Send without a message" or "Connect"
                print(f"✅ Sent connection request (no message)")
            
            print(f"✅ Completed: {instruction['task_id']}")
```

**Playwright Code (Node.js/TypeScript):**
```typescript
async function consumeMessageInstructions() {
  const queueName = 'playwright:message';
  
  while (true) {
    const result = await redis.brpop(queueName, 5);
    
    if (result) {
      const instruction = JSON.parse(result[1]);
      const inst = instruction.instruction;
      
      const profileUrl = inst.profile_url;
      const action = inst.action;
      const message = inst.message || '';
      
      console.log(`📨 Processing: ${action} for ${profileUrl}`);
      
      // Navigate to profile
      // await page.goto(profileUrl);
      
      if (action === 'send_message') {
        // Click "Connect" and send message
        // await page.click('[data-testid="connect-button"]');
        // await page.fill('[data-testid="message-input"]', message);
        // await page.click('[data-testid="send-button"]');
        console.log(`✅ Sent message: ${message.substring(0, 50)}...`);
      } else if (action === 'connect_only') {
        // Click "Connect" without message
        // await page.click('[data-testid="connect-button"]');
        console.log(`✅ Sent connection request (no message)`);
      }
      
      console.log(`✅ Completed: ${instruction.task_id}`);
    }
  }
}
```

---

## Complete Playwright Integration Example

### Python Example

```python
import redis
import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

async def scrape_linkedin_feed(page):
    """Scrape LinkedIn feed and extract profile URLs."""
    # Your scraping logic here
    profile_urls = []
    
    # Example: Scroll and collect profile URLs
    # await page.goto("https://www.linkedin.com/feed/")
    # ... your scraping code ...
    
    return profile_urls

async def scrape_profile(page, profile_url):
    """Scrape a single profile."""
    # Your profile scraping logic
    profile_data = {
        "url": profile_url,
        "scraped_at": datetime.now().isoformat(),
        "name": "...",
        "headline": "...",
        "bio": "...",
        "experience": [...],
        "education": [...]
    }
    
    return profile_data

def publish_profile(profile_data):
    """Publish scraped profile to Redis."""
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
    
    redis_client.lpush(queue_name, json.dumps(instruction))
    print(f"✅ Published: {profile_data['url']}")

async def consume_post_instructions(page):
    """Consume and execute post instructions."""
    queue_name = "playwright:post"
    
    while True:
        result = redis_client.brpop(queue_name, timeout=5)
        if result:
            _, data = result
            instruction = json.loads(data)
            content = instruction["instruction"]["content"]
            
            # Execute post
            # await page.goto("https://www.linkedin.com/feed/")
            # await page.fill('[data-testid="post-input"]', content)
            # await page.click('[data-testid="post-submit"]')
            
            print(f"✅ Post published: {instruction['task_id']}")

async def consume_message_instructions(page):
    """Consume and execute message instructions."""
    queue_name = "playwright:message"
    
    while True:
        result = redis_client.brpop(queue_name, timeout=5)
        if result:
            _, data = result
            instruction = json.loads(data)
            inst = instruction["instruction"]
            
            # Execute message/connection
            # await page.goto(inst["profile_url"])
            # ... your connection/message logic ...
            
            print(f"✅ Message processed: {instruction['task_id']}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Login to LinkedIn
        # await page.goto("https://www.linkedin.com/login")
        # ... login logic ...
        
        # Start consumers in background
        asyncio.create_task(consume_post_instructions(page))
        asyncio.create_task(consume_message_instructions(page))
        
        # Scrape feed and publish profiles
        while True:
            profile_urls = await scrape_linkedin_feed(page)
            
            for url in profile_urls:
                profile_data = await scrape_profile(page, url)
                publish_profile(profile_data)
            
            await asyncio.sleep(10)  # Wait before next scrape

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Integration Checklist

- [ ] Install Redis client library (Python: `redis`, Node.js: `ioredis`)
- [ ] Connect to Redis (localhost:6379)
- [ ] Publish scraped profiles to `profiles:scraped` queue
- [ ] Consume from `playwright:post` queue and execute posts
- [ ] Consume from `playwright:message` queue and execute connections/messages
- [ ] Handle errors gracefully
- [ ] Add logging for debugging

---

## Testing

### Test Profile Publishing

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Test profile
test_profile = {
    "url": "https://www.linkedin.com/in/test/",
    "name": "Test User",
    "headline": "Test Headline",
    "bio": "Test bio",
    "experience": [],
    "education": []
}

# Publish to queue
redis_client.lpush("profiles:scraped", json.dumps({
    "task_id": "test-123",
    "queue": "profiles:scraped",
    "instruction": {
        "action": "process_profile",
        "profile_url": test_profile["url"],
        "profile_data": test_profile,
        "timestamp": "2025-11-08T12:00:00"
    },
    "status": "pending"
}))

print("✅ Test profile published!")
```

### Check Queue Status

```python
# Check queue length
post_queue_length = redis_client.llen("playwright:post")
message_queue_length = redis_client.llen("playwright:message")
profiles_queue_length = redis_client.llen("profiles:scraped")

print(f"Post queue: {post_queue_length}")
print(f"Message queue: {message_queue_length}")
print(f"Profiles queue: {profiles_queue_length}")
```

---

## Key Points

1. **Redis is the communication layer** - All data flows through Redis queues
2. **Playwright publishes profiles** - Scraped data goes to `profiles:scraped`
3. **Playwright consumes instructions** - Reads from `playwright:post` and `playwright:message`
4. **Backend agents process automatically** - They consume from `profiles:scraped` and publish instructions
5. **Terminal feedback** - Backend shows all actions in real-time

---

## Next Steps

1. Set up Redis connection in your Playwright code
2. Implement profile publishing function
3. Implement instruction consumption functions
4. Test with a single profile
5. Integrate with your scraping loop

---

## Support

- Check backend terminal for agent actions and data flow
- Use `redis-cli` to inspect queues: `redis-cli LLEN profiles:scraped`
- Check backend logs for errors
- Use the test script: `python3 test_profile_data.py`

