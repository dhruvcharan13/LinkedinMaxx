# Patchright Profile Format

## Profile Data Structure

Patchright scrapes profiles and classifies them with a `type` field. The backend agents use this classification to route profiles appropriately.

## Profile JSON Format

```json
{
  "url": "https://www.linkedin.com/in/elrich-chen/",
  "scraped_at": "2025-11-08T16:47:09.871850",
  "name": "Elrich Chen",
  "headline": "CS @ UWaterloo | AI automations...",
  "location": "He/Him",
  "bio": "...",
  "type": "waterloo",  // ← Classification from Patchright
  "experience": [...],
  "education": [...]
}
```

## Type Values

The `type` field can be one of:
- `"waterloo"` - Waterloo student
- `"recruiter"` - Recruiter
- `"cofounder"` or `"co-founder"` or `"founder"` - Co-founder/Founder
- `"other"` - Other (or not specified)

## Backend Handling

### If `type` is provided:

1. **`type: "waterloo"`**
   - Skips Messaging Agent classification
   - Routes directly to Dating Agent
   - Dating Agent processes for stream estimation and pickup line generation

2. **`type: "recruiter"`**
   - Uses Messaging Agent to generate recruiter message
   - Publishes message instruction to Redis

3. **`type: "cofounder"` or `"founder"`**
   - Uses Messaging Agent to generate co-founder message
   - Publishes message instruction to Redis

4. **`type: "other"` or no type**
   - Uses Messaging Agent to classify (LLM fallback)
   - Processes accordingly

### If `type` is NOT provided:

- Messaging Agent uses LLM to classify the profile
- Same workflow as before

## Benefits

- **Faster processing** - No LLM call needed if type is pre-classified
- **Cost savings** - Reduces API calls
- **More reliable** - Patchright can use rule-based classification
- **Flexible** - Still supports LLM classification as fallback

## Example Flow

### With Pre-classified Type

```
Patchright scrapes profile
  ↓
Adds type: "waterloo"
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

### Without Type (Fallback)

```
Patchright scrapes profile
  ↓
No type field
  ↓
Publishes to Redis: profiles:scraped
  ↓
Backend uses Messaging Agent to classify (LLM)
  ↓
Routes based on classification
  ↓
Processes accordingly
```

## Integration

No changes needed to Patchright publishing format - just add the `type` field to the profile data before publishing to Redis.

```python
profile_data = {
    "url": "...",
    "name": "...",
    "type": "waterloo",  # Add this field
    # ... rest of profile data
}

# Publish to Redis
publish_profile_to_redis(profile_data)
```

