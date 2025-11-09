# Complete Workflow Walkthrough - LinkedInMaxx

## Overview

This document walks through the complete workflow of LinkedInMaxx, from startup to execution, listing every file that gets involved at each step.

---

## Workflow Steps

### 1. System Startup

**Entry Point:** `backend/main.py`

**Files Involved:**
- `backend/main.py` - Main FastAPI server
- `backend/.env` - Environment variables (API keys, Redis config, USER_STREAM)
- `backend/utils/logger.py` - Rich terminal logging
- `backend/utils/redis_client.py` - Redis connection
- `backend/agents/daily_post_agent.py` - Daily Post Agent initialization
- `backend/agents/messaging_agent.py` - Messaging Agent initialization
- `backend/agents/dating_agent.py` - Dating Agent initialization
- `backend/agents/comment_agent.py` - Comment Agent initialization
- `backend/data/waterloo_streams.json` - Stream data for Dating Agent

**Process:**
1. Loads environment variables from `.env`
2. Initializes Redis client (connects to Redis server)
3. Initializes all agents (Daily Post, Messaging, Dating, Comment)
4. Starts FastAPI server on port 8000 (or BACKEND_PORT)
5. Agents set up LLM models (Google Gemini) and prompts

---

### 2. User Starts Workflow

**Entry Point:** `POST /api/start-scrolling` (FastAPI endpoint in `backend/main.py`)

**Files Involved:**
- `backend/main.py` - `start_scrolling()` function
- `backend/utils/logger.py` - Logging feedback
- `backend/utils/redis_client.py` - Redis connection check

**Process:**
1. User sends POST request to `/api/start-scrolling`
2. Request includes `generate_daily_post` flag and optional `context`
3. Sets `is_running = True`
4. Starts `orchestrate_workflow()` as async task

---

### 3. Daily Post Generation (Optional)

**Entry Point:** `backend/main.py` → `orchestrate_workflow()` → Daily Post Agent

**Files Involved:**
- `backend/main.py` - `orchestrate_workflow()` function
- `backend/agents/daily_post_agent.py` - `generate_and_publish()`
- `backend/utils/redis_client.py` - `queue_post_instruction()`
- `backend/utils/logger.py` - Terminal feedback
- `.env` - GEMINI_API_KEY

**Process:**
1. If `generate_daily_post = True`, calls `daily_post_agent.generate_and_publish(context)`
2. Daily Post Agent:
   - Uses `ChatGoogleGenerativeAI` with `gemini-2.5-flash` model
   - Generates post using prompt template
   - Returns post content and metadata
3. Publishes to Redis queue `playwright:post`:
   - Format: `{action: "publish_post", content: "...", metadata: {...}}`
4. Redis stores in:
   - List: `playwright:post`
   - Hash: `playwright:post:tasks` (for retrieval)

**Output:** Post instruction in Redis queue `playwright:post`

---

### 4. Profile Processing Loop

**Entry Point:** `backend/main.py` → `orchestrate_workflow()` → Profile processing loop

**Files Involved:**
- `backend/main.py` - `orchestrate_workflow()` loop
- `backend/utils/redis_client.py` - `get_instruction("profiles:scraped")`
- `backend/agents/messaging_agent.py` - `process_profile()`
- `backend/agents/dating_agent.py` - `process_waterloo_student()`
- `backend/utils/logger.py` - Terminal feedback
- `.env` - GEMINI_API_KEY

**Process:**
1. Continuously polls Redis queue `profiles:scraped` (blocking pop, 1s timeout)
2. When profile found:
   - Extracts `profile_url` and `profile_data` from instruction
   - Checks `profile_data.type` (pre-classified by Patchright)
3. Routes based on type:
   - `"waterloo"` → Dating Agent
   - `"recruiter"` → Messaging Agent (recruiter message)
   - `"cofounder"` → Messaging Agent (co-founder message)
   - `"other"` or no type → Messaging Agent (classify with LLM)

---

### 5. Messaging Agent Processing

**Entry Point:** `backend/agents/messaging_agent.py` → `process_profile()`

**Files Involved:**
- `backend/agents/messaging_agent.py` - `process_profile()`, `classify_profile()`, `generate_recruiter_message()`, `generate_cofounder_message()`
- `backend/utils/redis_client.py` - `queue_message_instruction()`
- `backend/utils/logger.py` - Terminal feedback
- `.env` - GEMINI_API_KEY

**Process:**
1. **Classification:**
   - If `profile_data.type` exists, uses it (skip LLM)
   - Otherwise, uses LLM to classify: `recruiter`, `cofounder`, `waterloo_student`, `other`
2. **Message Generation:**
   - **Recruiter:** Generates recruiter message using LLM
   - **Co-founder:** Generates co-founder message using LLM
   - **Waterloo Student:** Routes to Dating Agent
   - **Other:** Just connect, no message
3. **Publish to Redis:**
   - Queue: `playwright:message`
   - Format: `{profile_url: "...", name: "...", message: "...", action: "send_message" | "connect_only"}`
   - Matches `patchright/messaging/test_profile.json` format

**Output:** Message instruction in Redis queue `playwright:message`

---

### 6. Dating Agent Processing

**Entry Point:** `backend/agents/dating_agent.py` → `process_waterloo_student()`

**Files Involved:**
- `backend/agents/dating_agent.py` - `process_waterloo_student()`, `estimate_stream()`, `generate_pickup_line()`, `is_same_stream()`
- `backend/data/waterloo_streams.json` - Stream data (1A, 1B, 2A, 2B, 4, 8)
- `backend/utils/redis_client.py` - `queue_message_instruction()`
- `backend/utils/logger.py` - Terminal feedback
- `.env` - GEMINI_API_KEY, USER_STREAM

**Process:**
1. **Stream Estimation:**
   - Rule-based inference first (checks education/bio for stream keywords)
   - If not found, uses LLM to estimate stream (1A, 1B, 2A, 2B, 4, 8)
2. **Stream Matching:**
   - Compares estimated stream with `USER_STREAM` (from `.env`)
   - If same stream: Generate pickup line
   - If different stream: Just connect, no message
3. **Pickup Line Generation:**
   - Uses LLM to generate pickup line based on profile and stream
   - Includes stream-specific references
4. **Publish to Redis:**
   - Queue: `playwright:message`
   - Format: `{profile_url: "...", name: "...", message: "...", action: "send_message" | "connect_only"}`
   - Matches `patchright/messaging/test_profile.json` format

**Output:** Message instruction in Redis queue `playwright:message`

---

### 7. Comment Agent Processing (For Posts)

**Entry Point:** `backend/agents/comment_agent.py` → `process_post()`

**Files Involved:**
- `backend/agents/comment_agent.py` - `process_post()`, `should_comment()`, `generate_comment()`
- `backend/utils/redis_client.py` - `queue_comment_instruction()`
- `backend/utils/logger.py` - Terminal feedback
- `.env` - GEMINI_API_KEY

**Process:**
1. **Decision:**
   - Keyword-based: Checks for tech keywords (tech, ai, software, startup, career, waterloo, etc.)
   - If keywords found and post length > 20: Comment
   - Otherwise: Skip
2. **Comment Generation:**
   - If should comment, uses LLM to generate comment
   - Comment is 1-2 sentences, professional but engaging
3. **Publish to Redis:**
   - Queue: `playwright:comment`
   - Format: `{post_url: "...", comment: "...", timestamp: "..."}`

**Output:** Comment instruction in Redis queue `playwright:comment`

**Note:** Comment agent is not yet integrated into the orchestration loop (needs post scraping first)

---

### 8. Patchright Execution (External Process)

**Entry Point:** Patchright scripts (separate process)

**Files Involved (Patchright):**
- `patchright/posting/linkedin_poster.py` - Consumes `playwright:post`
- `patchright/messaging/linkedin_messenger.py` - Consumes `playwright:message`
- `patchright/scraping/linkedin_scraper.py` - Scrapes profiles and publishes to `profiles:scraped`
- `patchright/scraping/profile_classifier.py` - Classifies profiles (waterloo, recruiter, etc.)
- `patchright/scraping/find_profiles.py` - Main scraping script
- `patchright/commenting/linkedin_commenter.py` - Consumes `playwright:comment` (TO BE BUILT)

**Process:**

#### 8a. Post Publishing
1. Patchright consumes from `playwright:post` queue
2. Uses `linkedin_poster.py` to:
   - Click "Start a post" button
   - Type post content (human-like)
   - Click "Post" button
   - Publish post to LinkedIn

#### 8b. Profile Scraping
1. Patchright scrolls LinkedIn feed
2. Collects profile URLs from posts
3. For each profile URL:
   - Scrapes profile data (bio, experience, education, name)
   - Classifies profile using `profile_classifier.py` (waterloo, recruiter, cofounder, other)
   - Adds `type` field to profile data
   - Publishes to Redis queue `profiles:scraped`
4. Format: `{action: "process_profile", profile_url: "...", profile_data: {..., type: "waterloo"}}`

#### 8c. Message Sending
1. Patchright consumes from `playwright:message` queue
2. Uses `linkedin_messenger.py` to:
   - Navigate to profile URL
   - Click "Message" button
   - Type message (human-like)
   - Click "Send" button
   - Or just connect if `action = "connect_only"`

#### 8d. Comment Posting (TO BE BUILT)
1. Patchright consumes from `playwright:comment` queue
2. Uses `linkedin_commenter.py` to:
   - Navigate to post URL
   - Find comment input
   - Type comment (human-like)
   - Submit comment

---

## Complete File List

### Backend Files

#### Core Files
1. `backend/main.py` - Main FastAPI server, orchestration logic
2. `backend/.env` - Environment variables (API keys, Redis config, USER_STREAM)
3. `backend/requirements.txt` - Python dependencies

#### Utility Files
4. `backend/utils/logger.py` - Rich terminal logging
5. `backend/utils/redis_client.py` - Redis client for queues and agent memory
6. `backend/utils/__init__.py` - Utility package init

#### Agent Files
7. `backend/agents/daily_post_agent.py` - Daily Post Agent
8. `backend/agents/messaging_agent.py` - Messaging Agent
9. `backend/agents/dating_agent.py` - Dating Agent
10. `backend/agents/comment_agent.py` - Comment Agent
11. `backend/agents/__init__.py` - Agents package init

#### Data Files
12. `backend/data/waterloo_streams.json` - Waterloo stream data (1A, 1B, 2A, 2B, 4, 8)

#### Documentation Files
13. `backend/README.md` - Backend documentation
14. `backend/COMPLETE_WORKFLOW_PLAN.md` - Workflow plan
15. `backend/DEMO_STRATEGY.md` - Demo strategy
16. `backend/AGENT_OUTPUT_FORMAT.md` - Agent output format documentation
17. `backend/COMPLETE_WORKFLOW_WALKTHROUGH.md` - This file

### Patchright Files

#### Core Files
18. `patchright/posting/linkedin_poster.py` - Post publishing
19. `patchright/messaging/linkedin_messenger.py` - Message sending
20. `patchright/scraping/linkedin_scraper.py` - Profile scraping
21. `patchright/scraping/profile_classifier.py` - Profile classification
22. `patchright/scraping/find_profiles.py` - Main scraping script
23. `patchright/commenting/linkedin_commenter.py` - Comment posting (TO BE BUILT)

#### Utility Files
24. `patchright/scraping/stealth_utils.py` - Stealth utilities
25. `patchright/stealth_utils.py` - Stealth utilities (legacy)

#### Data Files
26. `patchright/messaging/test_profile.json` - Test profile format
27. `patchright/browser_data/` - Browser session data (persistent login)

#### Documentation Files
28. `patchright/README.md` - Patchright documentation
29. `patchright/posting/README.md` - Posting documentation
30. `patchright/messaging/README.md` - Messaging documentation
31. `patchright/scraping/README.md` - Scraping documentation

---

## Redis Queues

### Queues Used

1. **`playwright:post`** - Post instructions for Patchright
   - Published by: Daily Post Agent
   - Consumed by: Patchright Posting Module

2. **`profiles:scraped`** - Scraped profiles for agent processing
   - Published by: Patchright Scraping Module
   - Consumed by: Backend Orchestration Loop

3. **`playwright:message`** - Message instructions for Patchright
   - Published by: Messaging Agent, Dating Agent
   - Consumed by: Patchright Messaging Module

4. **`playwright:comment`** - Comment instructions for Patchright
   - Published by: Comment Agent
   - Consumed by: Patchright Commenting Module (TO BE BUILT)

### Redis Storage

- **Lists:** `playwright:post`, `profiles:scraped`, `playwright:message`, `playwright:comment`
- **Hashes:** `{queue_name}:tasks` - Stores full instruction data for retrieval

---

## Data Flow Diagram

```
┌─────────────────┐
│   User/API      │
│  Start Workflow │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  main.py        │
│  orchestrate_   │
│  workflow()     │
└────────┬────────┘
         │
         ├──► Daily Post Agent ──► Redis: playwright:post ──► Patchright Poster
         │
         └──► Profile Processing Loop
              │
              ├──► Redis: profiles:scraped (from Patchright)
              │
              ├──► Messaging Agent ──► Redis: playwright:message ──► Patchright Messenger
              │
              ├──► Dating Agent ──► Redis: playwright:message ──► Patchright Messenger
              │
              └──► Comment Agent ──► Redis: playwright:comment ──► Patchright Commenter (TO BE BUILT)
```

---

## Environment Variables

### Required (`.env`)

- `GEMINI_API_KEY` - Google Gemini API key
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)
- `USER_STREAM` - User's Waterloo stream (1A, 1B, 2A, 2B, 4, 8)
- `BACKEND_PORT` - Backend port (default: 8000)

### Optional

- `REDIS_DB` - Redis database (default: 0)
- `GEMINI_MODEL` - Gemini model (default: gemini-2.5-flash)

---

## Key Integration Points

### 1. Backend → Patchright (Redis)
- Backend publishes instructions to Redis queues
- Patchright consumes from Redis queues
- Format: `{task_id, queue, instruction: {...}, timestamp, status}`

### 2. Patchright → Backend (Redis)
- Patchright publishes scraped profiles to `profiles:scraped`
- Backend consumes from `profiles:scraped`
- Format: `{action: "process_profile", profile_url: "...", profile_data: {..., type: "waterloo"}}`

### 3. Agent Output Format
- Messages: `{profile_url, name, message, action}`
- Comments: `{post_url, comment, timestamp}`
- Matches `patchright/messaging/test_profile.json` format

---

## Next Steps (To Complete Workflow)

1. **Build Commenting Module** (`patchright/commenting/linkedin_commenter.py`)
2. **Integrate Comment Agent** into orchestration loop (process posts from `posts:scraped`)
3. **Build Post Scraping** in Patchright (scrape posts, publish to `posts:scraped`)
4. **Build Orchestrator** in Patchright (coordinate posting, scraping, messaging, commenting)
5. **Test End-to-End** workflow

---

## Summary

The workflow involves:
- **Backend:** 17 files (core, utilities, agents, data, docs)
- **Patchright:** 13+ files (scraping, posting, messaging, commenting)
- **Redis:** 4 queues (post, profiles:scraped, message, comment)
- **Environment:** 1 file (`.env`)

Total: **30+ files** working together to automate LinkedIn posting, scraping, messaging, and commenting.

