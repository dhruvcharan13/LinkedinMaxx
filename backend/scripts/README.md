# Demo Tasks Preload Script

This directory contains scripts for preloading demo tasks into the Redis queue for the LinkedInMaxx demo.

## Overview

The `preload_demo_tasks.py` script pre-populates the `tasks:pending_approval` Redis queue with demo tasks that will appear in the frontend for approval. This is useful for demos where you want predictable, predefined tasks instead of relying on unpredictable scraped data.

## Demo Tasks

The script creates **4 demo tasks**:

1. **Message Task 1** (Dating Match)
   - Agent: Dating Agent 💕
   - Classification: Waterloo student (same stream)
   - Content: Pickup line for same-stream match
   - Purpose: Demonstrate dating agent functionality

2. **Message Task 2** (Recruiter)
   - Agent: Messaging Agent 💬
   - Classification: Recruiter
   - Content: Professional message to recruiter
   - Purpose: Demonstrate messaging agent functionality

3. **Comment Task 1** (Tech Post)
   - Agent: Comment Agent 💬
   - Content: Comment on tech/AI post
   - Purpose: Demonstrate comment agent functionality

4. **Comment Task 2** (Career Post)
   - Agent: Comment Agent 💬
   - Content: Comment on career advice post
   - Purpose: Demonstrate comment agent functionality

## Usage

### Basic Usage (Default Demo Data)

```bash
cd backend
python3 scripts/preload_demo_tasks.py
```

This will preload 4 demo tasks using the default configuration.

### Clear Queue Before Preloading

```bash
python3 scripts/preload_demo_tasks.py --clear
```

This clears any existing tasks in the queue before preloading new ones.

### Use Custom Config File

```bash
python3 scripts/preload_demo_tasks.py --config scripts/demo_tasks_config.json
```

You can customize the demo tasks by editing `demo_tasks_config.json` and loading it with the `--config` flag.

## Configuration

### Default Configuration

The default configuration is embedded in `preload_demo_tasks.py` and includes:

- **2 message tasks**: 1 dating match, 1 recruiter
- **2 comment tasks**: 2 different posts

### Custom Configuration

Edit `demo_tasks_config.json` to customize:

- Profile URLs for message tasks
- Post URLs for comment tasks
- Message/comment content
- Agent metadata (classification, confidence, reasoning)

### Configuration Format

```json
{
  "messages": [
    {
      "url": "https://www.linkedin.com/in/profile/",
      "name": "Person Name",
      "content": "Message text",
      "agent_name": "Dating Agent",
      "agent_emoji": "💕",
      "metadata": {
        "action": "send_message",
        "classification": "waterloo_student",
        "estimated_stream": "2A",
        "user_stream": "2A",
        "same_stream": true,
        "confidence": 0.95,
        "reasoning": "Profile shows 2A Computer Science at University of Waterloo"
      }
    }
  ],
  "comments": [
    {
      "url": "https://www.linkedin.com/feed/update/urn:li:activity:1234567890/",
      "name": "Post Name",
      "content": "Comment text",
      "agent_name": "Comment Agent",
      "agent_emoji": "💬",
      "metadata": {
        "action": "send_comment",
        "classification": "relevant",
        "confidence": 0.85,
        "reasoning": "Post is about AI/tech, relevant to CS student interests"
      }
    }
  ]
}
```

## Demo Workflow

1. **Preload demo tasks** (before backend starts):
   ```bash
   python3 scripts/preload_demo_tasks.py --clear
   ```

2. **Start backend**:
   ```bash
   python3 main.py
   ```

3. **Start frontend**:
   ```bash
   cd ../client
   npm run dev
   ```

4. **Start orchestrator** (optional, for execution):
   ```bash
   cd ../patchright
   python3 playwright_orchestrator.py
   ```

5. **View tasks in frontend**: The 4 preloaded tasks will appear in the frontend for approval.

6. **Approve tasks**: Click "Approve" on tasks to execute them via Playwright.

## Task Structure

Each task in the queue matches the `PendingTask` interface expected by the frontend:

```python
{
    "task_id": "tasks:pending_approval:2025-11-09T14:52:27.435697",
    "type": "message",  # or "comment" or "post"
    "content": "Message text or comment text",
    "url": "https://www.linkedin.com/in/profile/",  # Profile URL for messages, post URL for comments
    "name": "Person Name",
    "agent_name": "Dating Agent",
    "agent_emoji": "💕",
    "metadata": {
        "action": "send_message",
        "classification": "waterloo_student",
        "confidence": 0.95,
        "reasoning": "Profile shows 2A Computer Science at University of Waterloo"
    },
    "status": "pending",
    "timestamp": "2025-11-09T14:52:27.435697"
}
```

## Verification

After preloading, verify tasks are in the queue:

```bash
# Check via API
curl http://localhost:8000/api/tasks/pending | python3 -m json.tool

# Check queue stats
curl http://localhost:8000/api/queue-stats | python3 -m json.tool
```

## Customization for Demo

To customize the demo tasks for your specific demo:

1. **Update URLs**: Edit `demo_tasks_config.json` with real LinkedIn profile/post URLs
2. **Update Messages**: Customize message and comment content
3. **Update Metadata**: Adjust classification, confidence, reasoning to match your demo scenario
4. **Run Script**: Use `--config` flag to load your custom config

## Notes

- Tasks are stored in both Redis list (`tasks:pending_approval`) and Redis hash (`tasks:pending_approval:tasks`)
- Tasks will appear in the frontend immediately after preloading
- Approved tasks are removed from the pending queue and published to execution queues (`playwright:message`, `playwright:comment`, `playwright:post`)
- The orchestrator consumes from execution queues and executes tasks via Playwright

## Troubleshooting

**Tasks don't appear in frontend:**
- Check if backend is running: `curl http://localhost:8000/api/tasks/pending`
- Check Redis connection: `redis-cli ping`
- Verify tasks are in queue: `redis-cli LLEN tasks:pending_approval`

**Script fails to connect to Redis:**
- Make sure Redis is running: `redis-server`
- Check Redis is accessible: `redis-cli ping`

**Tasks are cleared:**
- Use `--clear` flag only when you want to clear existing tasks
- Be careful not to clear tasks that are pending approval in the frontend

