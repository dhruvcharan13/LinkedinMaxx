# LinkedInMaxx Backend Setup Guide

## Overview

This backend implements a LangChain-based agent system for LinkedIn automation. It uses:
- **LangChain** for AI agent orchestration
- **Redis** for task queues and agent memory
- **FastAPI** for REST API endpoints
- **Rich** for beautiful terminal output

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │ HTTP API
         ▼
┌─────────────────┐
│   FastAPI       │
│   (main.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         Agents                      │
│  ┌──────────┐  ┌──────────┐        │
│  │  Daily   │  │Messaging │        │
│  │  Post    │  │  Agent   │        │
│  └──────────┘  └────┬─────┘        │
│                     │               │
│              ┌──────▼─────┐         │
│              │  Dating    │         │
│              │  Agent     │         │
│              └────────────┘         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Redis Queues                │
│  • playwright:post                  │
│  • playwright:message               │
│  • profiles:scraped                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Playwright                  │
│    (Consumes instructions)          │
└─────────────────────────────────────┘
```

## Setup Instructions

### 1. Prerequisites

- Python 3.10+
- Redis server
- OpenAI API key

### 2. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the `backend/` directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Backend Configuration
BACKEND_PORT=8000
LOG_LEVEL=INFO

# LinkedInMaxx Configuration
USER_STREAM=1A  # Your Waterloo stream (1A, 1B, 2A, 2B, 4, or 8)
WATERLOO_STREAM_DATA_PATH=./data/waterloo_streams.json
```

### 4. Start Redis

**Option A: Using Docker**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**Option B: Local Installation**
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download from https://redis.io/download
```

### 5. Test the Setup

Run the test script to verify everything works:

```bash
python test_agents.py
```

This will test:
- Redis connection
- Daily Post Agent
- Messaging Agent
- Dating Agent
- Full workflow

### 6. Start the Backend Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
```

### Start Scrolling
```bash
POST /api/start-scrolling
Content-Type: application/json

{
  "generate_daily_post": true,
  "context": "Optional context for post generation"
}
```

### Stop Scrolling
```bash
POST /api/stop-scrolling
```

### Generate Daily Post
```bash
POST /api/generate-daily-post
Content-Type: application/json

{
  "context": "Optional context"
}
```

### Process Profile
```bash
POST /api/process-profile
Content-Type: application/json

{
  "url": "https://linkedin.com/in/profile",
  "bio": "Profile bio text",
  "experience": "Experience details",
  "education": "Education details"
}
```

### Queue Statistics
```bash
GET /api/queue-stats
```

## Workflow

### 1. Daily Post Generation
- Agent generates a LinkedIn post using LangChain
- Post is published to `playwright:post` queue
- Playwright consumes and publishes the post

### 2. Profile Scraping (Playwright)
- Playwright scrapes LinkedIn feed
- Profiles are published to `profiles:scraped` queue
- Each profile includes: URL, bio, experience, education

### 3. Profile Processing
- Messaging Agent classifies each profile:
  - **Recruiter** → Generate internship inquiry message
  - **Co-founder/Founder** → Generate collaboration message
  - **Waterloo Student** → Route to Dating Agent
  - **Other** → Just connect (no message)

### 4. Dating Agent Processing
- Detects if profile is Waterloo student
- Estimates their co-op stream
- If same stream: Generate pickup line
- If different stream: Just connect

### 5. Message Execution
- Messages/connection requests published to `playwright:message` queue
- Playwright consumes and executes

## Terminal Feedback

The backend provides rich terminal output showing:
- 🤖 Agent actions
- 📤 Data published to queues
- 📥 Data extracted from queues
- 🏷️ Profile classifications
- ✅ Task completions
- ❌ Errors

## Testing

### Test Individual Agents

```bash
# Test Daily Post Agent
python -c "from agents.daily_post_agent import DailyPostAgent; agent = DailyPostAgent(); agent.generate_and_publish()"

# Test Messaging Agent
python -c "from agents.messaging_agent import MessagingAgent; agent = MessagingAgent(); print('Messaging agent loaded')"

# Test Dating Agent
python -c "from agents.dating_agent import DatingAgent; agent = DatingAgent(); print('Dating agent loaded')"
```

### Test Full Workflow

```bash
python test_agents.py
```

## Playwright Integration

The backend publishes instructions to Redis queues. Playwright should:

1. **Subscribe to queues:**
   - `playwright:post` - Post publishing instructions
   - `playwright:message` - Message/connection instructions

2. **Publish scraped profiles:**
   - `profiles:scraped` - Scraped profile data

3. **Instruction format:**
```json
{
  "task_id": "playwright:post:2024-01-01T12:00:00",
  "queue": "playwright:post",
  "instruction": {
    "action": "publish_post",
    "content": "Post content here...",
    "metadata": {},
    "timestamp": "2024-01-01T12:00:00"
  },
  "status": "pending"
}
```

## Troubleshooting

### Redis Connection Failed
- Ensure Redis is running: `redis-cli ping`
- Check Redis host/port in `.env`
- Verify Redis is accessible: `telnet localhost 6379`

### OpenAI API Errors
- Verify API key in `.env`
- Check OpenAI account has credits
- Verify API key permissions

### Import Errors
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

### Agent Errors
- Check OpenAI API key is set
- Verify model name is correct (gpt-4, gpt-3.5-turbo, etc.)
- Check terminal output for detailed error messages

## Next Steps

1. **Integrate Playwright** - Set up Playwright to consume instructions and scrape profiles
2. **Add Rate Limiting** - Implement rate limiting for API calls
3. **Add Authentication** - Add API key authentication for production
4. **Add Monitoring** - Add logging and monitoring for production
5. **Add Error Handling** - Improve error handling and retry logic

## Support

For issues or questions, check:
- Terminal output for detailed error messages
- Redis queue contents: `redis-cli LLEN playwright:post`
- API docs: `http://localhost:8000/docs`

