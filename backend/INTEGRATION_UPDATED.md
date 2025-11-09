# Updated Integration: Patchright Pre-Classification

## Overview

Patchright now classifies profiles with a `type` field before publishing to Redis. The backend agents use this classification to optimize processing.

## Profile Format

```json
{
  "url": "https://www.linkedin.com/in/...",
  "name": "...",
  "headline": "...",
  "bio": "...",
  "type": "waterloo",  // ← Pre-classified by Patchright
  "experience": [...],
  "education": [...]
}
```

## Type Values

- `"waterloo"` - Waterloo student
- `"recruiter"` - Recruiter
- `"cofounder"` / `"founder"` - Co-founder/Founder
- `"other"` - Other (or not specified)

## Backend Behavior

### With Pre-classified Type

1. **`type: "waterloo"`**
   - ✅ Skips Messaging Agent classification (no LLM call)
   - ✅ Routes directly to Dating Agent
   - ✅ Faster processing, saves API costs

2. **`type: "recruiter"`**
   - ✅ Uses Messaging Agent to generate recruiter message
   - ✅ Publishes to `playwright:message` queue

3. **`type: "cofounder"` or `"founder"`**
   - ✅ Uses Messaging Agent to generate co-founder message
   - ✅ Publishes to `playwright:message` queue

4. **`type: "other"` or no type**
   - ✅ Falls back to LLM classification
   - ✅ Processes accordingly

## Benefits

- **Faster**: No LLM call needed for pre-classified profiles
- **Cheaper**: Reduces API costs
- **More reliable**: Patchright can use rule-based classification
- **Flexible**: Still supports LLM classification as fallback

## Terminal Feedback

When a pre-classified type is used:

```
╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Messaging Agent] Using pre-classified type: waterloo                    │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Classification ──────────────────────────────╮
│ 🏷️  CLASSIFIED: https://www.linkedin.com/in/...                            │
│    Category: waterloo_student (confidence: 100.00%)                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Workflow

```
Patchright scrapes profile
  ↓
Adds type: "waterloo" (rule-based classification)
  ↓
Publishes to Redis: profiles:scraped
  ↓
Backend detects type: "waterloo"
  ↓
Skips Messaging Agent classification
  ↓
Routes directly to Dating Agent
  ↓
Dating Agent processes (stream estimation, pickup line)
  ↓
Publishes instruction to Redis: playwright:message
```

## Testing

The test script (`test_profile_data.py`) includes a profile with `type: "waterloo"` to test the pre-classification flow.

