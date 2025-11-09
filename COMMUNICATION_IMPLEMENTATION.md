# Frontend-Backend Communication Implementation

## Overview

FastAPI REST API communication between frontend and backend for task approval workflow.

## Architecture

### Communication Method: FastAPI REST API

**Why FastAPI?**
- ✅ Simple to implement (1-2 hours)
- ✅ Works with existing FastAPI setup
- ✅ 2-3 second polling delay is acceptable
- ✅ Easy to debug and maintain
- ✅ Can upgrade to WebSockets later if needed

### Data Flow

```
┌─────────────┐
│   Agents    │
│  Generate   │
│   Tasks     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Redis Queue:    │
│ tasks:pending_  │
│ approval        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐      Poll (every 2s)
│   FastAPI       │ ◄─────────────────┐
│  /api/tasks/    │                   │
│  pending        │                   │
└──────┬──────────┘                   │
       │                               │
       ▼                               │
┌─────────────┐                        │
│  Frontend   │                        │
│  Display    │                        │
│  Edit/Approve│                       │
└──────┬──────┘                        │
       │                                │
       │ POST /api/tasks/approve        │
       │ POST /api/tasks/reject         │
       └───────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  FastAPI      │
            │  Processes    │
            │  Decision     │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ Redis:        │
            │ playwright:   │
            │ post/message  │
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │  Patchright   │
            │  Executes     │
            └───────────────┘
```

## Implementation

### Backend

#### 1. Redis Client (`backend/utils/redis_client.py`)

**New Methods:**
- `queue_pending_task()` - Queues task for frontend approval
- `get_pending_tasks()` - Gets all pending tasks
- `approve_task()` - Approves task and publishes to execution queue
- `reject_task()` - Rejects task

#### 2. FastAPI Endpoints (`backend/main.py`)

**Endpoints:**
- `GET /api/tasks/pending` - Get all pending tasks
- `POST /api/tasks/approve` - Approve a task (with optional edited content)
- `POST /api/tasks/reject` - Reject a task

#### 3. Agent Updates

**All agents now:**
- Queue tasks to `tasks:pending_approval` instead of publishing directly
- Include: type, content, url, name, agent_name, agent_emoji, metadata

### Frontend

#### 1. API Client (`client/src/services/api.ts`)

**Functions:**
- `getPendingTasks()` - Fetches pending tasks from backend
- `approveTask(taskId, editedContent?)` - Approves task
- `rejectTask(taskId)` - Rejects task

#### 2. AgenticControlPanel (`client/src/components/AgenticControlPanel.tsx`)

**Features:**
- Polls `/api/tasks/pending` every 2 seconds
- Displays tasks from backend
- Handles approve/reject/edit actions
- Updates UI based on API responses

#### 3. AgentCard (`client/src/components/AgentCard.tsx`)

**Features:**
- "Save & Approve" button when editing
- Passes edited content to approve handler
- Updates UI immediately for better UX

## Task Format

### Task Sent to Frontend

```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
  "type": "post" | "message" | "comment",
  "content": "Task content (post text, message text, comment text)",
  "url": "Profile URL or post URL",
  "name": "Person name (for messages/comments)",
  "agent_name": "Daily Post Agent" | "Messaging Agent" | "Dating Agent" | "Comment Agent",
  "agent_emoji": "🧠" | "💬" | "💕" | "💬",
  "metadata": {
    "confidence": 87,
    "classification": "recruiter" | "cofounder" | "waterloo_student",
    "action": "send_message" | "connect_only",
    "estimated_stream": "2A",
    "user_stream": "1A",
    "same_stream": true,
    "reasoning": "..."
  },
  "status": "pending",
  "timestamp": "2025-11-09T10:31:14.674919"
}
```

### Task Received from Frontend (Approval)

```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
  "edited_content": "Optional edited content (if user edited the task)"
}
```

### Task Published to Playwright (After Approval)

**Post:**
```json
{
  "action": "publish_post",
  "content": "Post content (edited or original)",
  "metadata": {...},
  "timestamp": "..."
}
```

**Message:**
```json
{
  "profile_url": "https://linkedin.com/in/...",
  "name": "Person Name",
  "message": "Message text (edited or original)",
  "action": "send_message" | "connect_only",
  "timestamp": "..."
}
```

**Comment:**
```json
{
  "post_url": "https://linkedin.com/feed/update/...",
  "comment": "Comment text (edited or original)",
  "timestamp": "..."
}
```

## How It Works

### 1. Agent Generates Task

```python
# Daily Post Agent
task_data = {
    "type": "post",
    "content": "Generated post content...",
    "url": "",
    "name": "",
    "agent_name": "Daily Post Agent",
    "agent_emoji": "🧠",
    "metadata": {...}
}
task_id = redis_client.queue_pending_task(task_data)
```

### 2. Frontend Polls for Tasks

```typescript
// Polls every 2 seconds
const tasks = await getPendingTasks();
// Displays in UI
```

### 3. User Approves/Rejects

```typescript
// Approve with edited content
await approveTask(taskId, editedContent);

// Reject
await rejectTask(taskId);
```

### 4. Backend Publishes to Execution Queue

```python
# Backend receives approval
if task_type == "post":
    redis_client.queue_post_instruction(content, metadata)
elif task_type == "message":
    redis_client.queue_message_instruction(url, content, action, name)
elif task_type == "comment":
    redis_client.queue_comment_instruction(url, content)
```

### 5. Playwright Consumes and Executes

```python
# Playwright consumes from execution queues
instruction = redis_client.get_instruction("playwright:post")
# Executes the task
```

## API Endpoints

### GET `/api/tasks/pending`

Get all pending tasks.

**Response:**
```json
{
  "status": "success",
  "tasks": [...],
  "count": 1,
  "timestamp": "..."
}
```

### POST `/api/tasks/approve`

Approve a task.

**Request:**
```json
{
  "task_id": "...",
  "edited_content": "Optional edited content"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task approved and queued for execution",
  "task_id": "...",
  "timestamp": "..."
}
```

### POST `/api/tasks/reject`

Reject a task.

**Request:**
```json
{
  "task_id": "..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task rejected",
  "task_id": "...",
  "timestamp": "..."
}
```

## Environment Variables

### Frontend

Add to `.env` or `vite.config.ts`:
```env
VITE_API_URL=http://localhost:8000
```

### Backend

Uses existing `.env`:
```env
GEMINI_API_KEY=...
REDIS_HOST=localhost
REDIS_PORT=6379
USER_STREAM=1A
BACKEND_PORT=8000
```

## Testing

### Test Backend Endpoints

```bash
# Get pending tasks
curl http://localhost:8000/api/tasks/pending

# Approve task
curl -X POST http://localhost:8000/api/tasks/approve \
  -H "Content-Type: application/json" \
  -d '{"task_id": "...", "edited_content": "..."}'

# Reject task
curl -X POST http://localhost:8000/api/tasks/reject \
  -H "Content-Type: application/json" \
  -d '{"task_id": "..."}'
```

### Test Frontend

1. Start backend: `cd backend && python3 main.py`
2. Start frontend: `cd client && npm run dev`
3. Open http://localhost:3000
4. Generate a task (via API or agent)
5. See task appear in frontend
6. Approve/reject/edit task
7. Check Redis queues for execution

## Files Modified

### Backend
- `backend/utils/redis_client.py` - Added pending task methods
- `backend/main.py` - Added FastAPI endpoints
- `backend/agents/daily_post_agent.py` - Queue for approval
- `backend/agents/messaging_agent.py` - Queue for approval
- `backend/agents/dating_agent.py` - Queue for approval
- `backend/agents/comment_agent.py` - Queue for approval

### Frontend
- `client/src/services/api.ts` - API client (NEW)
- `client/src/components/AgenticControlPanel.tsx` - Polls API
- `client/src/components/AgentCard.tsx` - Handles edited content

## Complexity

**Implementation Time:** 1-2 hours
**Difficulty:** Low
**Real-time:** No (2-3 second polling delay)
**User Control:** ✅ Full (edit, approve, reject)

## Benefits

1. ✅ Simple to implement
2. ✅ Easy to debug
3. ✅ Full user control
4. ✅ Works with existing setup
5. ✅ Can upgrade to WebSockets later

## Next Steps

1. Test end-to-end flow
2. Add error handling
3. Add loading states
4. Test with real agents
5. Add environment variable for API URL

