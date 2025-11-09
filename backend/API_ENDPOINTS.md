# FastAPI Endpoints - LinkedInMaxx Backend

## Task Management Endpoints

### GET `/api/tasks/pending`

Get all pending tasks waiting for frontend approval.

**Response:**
```json
{
  "status": "success",
  "tasks": [
    {
      "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
      "type": "post",
      "content": "Post content here...",
      "url": "",
      "name": "",
      "agent_name": "Daily Post Agent",
      "agent_emoji": "🧠",
      "metadata": {
        "confidence": 87,
        "classification": "recruiter"
      },
      "status": "pending",
      "timestamp": "2025-11-09T10:31:14.674919"
    }
  ],
  "count": 1,
  "timestamp": "2025-11-09T10:31:14.674919"
}
```

### POST `/api/tasks/approve`

Approve a task and publish it to execution queue.

**Request:**
```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
  "edited_content": "Optional edited content (if user edited the task)"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task approved and queued for execution",
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
  "timestamp": "2025-11-09T10:31:14.674919"
}
```

**What happens:**
- Task is removed from `tasks:pending_approval` queue
- Task is published to execution queue based on type:
  - `post` → `playwright:post`
  - `message` → `playwright:message`
  - `comment` → `playwright:comment`
- Published format matches Playwright expectations

### POST `/api/tasks/reject`

Reject a task (removes from pending queue).

**Request:**
```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Task rejected",
  "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
  "timestamp": "2025-11-09T10:31:14.674919"
}
```

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
  "edited_content": "Optional edited content"
}
```

### Task Published to Playwright (After Approval)

**Post:**
```json
{
  "action": "publish_post",
  "content": "Post content",
  "metadata": {...},
  "timestamp": "..."
}
```

**Message:**
```json
{
  "profile_url": "https://linkedin.com/in/...",
  "name": "Person Name",
  "message": "Message text",
  "action": "send_message" | "connect_only",
  "timestamp": "..."
}
```

**Comment:**
```json
{
  "post_url": "https://linkedin.com/feed/update/...",
  "comment": "Comment text",
  "timestamp": "..."
}
```

## Data Flow

```
Agent → Redis: tasks:pending_approval
  ↓
Frontend polls GET /api/tasks/pending
  ↓
Frontend displays tasks
  ↓
User edits/approves/rejects
  ↓
Frontend sends POST /api/tasks/approve
  ↓
Backend publishes to execution queue (playwright:post, playwright:message, playwright:comment)
  ↓
Playwright consumes and executes
```

## Testing

### Test Pending Tasks Endpoint

```bash
curl http://localhost:8000/api/tasks/pending
```

### Test Approve Task

```bash
curl -X POST http://localhost:8000/api/tasks/approve \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919",
    "edited_content": "Edited content here"
  }'
```

### Test Reject Task

```bash
curl -X POST http://localhost:8000/api/tasks/reject \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "tasks:pending_approval:2025-11-09T10:31:14.674919"
  }'
```

