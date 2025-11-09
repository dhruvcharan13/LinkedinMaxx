# Agent Output Format

## Message Format (Matches test_profile.json)

When agents generate messages, they are published to Redis in the following format:

### Redis Instruction Format

The instruction is wrapped in a standard Redis message structure:

```json
{
  "task_id": "playwright:message:2025-11-09T08:25:43.554393",
  "queue": "playwright:message",
  "instruction": {
    "profile_url": "https://linkedin.com/in/dhruv-charan",
    "name": "Dhruv Charan",
    "message": "Hi Dhruv, I came across your profile and would love to connect!",
    "action": "send_message",
    "timestamp": "2025-11-09T08:25:43.554390"
  },
  "timestamp": "2025-11-09T08:25:43.554393",
  "status": "pending"
}
```

### Inner Instruction Format (Matches test_profile.json)

The inner `instruction` object matches the format expected by Patchright's messaging module:

```json
{
  "profile_url": "https://linkedin.com/in/dhruv-charan",
  "name": "Dhruv Charan",
  "message": "Hi Dhruv, I came across your profile and would love to connect!",
  "action": "send_message",
  "timestamp": "2025-11-09T08:25:43.554390"
}
```

### Fields

- **profile_url** (required): LinkedIn profile URL
- **name** (required): Name of the profile owner
- **message** (required): Message text to send (empty string for connect_only)
- **action** (required): Either "send_message" or "connect_only"
- **timestamp** (optional): ISO timestamp

### Example: test_profile.json

```json
{
  "profile_url": "https://www.linkedin.com/in/dhruv-charan-89b1b5194/",
  "name": "Dhruv Charan",
  "message": "Hi Dhruv, I came across your profile and would love to connect! I'm impressed by your background and thought it would be great to connect and exchange ideas."
}
```

## Comment Format

Comments are published to Redis in a similar format:

```json
{
  "task_id": "playwright:comment:2025-11-09T08:25:43.554393",
  "queue": "playwright:comment",
  "instruction": {
    "post_url": "https://linkedin.com/feed/update/...",
    "comment": "Great post! Thanks for sharing.",
    "timestamp": "2025-11-09T08:25:43.554390"
  },
  "timestamp": "2025-11-09T08:25:43.554393",
  "status": "pending"
}
```

### Inner Instruction Format

```json
{
  "post_url": "https://linkedin.com/feed/update/...",
  "comment": "Great post! Thanks for sharing.",
  "timestamp": "2025-11-09T08:25:43.554390"
}
```

## How Agents Use This Format

### Messaging Agent

```python
# Publish message instruction (format matches test_profile.json)
name = profile_data.get("name", "LinkedIn User")
task_id = redis_client.queue_message_instruction(
    profile_url, 
    message, 
    "send_message", 
    name=name
)
```

### Dating Agent

```python
# Publish message instruction (format matches test_profile.json)
name = profile_data.get("name", "LinkedIn User")
task_id = redis_client.queue_message_instruction(
    profile_url, 
    pickup_line, 
    "send_message", 
    name=name
)
```

### Comment Agent

```python
# Publish comment instruction
task_id = redis_client.queue_comment_instruction(post_url, comment)
```

## Patchright Consumption

When Patchright consumes from Redis, it should access the `instruction` object:

```python
# Consume message instruction
instruction = redis_client.get_instruction("playwright:message")
profile_url = instruction["instruction"]["profile_url"]
name = instruction["instruction"]["name"]
message = instruction["instruction"]["message"]
action = instruction["instruction"]["action"]
```

This matches the format expected by `patchright/messaging/test_profile.json`.

