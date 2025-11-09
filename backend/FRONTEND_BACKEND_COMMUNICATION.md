# Frontend ↔ Backend Communication Architecture

## Overview

This document explains how the frontend and backend communicate for task approval workflow.

## Architecture Options

### Option 1: FastAPI REST API (Recommended - Simple & Effective) ⭐

**How it works:**
1. Agents generate tasks → Publish to `tasks:pending_approval` Redis queue
2. Frontend polls `/api/tasks/pending` every 2-3 seconds
3. Frontend displays tasks, allows editing/approve/deny
4. Frontend sends decisions to `/api/tasks/approve` or `/api/tasks/reject`
5. Backend publishes approved tasks to execution queues (`playwright:post`, `playwright:message`, etc.)

**Pros:**
- ✅ Simple to implement
- ✅ Works with existing FastAPI setup
- ✅ Easy to debug
- ✅ No complex WebSocket setup
- ✅ Frontend can work independently

**Cons:**
- ⚠️ Requires polling (but only every 2-3 seconds)
- ⚠️ Slight delay (2-3 seconds) for new tasks

**Complexity:** Low (1-2 hours)

---

### Option 2: WebSockets (Real-time) 

**How it works:**
1. Frontend connects to WebSocket endpoint
2. Backend sends tasks in real-time via WebSocket
3. Frontend sends approve/deny via WebSocket
4. Backend publishes approved tasks to Redis

**Pros:**
- ✅ Real-time updates (no polling)
- ✅ Better UX

**Cons:**
- ❌ More complex to implement
- ❌ Requires WebSocket server
- ❌ Connection management needed
- ❌ More error handling

**Complexity:** Medium-High (4-6 hours)

---

### Option 3: Server-Sent Events (SSE)

**How it works:**
1. Frontend connects to SSE endpoint
2. Backend streams tasks to frontend
3. Frontend sends approve/deny via REST API
4. Backend publishes approved tasks to Redis

**Pros:**
- ✅ Real-time updates (one-way)
- ✅ Simpler than WebSockets
- ✅ Auto-reconnect

**Cons:**
- ❌ One-way only (still need REST for approvals)
- ❌ More complex than REST polling

**Complexity:** Medium (3-4 hours)

---

### Option 4: Just Display (No Approval)

**How it works:**
1. Agents generate tasks → Publish directly to execution queues
2. Frontend polls `/api/tasks/execution` to display what's being executed
3. No approval needed

**Pros:**
- ✅ Simplest (no approval flow)
- ✅ Fastest to implement
- ✅ Agents run autonomously

**Cons:**
- ❌ No user control
- ❌ No editing
- ❌ Less safe (agents can send anything)

**Complexity:** Very Low (30 minutes)

---

## Recommended Solution: Option 1 (FastAPI REST)

### Flow Diagram

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
┌─────────────────┐      Poll (every 2-3s)
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

### Implementation Plan

#### 1. Backend Changes

**New Redis Queue:**
- `tasks:pending_approval` - Tasks waiting for user approval

**New FastAPI Endpoints:**
- `GET /api/tasks/pending` - Get all pending tasks
- `POST /api/tasks/approve` - Approve a task (with optional edited text)
- `POST /api/tasks/reject` - Reject a task
- `GET /api/tasks/{task_id}` - Get a specific task

**Agent Changes:**
- Instead of publishing directly to `playwright:post` or `playwright:message`
- Publish to `tasks:pending_approval` first
- Include all task metadata (type, content, target, etc.)

#### 2. Frontend Changes

**New API Client:**
- `src/services/api.ts` - API client for FastAPI
- Functions: `getPendingTasks()`, `approveTask()`, `rejectTask()`

**Updated AgenticControlPanel:**
- Polls `/api/tasks/pending` every 2-3 seconds
- Displays tasks from API instead of mock data
- Sends approve/deny to API
- Updates UI based on API responses

#### 3. Task Format

**Pending Task Format:**
```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:00:00",
  "type": "post" | "message" | "comment",
  "agent_name": "Daily Post Agent" | "Messaging Agent" | "Dating Agent" | "Comment Agent",
  "agent_emoji": "🧠" | "💬" | "💕" | "💬",
  "content": "Task content (post text, message text, comment text)",
  "target": {
    "profile_url": "https://linkedin.com/in/...",  // For messages
    "post_url": "https://linkedin.com/feed/...",   // For comments
    "name": "Person Name"                           // For messages
  },
  "metadata": {
    "confidence": 87,
    "classification": "recruiter" | "cofounder" | "waterloo_student",
    "stream": "2A",
    "reasoning": "..."
  },
  "status": "pending",
  "timestamp": "2025-11-09T10:00:00"
}
```

**Approval Request Format:**
```json
{
  "task_id": "tasks:pending_approval:2025-11-09T10:00:00",
  "status": "approved" | "rejected",
  "edited_content": "Optional edited content",
  "timestamp": "2025-11-09T10:00:00"
}
```

---

## Complexity Comparison

| Option | Implementation Time | Complexity | Real-time | User Control |
|--------|-------------------|------------|-----------|--------------|
| **REST API (Polling)** | 1-2 hours | Low | No (2-3s delay) | ✅ Full |
| **WebSockets** | 4-6 hours | Medium-High | ✅ Yes | ✅ Full |
| **SSE** | 3-4 hours | Medium | ✅ Yes | ✅ Full |
| **Just Display** | 30 minutes | Very Low | No | ❌ None |

---

## Recommendation

**Use Option 1 (REST API with Polling)** because:
1. ✅ Simple to implement (1-2 hours)
2. ✅ Works with existing FastAPI setup
3. ✅ 2-3 second delay is acceptable for this use case
4. ✅ Easy to debug and maintain
5. ✅ Can upgrade to WebSockets later if needed

**If you want real-time updates later**, you can easily upgrade to WebSockets without changing the core logic.

---

## Implementation Steps

1. **Backend:**
   - Add `tasks:pending_approval` queue
   - Modify agents to publish to pending queue
   - Add FastAPI endpoints for task management
   - Add task approval/rejection logic

2. **Frontend:**
   - Create API client service
   - Update AgenticControlPanel to use API
   - Add polling logic (every 2-3 seconds)
   - Handle approve/deny API calls

3. **Testing:**
   - Test task flow end-to-end
   - Test editing and approval
   - Test rejection

---

## Next Steps

1. Implement backend changes (FastAPI endpoints + Redis queue)
2. Update agents to publish to pending queue
3. Implement frontend API client
4. Update frontend to use API
5. Test end-to-end flow

