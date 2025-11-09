# LinkedIn Commenting Module

Post comments on LinkedIn posts with human-like behavior and stealth measures.

## Features

- **Human-like typing**: Character-by-character typing with realistic delays
- **Reading simulation**: Scrolls down to "read" post before commenting
- **Stealth measures**: Random delays, smooth scrolling, force clicks
- **Edge case handling**: Multiple selectors, fallback options, manual checkpoints
- **Persistent browser**: Keeps you logged in between sessions

## Quick Start

### 1. Post a Test Comment

```bash
cd commenting
python linkedin_commenter.py
```

This will:
1. Load `test_comment.json` (Dhruv's post)
2. Open browser and wait for manual login
3. Navigate to the post
4. Simulate reading the post (scroll down, pause, scroll up)
5. Click "Comment" button
6. Type the comment character-by-character
7. **Wait for you to press ENTER** before posting
8. Post the comment
9. Return to home page

### 2. Test Comment Data

Edit `test_comment.json` to change the default test:

```json
{
  "post_url": "https://www.linkedin.com/posts/...",
  "post_author": "Dhruv Charan",
  "comment": "Congrats on the win! DataWeave sounds like an amazing project..."
}
```

### 3. Use in Your Own Script

```python
from linkedin_commenter import LinkedInCommenter

with LinkedInCommenter(headless=False) as commenter:
    commenter.login(manual=True)
    
    commenter.post_comment(
        post_url="https://www.linkedin.com/posts/...",
        comment="Your comment here"
    )
```

## Workflow Details

### 1. Navigation
- Goes to post URL
- Waits 3 seconds for full page load

### 2. Reading Simulation (Stealth)
- Scrolls down 200-400px (random)
- Pauses 1.5-2.5s (simulating reading)
- Scrolls back to top smoothly

### 3. Comment Button
- Waits 0.5-1.0s before clicking
- Tries multiple selectors
- Uses `force=True` to bypass visibility checks

### 4. Typing
- Character-by-character with delays:
  - 0.05-0.15s between characters
  - 0.2-0.5s between words
  - Occasional 0.5-1.2s "thinking" pauses (15% chance)

### 5. Manual Checkpoint
- **Pauses and asks you to press ENTER before posting**
- Lets you review the typed comment

### 6. Post Button
- Waits 0.8-1.5s before clicking
- Force clicks to ensure success
- Waits 2-3s after posting

### 7. Return Home
- Navigates back to LinkedIn feed
- Keeps browser open for review

## Stealth Features

✅ **Human-like typing** with realistic pauses  
✅ **Reading simulation** before commenting  
✅ **Random delays** between all actions  
✅ **Smooth scrolling** animations  
✅ **Force clicks** to bypass visibility issues  
✅ **Persistent browser context** (stays logged in)  
✅ **Manual checkpoints** to avoid looking robotic

## Edge Cases Handled

### Comment Button Issues
- Multiple selectors tried
- Force click used
- Manual fallback if automation fails

### Comment Box Issues
- Waits 1-2s after clicking for box to appear
- Multiple input field selectors
- Continues even if click seems to fail

### Post Button Issues
- Waits for text to be fully typed
- Multiple selectors for Post button
- Force click with fallbacks

### Network/Load Issues
- 3 second wait after navigation
- Reasonable timeouts (5s per selector)
- Graceful handling of slow networks

## Files

- `linkedin_commenter.py` - Main commenter class
- `test_comment.json` - Test comment data (Dhruv's post)
- `README.md` - This file

## Tips

1. **Always test with a dummy post first** (like Dhruv's in test_comment.json)
2. **Review before posting** - Use the manual checkpoint to verify the comment
3. **Keep delays random** - Don't run multiple comments back-to-back
4. **Keep browser open** - After posting, verify the comment was successful

## Next Steps

- Add comment templates for common scenarios
- Batch commenting with rate limiting
- Integration with scraping module (comment on posts from scraped profiles)
- Track posted comments and responses
- Reply to existing comments

