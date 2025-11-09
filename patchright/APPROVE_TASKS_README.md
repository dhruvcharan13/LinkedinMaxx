# Task Approval Script

This script allows you to manually approve tasks and send them to Playwright queues, bypassing the frontend approval step.

## Usage

### Auto-approve all pending tasks:
```bash
cd patchright
python3 approve_tasks.py --auto
```

### Interactive approval (review each task):
```bash
cd patchright
python3 approve_tasks.py
```

### Watch mode (continuously check for new tasks):
```bash
cd patchright
python3 approve_tasks.py --watch
```

### Watch mode with auto-approval:
```bash
cd patchright
python3 approve_tasks.py --watch --auto
```

## Interactive Mode Options

When a task is shown, you can:
- `[a]` - Approve as-is
- `[e]` - Edit then approve
- `[r]` - Reject
- `[s]` - Skip (approve later)
- `[q]` - Quit

## Workflow

1. **Backend generates tasks** → Queues to `tasks:pending_approval`
2. **Run approval script** → Approves tasks and sends to Playwright queues
3. **Playwright orchestrator** → Consumes from Playwright queues and executes

## Example

```bash
# Terminal 1: Start backend
cd backend
python3 main.py

# Terminal 2: Start orchestrator
cd patchright
python3 playwright_orchestrator.py

# Terminal 3: Approve tasks (auto-approve)
cd patchright
python3 approve_tasks.py --auto --watch
```

## Notes

- The script connects to Redis to get pending tasks
- Approved tasks are sent to the appropriate Playwright queues:
  - `playwright:post` for posts
  - `playwright:message` for messages
  - `playwright:comment` for comments
- Rejected tasks are marked as rejected but not removed (for logging)

