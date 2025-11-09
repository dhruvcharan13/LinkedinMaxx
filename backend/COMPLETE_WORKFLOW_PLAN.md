# Complete Workflow Plan - LinkedInMaxx

## Current State

### ✅ What's Working
1. **Backend Agents**: All agents working with Gemini Flash
   - Daily Post Agent ✅
   - Messaging Agent ✅
   - Dating Agent ✅
2. **Redis Communication**: Publishing/consuming working ✅
3. **Patchright Functionality**:
   - Posting ✅ (can create posts)
   - Scraping ✅ (can scroll, collect profile URLs, classify)
   - Messaging ✅ (can send messages/connection requests)
   - **Commenting ❌** (needs to be built)

## Desired Workflow

### Full Automation Flow

```
1. START
   ↓
2. Click "Start a post" button
   ↓
3. Publish daily post (from Daily Post Agent via Redis)
   ↓
4. Start scraping LinkedIn feed
   ↓
5. Collect profile URLs and post URLs from home screen
   ↓
6. Queue profile URLs → profiles:scrape_queue
   ↓
7. Queue post URLs → posts:scrape_queue
   ↓
8. Process queue (parallel or sequential):
   ├─→ Scrape profile → Publish to profiles:scraped → Agent processes → playwright:message
   └─→ Scrape post → Publish to posts:scraped → Agent processes → playwright:comment
   ↓
9. Patchright consumes instructions:
   ├─→ playwright:message → Send message/connect
   └─→ playwright:comment → Comment on post
   ↓
10. Loop back to step 4 (continue scraping)
```

## Implementation Plan

### Phase 1: Commenting Functionality

**File:** `patchright/commenting/linkedin_commenter.py` (NEW)

```python
class LinkedInCommenter:
    """Comment on LinkedIn posts."""
    
    def comment_on_post(self, post_url: str, comment_text: str):
        """
        Comment on a LinkedIn post.
        
        Workflow:
        1. Navigate to post URL
        2. Find comment input
        3. Type comment (human-like)
        4. Submit comment
        """
        # Navigate to post
        # Find comment box
        # Type comment
        # Submit
```

**Integration:**
- Add to Redis consumption loop
- Consume from `playwright:comment` queue
- Execute comments

### Phase 2: Post Scraping & Agent Processing

**New Agent:** `CommentAgent` (or extend MessagingAgent)

```python
class CommentAgent:
    """Decides whether to comment on posts and generates comments."""
    
    def should_comment(self, post_data: Dict) -> bool:
        """Decide if we should comment on this post."""
        # Check if post is relevant
        # Check if we've already commented
        # Return True/False
    
    def generate_comment(self, post_data: Dict) -> str:
        """Generate a comment for the post."""
        # Use LLM to generate relevant comment
        # Return comment text
```

**New Queue:** `posts:scraped`
- Patchright publishes post data here
- Backend consumes and processes
- Agent decides: comment or skip
- Publishes to `playwright:comment` if yes

### Phase 3: Orchestration

**Main Orchestrator:** `patchright/orchestrator.py` (NEW)

```python
class LinkedInOrchestrator:
    """Main orchestrator for full automation."""
    
    def run_full_workflow(self):
        """Run the complete workflow."""
        # 1. Post daily post
        # 2. Start scraping feed
        # 3. Collect URLs
        # 4. Queue for scraping
        # 5. Process queues
        # 6. Consume instructions
        # 7. Execute actions
        # 8. Loop
```

## Demo Strategy

### Problem
- Judges approach unpredictably
- Home feed is unpredictable
- Need reliable demo

### Solution Options

#### Option 1: Pre-Queue URLs (Your Idea) ✅ RECOMMENDED
**Pros:**
- Predictable demo
- Can test with known profiles/posts
- Reliable execution
- Can show full flow

**Implementation:**
```python
# Pre-queue file: patchright/demo_queue.json
{
    "profiles": [
        {"url": "https://linkedin.com/in/friend1", "type": "waterloo"},
        {"url": "https://linkedin.com/in/friend2", "type": "recruiter"}
    ],
    "posts": [
        {"url": "https://linkedin.com/feed/update/...", "author": "..."}
    ]
}

# Load and queue at start
orchestrator.preload_demo_queue("demo_queue.json")
```

#### Option 2: Hybrid Mode
- Start with pre-queued URLs
- Then switch to live scraping
- Best of both worlds

#### Option 3: Recorded Demo
- Pre-record video
- Show during demo
- Less impressive but reliable

### Recommendation: **Option 1 + Option 2**

**For Demo:**
1. Pre-queue 5-10 known profiles/posts
2. Show full automation flow
3. Can switch to live scraping if time permits

**Benefits:**
- Reliable demo
- Shows all features
- Can explain the system
- Can switch to live if needed

## Detailed Workflow

### Step-by-Step Implementation

#### 1. Daily Post (Already Working)
```
Backend generates post → Redis: playwright:post → Patchright consumes → Posts
```

#### 2. Feed Scraping (Already Working)
```
Patchright scrolls feed → Collects profile URLs + post URLs
```

#### 3. URL Queuing (NEW)
```python
# In Patchright
profile_urls = scraper.get_profile_urls_from_feed()
post_urls = scraper.get_post_urls_from_feed()

# Queue them
for url in profile_urls:
    redis_client.lpush("profiles:scrape_queue", json.dumps({
        "url": url,
        "type": "profile",
        "timestamp": datetime.now().isoformat()
    }))

for url in post_urls:
    redis_client.lpush("posts:scrape_queue", json.dumps({
        "url": url,
        "type": "post",
        "timestamp": datetime.now().isoformat()
    }))
```

#### 4. Profile Scraping Loop (NEW)
```python
# In Patchright
while True:
    # Get next profile URL to scrape
    profile_task = redis_client.brpop("profiles:scrape_queue", timeout=1)
    if profile_task:
        _, data = json.loads(profile_task[1])
        profile_url = data["url"]
        
        # Scrape profile
        profile_data = scraper.scrape_profile(profile_url)
        
        # Classify (already done in scraper)
        profile_data["type"] = classifier.classify(profile_data)
        
        # Publish to profiles:scraped
        redis_client.queue_profile_for_processing(profile_url, profile_data)
```

#### 5. Post Scraping Loop (NEW)
```python
# In Patchright
while True:
    # Get next post URL to scrape
    post_task = redis_client.brpop("posts:scrape_queue", timeout=1)
    if post_task:
        _, data = json.loads(post_task[1])
        post_url = data["url"]
        
        # Scrape post
        post_data = scraper.scrape_post(post_url)  # NEW METHOD
        
        # Publish to posts:scraped
        redis_client.lpush("posts:scraped", json.dumps({
            "task_id": f"posts:scraped:{datetime.now().isoformat()}",
            "queue": "posts:scraped",
            "instruction": {
                "action": "process_post",
                "post_url": post_url,
                "post_data": post_data,
                "timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }))
```

#### 6. Post Processing Agent (NEW)
```python
# In Backend
class PostCommentAgent:
    """Decides whether to comment on posts."""
    
    def process_post(self, post_url: str, post_data: Dict) -> Dict:
        """Process a post and decide if we should comment."""
        # Analyze post content
        # Decide: comment or skip
        # Generate comment if yes
        # Publish to playwright:comment
```

#### 7. Comment Execution (NEW)
```python
# In Patchright
comment_instruction = redis_client.brpop("playwright:comment", timeout=1)
if comment_instruction:
    _, data = json.loads(comment_instruction[1])
    instruction = data["instruction"]
    
    commenter.comment_on_post(
        instruction["post_url"],
        instruction["comment_text"]
    )
```

## Redis Queue Structure

### New Queues Needed

1. **`profiles:scrape_queue`** - Profile URLs waiting to be scraped
2. **`posts:scrape_queue`** - Post URLs waiting to be scraped
3. **`posts:scraped`** - Scraped post data for agent processing
4. **`playwright:comment`** - Comment instructions for Patchright

### Queue Flow

```
Feed Scraping
  ↓
profiles:scrape_queue (URLs to scrape)
  ↓
Profile Scraping
  ↓
profiles:scraped (scraped data)
  ↓
Agent Processing
  ↓
playwright:message (instructions)

Feed Scraping
  ↓
posts:scrape_queue (URLs to scrape)
  ↓
Post Scraping
  ↓
posts:scraped (scraped data)
  ↓
Comment Agent Processing
  ↓
playwright:comment (instructions)
```

## Demo Queue Format

**File:** `patchright/demo_queue.json`

```json
{
    "profiles": [
        {
            "url": "https://linkedin.com/in/friend1",
            "type": "waterloo",
            "name": "Friend 1",
            "note": "Known Waterloo student for demo"
        },
        {
            "url": "https://linkedin.com/in/recruiter1",
            "type": "recruiter",
            "name": "Recruiter 1",
            "note": "Known recruiter for demo"
        }
    ],
    "posts": [
        {
            "url": "https://linkedin.com/feed/update/...",
            "author": "Friend 2",
            "note": "Known post for demo commenting"
        }
    ]
}
```

## Implementation Priority

### Must Have (For Demo)
1. ✅ Commenting functionality
2. ✅ Post scraping
3. ✅ Comment agent
4. ✅ Demo queue system
5. ✅ Orchestration loop

### Nice to Have
1. Parallel scraping (multiple profiles at once)
2. Rate limiting
3. Error recovery
4. Progress tracking

## Next Steps

1. **Build commenting module** (`patchright/commenting/`)
2. **Build post scraping** (extend `linkedin_scraper.py`)
3. **Build comment agent** (`backend/agents/comment_agent.py`)
4. **Build orchestration** (`patchright/orchestrator.py`)
5. **Build demo queue loader**
6. **Test end-to-end**

## Questions to Answer

1. **Commenting strategy**: When should we comment?
   - On all posts? (spam risk)
   - Only relevant posts? (need agent logic)
   - Only posts from connections? (safer)

2. **Post scraping**: What data do we need?
   - Post text
   - Author info
   - Engagement metrics
   - Comments already there

3. **Rate limiting**: How fast should we go?
   - LinkedIn has limits
   - Need to be human-like
   - Demo vs production speeds

4. **Error handling**: What if something fails?
   - Retry logic
   - Skip and continue
   - Log errors

