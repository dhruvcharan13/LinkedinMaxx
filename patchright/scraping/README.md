# LinkedIn Scraping Module

Find and classify LinkedIn profiles: Waterloo students and recruiters/founders.

## Main Script

**`find_profiles.py`** - Dual-target profile finder

Finds BOTH Waterloo students AND recruiters until both targets are met.

### Usage

```bash
cd patchright/scraping
python3 find_profiles.py
```

### How It Works

1. Asks for targets (e.g., 5 Waterloo + 3 Recruiters)
2. Scrolls LinkedIn feed
3. Classifies each profile as:
   - **Waterloo**: Has "waterloo" in education
   - **Recruiter**: Has recruiter/founder keywords in bio/title
   - **Other**: Neither
4. Saves immediately as found:
   - `waterloo_1.json`, `waterloo_2.json`, ...
   - `recruiter_1.json`, `recruiter_2.json`, ...
5. Continues until **BOTH** targets met

## Files

- `linkedin_scraper.py` - Core scraper class
- `profile_classifier.py` - Classifies profiles (waterloo/recruiter)
- `find_profiles.py` - Main dual-target scraper
- `stealth_utils.py` - Anti-detection utilities
- `find_waterloo_students.py` - Legacy single-target scraper

## Profile Classification

### Waterloo Detection
- Checks education for "waterloo", "uwaterloo", "university of waterloo"

### Recruiter Detection  
Keywords in bio/headline/experience:
- recruiter, talent acquisition, talent partner
- founder, co-founder, CEO
- hiring manager, head of talent
- startup founder

## Output Structure

```
scraped_data/
  session_TIMESTAMP/
    waterloo_1.json      {"Type": "waterloo", ...}
    waterloo_2.json
    recruiter_1.json     {"Type": "recruiter", ...}
    recruiter_2.json
    summary_all.json
    session_log.txt
```

## Example

```
Waterloo students (default: 5): 3
Recruiters/Founders (default: 3): 2

✓ Target: 3 Waterloo + 2 Recruiters
Will continue scraping until BOTH targets are met!
```

Script will find 3 Waterloo students AND 2 recruiters before stopping.

