# Agent Output Example - Elrich Chen Profile

## Profile Data Received

```json
{
  "url": "https://www.linkedin.com/in/elrich-chen/",
  "name": "Elrich Chen",
  "headline": "CS @ UWaterloo | AI automations for DoneMaker | Aspiring Backend Engineer 💻☁️",
  "bio": "University of Waterloo CS student...",
  "experience": [...],
  "education": ["University of Waterloo", "Transferred into 2A term.", ...]
}
```

## Expected Agent Outputs

### 1. Messaging Agent - Classification

**Input:** Profile data from Playwright

**Processing:**
- Bio contains: "University of Waterloo", "CS @ UWaterloo"
- Education: "University of Waterloo", "Transferred into 2A term"
- Experience: Multiple internships, including at DoneMaker

**Classification Result:**
```json
{
  "category": "waterloo_student",
  "confidence": 0.95,
  "reasoning": "Profile clearly indicates University of Waterloo student (CS program), mentions UWaterloo in headline, and has Waterloo email (eklchen@uwaterloo.ca)"
}
```

**Action:** `route_to_dating_agent`

**Terminal Output:**
```
╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Messaging Agent] Classifying profile...                                  │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Classification ──────────────────────────────╮
│ 🏷️  CLASSIFIED: https://www.linkedin.com/in/elrich-chen/                    │
│    Category: waterloo_student (confidence: 95.00%)                           │
╰──────────────────────────────────────────────────────────────────────────────╯

✅ Profile routed to Dating Agent
```

---

### 2. Dating Agent - Stream Estimation

**Input:** Profile data (routed from Messaging Agent)

**Processing:**
- Detects Waterloo student: ✅ (bio mentions "University of Waterloo", email is uwaterloo.ca)
- Education shows: "Transferred into 2A term"
- Experience shows: Internships but dates not clearly visible in provided data
- Headline: "CS @ UWaterloo"

**Stream Estimation:**
```json
{
  "is_waterloo": true,
  "estimated_stream": "2A",
  "confidence": 0.85,
  "reasoning": "Profile explicitly states 'Transferred into 2A term' in education section, indicating they are currently in 2A stream"
}
```

**Stream Comparison:**
- User Stream: `1A`
- Estimated Stream: `2A`
- Same Stream: `false`

**Action:** `connect_only` (different stream, so just connect without pickup line)

**Terminal Output:**
```
╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Dating Agent] Estimating Waterloo stream...                              │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Dating Agent] Estimated stream: 2A                                      │
│    Confidence: 85.00%                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯

✅ Different stream (2A vs 1A), connection queued
```

**Redis Instruction Published:**
```json
{
  "task_id": "playwright:message:2025-11-08T16:54:07.771611",
  "queue": "playwright:message",
  "instruction": {
    "action": "connect_only",
    "profile_url": "https://www.linkedin.com/in/elrich-chen/",
    "message": "",
    "timestamp": "2025-11-08T16:54:07.771611"
  },
  "status": "pending"
}
```

---

### 3. Alternative Scenario: Same Stream (1A)

If the user's stream was also `2A`, the Dating Agent would:

**Stream Comparison:**
- User Stream: `2A`
- Estimated Stream: `2A`
- Same Stream: `true` ✅

**Pickup Line Generation:**
```
💕 Generated Pickup Line:
"Hey Elrich! Saw you're in 2A too - same stream! 🎯 
Love that you're building AI automations at DoneMaker. 
Want to grab coffee and compare co-op experiences? ☕"
```

**Action:** `send_message`

**Redis Instruction Published:**
```json
{
  "task_id": "playwright:message:2025-11-08T16:54:07.771611",
  "queue": "playwright:message",
  "instruction": {
    "action": "send_message",
    "profile_url": "https://www.linkedin.com/in/elrich-chen/",
    "message": "Hey Elrich! Saw you're in 2A too - same stream! 🎯 Love that you're building AI automations at DoneMaker. Want to grab coffee and compare co-op experiences? ☕",
    "timestamp": "2025-11-08T16:54:07.771611"
  },
  "status": "pending"
}
```

---

## Full Pipeline Flow

```
1. Playwright scrapes profile
   ↓
2. Profile data published to Redis queue: "profiles:scraped"
   ↓
3. Messaging Agent classifies:
   - Category: waterloo_student
   - Action: route_to_dating_agent
   ↓
4. Dating Agent processes:
   - Detects: Waterloo student ✅
   - Estimates stream: 2A
   - Compares with user stream: 1A
   - Decision: Different stream → connect_only
   ↓
5. Instruction published to Redis: "playwright:message"
   - Action: connect_only
   - Profile URL: https://www.linkedin.com/in/elrich-chen/
   ↓
6. Playwright consumes instruction and executes:
   - Sends connection request (no message)
```

---

## Terminal Feedback Summary

```
╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Messaging Agent] Classifying profile...                                  │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Classification ──────────────────────────────╮
│ 🏷️  CLASSIFIED: https://www.linkedin.com/in/elrich-chen/                    │
│    Category: waterloo_student                                                │
│    Confidence: 95.00%                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Dating Agent] Estimating Waterloo stream...                              │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────── Agent Action ────────────────────────────────╮
│ 🤖 [Dating Agent] Estimated stream: 2A                                      │
│    Confidence: 85.00%                                                        │
╰──────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────── Data Published ───────────────────────────────╮
│ 📤 PUBLISHED: connect_only to playwright:message                             │
│    {'action': 'connect_only', 'profile_url': '...'}                          │
╰──────────────────────────────────────────────────────────────────────────────╯

🎭 Playwright Instruction: connect_only
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key         ┃ Value                                    ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ action      │ connect_only                             │
│ profile_url │ https://www.linkedin.com/in/elrich-chen/ │
│ message     │                                          │
│ timestamp   │ 2025-11-08T16:54:07.771611               │
└─────────────┴──────────────────────────────────────────┘

✅ Completed profile_processing
   Different stream (2A vs 1A), connection queued
```

---

## Key Observations

1. **Data Format Handling:** ✅
   - Agents successfully convert array-based experience/education to strings
   - Bio and headline are properly extracted
   - URL is preserved for Playwright

2. **Classification Accuracy:** ✅
   - Correctly identifies Waterloo student (95% confidence)
   - Properly routes to Dating Agent

3. **Stream Detection:** ✅
   - Detects "2A" from education data
   - Correctly compares with user stream
   - Makes appropriate decision (connect vs message)

4. **Redis Integration:** ✅
   - Instructions properly formatted
   - Published to correct queue
   - Terminal feedback shows all actions

5. **Error Handling:** ✅
   - Falls back gracefully if API fails
   - Still publishes connection instruction
   - Terminal shows clear error messages

---

## Next Steps for Playwright

Playwright should:
1. Consume from `playwright:message` queue
2. Read instruction: `{"action": "connect_only", "profile_url": "..."}`
3. Navigate to profile URL
4. Click "Connect" button
5. Mark instruction as completed in Redis

