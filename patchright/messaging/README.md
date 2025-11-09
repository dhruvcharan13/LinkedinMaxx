# LinkedIn Messaging Module

Send direct messages and connection requests on LinkedIn with stealth measures.

## Features

- **Human-like typing**: Character-by-character typing with realistic delays
- **Stealth measures**: Random delays, smooth scrolling, browser behavior mimicking
- **Manual checkpoints**: Pause at key steps for verification
- **Persistent browser**: Keeps you logged in between sessions
- **Connection requests**: Send connection requests with optional notes

## Quick Start

### 1. Send a Test Message

```bash
cd messaging
python linkedin_messenger.py
```

This will:
1. Load `test_profile.json` (Dhruv Charan's profile)
2. Open browser and wait for manual login
3. Navigate to the profile
4. Click "Message" button
5. Type the message character-by-character
6. Send the message
7. Return to home page

### 2. Test Profile Data

Edit `test_profile.json` to change the default test profile:

```json
{
  "profile_url": "https://www.linkedin.com/in/dhruv-charan-89b1b5194/",
  "name": "Dhruv Charan",
  "message": "Hi Dhruv, I came across your profile and would love to connect!"
}
```

### 3. Use in Your Own Script

```python
from linkedin_messenger import LinkedInMessenger

with LinkedInMessenger(headless=False) as messenger:
    messenger.login(manual=True)
    
    # Send a message
    messenger.send_message(
        profile_url="https://www.linkedin.com/in/username/",
        message="Your message here"
    )
    
    # Or send a connection request
    messenger.send_connection_request(
        profile_url="https://www.linkedin.com/in/username/",
        note="Optional connection note"
    )
```

## How It Works

### Message Workflow

1. **Navigate to profile** - Goes to the LinkedIn profile URL
2. **Scroll briefly** - Simulates reading the profile (300-500px scroll)
3. **Click "Message"** - Finds and clicks the Message button
4. **Type message** - Types character-by-character with human-like delays:
   - 0.05-0.15s between characters
   - 0.2-0.5s between words
   - Occasional 0.5-1.2s "thinking" pauses (15% chance)
5. **Send** - Clicks the Send button
6. **Return home** - Navigates back to LinkedIn feed

### Manual Checkpoints

The script pauses at key moments and waits for you to press ENTER:
- After profile loads
- After message modal opens
- Before sending the message
- Option to keep browser open after completion

This gives you full control and lets you verify each step.

## Stealth Features

✅ **Character-by-character typing** with realistic delays  
✅ **Random delays** between all actions (0.5-3s)  
✅ **Smooth scrolling** to simulate reading  
✅ **bring_to_front()** before each action  
✅ **Manual intervention points** to avoid detection  
✅ **Persistent browser context** (stays logged in)

## Files

- `linkedin_messenger.py` - Main messaging class
- `test_profile.json` - Test profile data (Dhruv Charan)
- `message_templates.py` - (Future) Message templates
- `README.md` - This file

## Tips

1. **Always test with a dummy account first** (like Dhruv's profile in test_profile.json)
2. **Keep delays random** - Don't run multiple messages back-to-back
3. **Review before sending** - Use the manual checkpoints to verify everything
4. **Keep browser open** - After sending, you can verify the message was delivered

## Next Steps

- Add message templates for common scenarios
- Batch messaging with rate limiting
- Integration with scraping module (message Waterloo students/recruiters)
- Track sent messages and responses

