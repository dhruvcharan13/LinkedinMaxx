# LinkedIn Posting Module

Post text and images to LinkedIn.

## Usage

```python
from posting.linkedin_poster import LinkedInPoster

# Create a post
with LinkedInPoster(headless=False) as poster:
    poster.login(manual=True)
    poster.create_post(
        text="Check out this amazing post!",
        image_path="photo.jpg"  # Optional
    )
```

## Running the Example

```bash
cd patchright/posting
python3 linkedin_poster.py
```

## Features

- ✅ Post text content
- ✅ Upload and post images
- ✅ Persistent login (stays logged in)
- ✅ Completely standalone (no scraping dependency)

## Notes

- First time: You'll need to log in manually
- After that: Browser remembers your login
- Supports JPG, PNG image formats

