# Playwright-Redis Integration

## Overview

Playwright modules now integrate with Redis queues to receive tasks from backend agents and publish scraped data.

## Setup

### 1. Install Dependencies

```bash
cd patchright
pip install -r requirements.txt
```

### 2. Start Redis

```bash
docker run -d -p 6379:6379 redis:alpine
```

### 3. Configure Environment Variables

Create a `.env` file in the `patchright/` directory (or use the one in the root):

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Usage

### Run Orchestrator

The orchestrator consumes tasks from Redis queues and executes them:

```bash
cd patchright
python3 playwright_orchestrator.py
```

Options:
- `--headless`: Run browser in headless mode
- `--user-data-dir`: Browser data directory (default: `./browser_data`)

### First Run

1. Start the orchestrator
2. Log in to LinkedIn manually when prompted
3. The orchestrator will wait for tasks from Redis queues

## Queue Formats

### Input Queues (Playwright Consumes)

**`playwright:post`:**
```json
{
  "action": "publish_post",
  "content": "Post text...",
  "metadata": {
    "image_path": "/path/to/image.png"  // Optional
  },
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

### Output Queues (Playwright Publishes)

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

## Module Changes

### Messaging (`messaging/linkedin_messenger.py`)

**Changes:**
- ✅ Removed all `input()` prompts
- ✅ Removed file-based input (`test_profile.json`)
- ✅ Added `execute_message_task()` method
- ✅ Fully automated execution

**New Method:**
```python
messenger.execute_message_task({
    "profile_url": "...",
    "name": "...",
    "message": "...",
    "action": "send_message" | "connect_only"
})
```

### Posting (`posting/linkedin_poster.py`)

**Changes:**
- ✅ Removed all `input()` prompts
- ✅ Removed terminal input
- ✅ Added `execute_post_task()` method
- ✅ Fully automated execution

**New Method:**
```python
poster.execute_post_task({
    "content": "Post text...",
    "metadata": {"image_path": "..."}  # Optional
})
```

### Commenting (`commenting/linkedin_commenter.py`)

**Changes:**
- ✅ Removed all `input()` prompts
- ✅ Removed file-based input (`test_comment.json`)
- ✅ Added `execute_comment_task()` method
- ✅ Fully automated execution

**New Method:**
```python
commenter.execute_comment_task({
    "post_url": "...",
    "comment": "Comment text..."
})
```

### Scraping (`scraping/linkedin_scraper.py`)

**Changes:**
- ✅ Added Redis client integration
- ✅ Publishes scraped profiles to `profiles:scraped` queue
- ✅ Classifies profiles and adds `type` field
- ✅ Still saves to files as backup

**Automatic Publishing:**
When a profile is scraped, it's automatically:
1. Classified (waterloo/recruiter/other)
2. Published to Redis queue `profiles:scraped`
3. Saved to file (backup)

## Workflow

### Complete Flow

1. **Scraping:**
   - Playwright scraper scrapes profiles from LinkedIn feed
   - Classifies profiles (waterloo/recruiter/other)
   - Publishes to Redis: `profiles:scraped`

2. **Backend Processing:**
   - Backend agents consume from `profiles:scraped`
   - Agents generate tasks (posts, messages, comments)
   - Tasks queued for frontend approval

3. **Frontend Approval:**
   - Frontend displays tasks
   - User approves/rejects/edits tasks
   - Approved tasks published to execution queues

4. **Execution:**
   - Playwright orchestrator consumes from execution queues
   - Executes tasks (post/message/comment)
   - Tasks completed automatically

## Error Handling

- **Redis Connection Errors**: Orchestrator will fail to start if Redis is not available
- **Task Execution Errors**: Errors are logged and orchestrator continues to next task
- **Browser Errors**: Browser is restarted if needed (manual intervention may be required)

## Testing

### Test Redis Connection

```python
from redis_client import PlaywrightRedisClient
client = PlaywrightRedisClient()
print(f"Connected: {client.is_connected()}")
```

### Test Task Execution

1. Start orchestrator
2. Publish a test task to Redis queue
3. Watch orchestrator consume and execute task

### Test Scraping and Publishing

```python
from scraping.linkedin_scraper import LinkedInScraper

with LinkedInScraper() as scraper:
    scraper.login(manual=True)
    profile_data = scraper.scrape_profile("https://linkedin.com/in/...")
    # Profile is automatically published to Redis
```

## Troubleshooting

### Redis Connection Failed

```
❌ Failed to connect to Redis: ...
```

**Solution:**
- Make sure Redis is running: `docker run -d -p 6379:6379 redis:alpine`
- Check Redis host/port in `.env` file

### Browser Not Starting

```
❌ Failed to start browser
```

**Solution:**
- Make sure Patchright is installed: `pip install patchright`
- Install Chrome: `patchright install chrome`

### Tasks Not Executing

**Check:**
1. Redis is running
2. Tasks are in Redis queues
3. Orchestrator is running and connected to Redis
4. Browser is logged in to LinkedIn

### Profile Not Published to Redis

**Check:**
1. Redis client is available
2. Profile scraping succeeded (no errors)
3. Profile has required fields (name, type, etc.)

## Next Steps

1. **Run Orchestrator**: Start the orchestrator to process tasks
2. **Start Backend**: Start backend to generate tasks
3. **Start Frontend**: Start frontend to approve tasks
4. **Test End-to-End**: Test complete workflow

## Files

- `redis_client.py` - Redis client for Playwright
- `playwright_orchestrator.py` - Main orchestrator
- `messaging/linkedin_messenger.py` - Updated messaging module
- `posting/linkedin_poster.py` - Updated posting module
- `commenting/linkedin_commenter.py` - Updated commenting module
- `scraping/linkedin_scraper.py` - Updated scraping module


