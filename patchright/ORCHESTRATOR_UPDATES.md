# Orchestrator Updates

## Changes Made

### 1. Post Generation on Startup ✅
- Orchestrator now triggers post generation when it starts
- Calls `/api/generate-daily-post` endpoint on backend
- Post is queued for frontend approval
- Once approved, it appears in `playwright:post` queue for execution

### 2. Browser Stays Open ✅
- All tasks (post, message, comment) now return to feed but keep browser open
- No closing/reopening of tabs between tasks
- Browser context persists throughout orchestrator lifecycle
- Browser only closes when orchestrator is stopped (and even then, it's optional)

### 3. Profile Scraper Integration ✅
- `find_profiles.py` uses `scraper.scrape_profile()` which automatically:
  - Classifies profiles (waterloo/recruiter/other)
  - Publishes to Redis `profiles:scraped` queue
  - Saves to files as backup
- No additional changes needed - it's already integrated!

## Workflow

### On Orchestrator Startup:
1. Browser opens
2. User logs in to LinkedIn
3. Orchestrator triggers post generation via API
4. Post agent generates post
5. Post queued for frontend approval
6. User approves/rejects/edits in frontend
7. Approved post published to `playwright:post` queue
8. Orchestrator consumes and executes

### During Execution:
1. Orchestrator consumes tasks from Redis queues
2. Executes task (post/message/comment)
3. Returns to feed (same tab, browser stays open)
4. Waits for next task
5. Repeats

### Profile Scraping:
1. `find_profiles.py` scrapes profiles
2. `scrape_profile()` automatically:
   - Classifies profile
   - Publishes to Redis `profiles:scraped`
   - Saves to file
3. Backend agents consume from `profiles:scraped`
4. Generate tasks → Frontend approval → Execution

## Key Points

- **Browser Persistence**: Browser stays open throughout, no closing/reopening
- **Post Generation**: Triggered automatically on startup
- **Profile Publishing**: Automatic via `scrape_profile()` method
- **Task Flow**: Backend → Frontend Approval → Redis Queue → Playwright Execution

