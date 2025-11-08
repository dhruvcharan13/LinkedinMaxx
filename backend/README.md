# LinkedInMaxx Backend

Python backend with LangChain agents for LinkedIn automation.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY
   ```

3. **Start Redis:**
   ```bash
   brew services start redis
   ```

4. **Run the server:**
   ```bash
   python3 main.py
   ```

## Architecture

```
┌─────────────────┐
│   Patchright    │  ← Scrapes LinkedIn profiles
│   (Scraping)    │
└────────┬────────┘
         │
         │ Publish to Redis: profiles:scraped
         ▼
┌─────────────────────────────────────┐
│         Redis Queues                │
│  • profiles:scraped (INPUT)         │
│  • playwright:post (OUTPUT)         │
│  • playwright:message (OUTPUT)      │
└────────┬────────────────────────────┘
         │
         │ Agents process & publish instructions
         ▼
┌─────────────────┐
│  Python Backend │  ← This code
│  (Agents)       │
└─────────────────┘
```

## Agents

- **DailyPostAgent** - Generates LinkedIn posts using Gemini
- **MessagingAgent** - Classifies profiles (Recruiter, Co-founder, Waterloo Student)
- **DatingAgent** - Detects Waterloo students, estimates stream, generates pickup lines

## API Endpoints

- `GET /health` - Health check
- `POST /api/start-scrolling` - Start automation workflow
- `POST /api/stop-scrolling` - Stop workflow
- `POST /api/generate-daily-post` - Generate LinkedIn post
- `POST /api/process-profile` - Process a profile
- `GET /api/queue-stats` - Queue statistics

## Integration with Patchright

The Patchright scraper (in `../patchright/`) should:
1. Publish scraped profiles to `profiles:scraped` Redis queue
2. Consume from `playwright:post` queue (post instructions)
3. Consume from `playwright:message` queue (message/connection instructions)

See `PLAYWRIGHT_INTEGRATION.md` for detailed integration guide.

## Testing

```bash
# Test with real profile data
python3 test_profile_data.py
```
