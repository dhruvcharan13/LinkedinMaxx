# LinkedInMaxx

A hackathon project that automates LinkedIn behavior for Waterloo students - posting, connecting, and messaging with AI-powered agents.

## Tech Stack

- **Backend**: Python + FastAPI + LangChain + Google Gemini
- **Frontend**: React + TypeScript + Vite
- **Automation**: Playwright (LinkedIn scraping & automation)
- **Queue System**: Redis
- **AI Agents**: LangChain agents for post generation, profile classification, and messaging

## Features

- 🤖 **Daily Post Agent** - Generates LinkedIn posts using AI
- 💬 **Messaging Agent** - Classifies profiles and generates personalized messages
- 💕 **Dating Agent** - Detects Waterloo students and generates pickup lines for same-stream matches
- 📤 **Redis Queues** - Decoupled architecture for Playwright integration
- 🎨 **Rich Terminal Feedback** - Real-time visibility into agent actions

## Project Structure

```
LinkedinMaxx/
├── backend/          # Python backend with LangChain agents
├── client/           # React frontend
├── server/           # Node.js server (optional)
└── README.md
```

## Setup

### Backend

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY and other settings
   ```

3. **Start Redis:**
   ```bash
   brew services start redis
   # or
   docker run -d -p 6379:6379 redis:alpine
   ```

4. **Run the backend:**
   ```bash
   python3 main.py
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd client
   npm install
   ```

2. **Run development server:**
   ```bash
   npm run dev
   ```

## Playwright Integration

See `backend/PLAYWRIGHT_INTEGRATION.md` for complete integration guide.

### Key Queues

- **Input**: `profiles:scraped` - Publish scraped profiles here
- **Output**: `playwright:post` - Consume post instructions
- **Output**: `playwright:message` - Consume message/connection instructions

## API Endpoints

- `GET /health` - Health check
- `POST /api/start-scrolling` - Start automation workflow
- `POST /api/stop-scrolling` - Stop workflow
- `POST /api/generate-daily-post` - Generate LinkedIn post
- `POST /api/process-profile` - Process a profile
- `GET /api/queue-stats` - Queue statistics

## Environment Variables

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Backend
BACKEND_PORT=8000
USER_STREAM=1A
```

## Documentation

- `backend/PLAYWRIGHT_INTEGRATION.md` - Playwright integration guide
- `backend/BACKEND_SETUP.md` - Backend setup and API docs
- `backend/AGENT_OUTPUT_EXAMPLE.md` - Example agent outputs

## License

MIT

