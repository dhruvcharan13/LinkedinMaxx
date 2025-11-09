# LinkedIn Automation Suite

Three modular functionalities for LinkedIn automation.

## 📁 Directory Structure

```
patchright/
├── scraping/          # Find & classify profiles
├── messaging/         # Send messages (placeholder)
├── posting/           # Create posts
└── shared/            # Shared utilities (future)
```

## 🔍 1. Scraping Module

**Location:** `scraping/`

Find Waterloo students AND recruiters/founders.

```bash
cd scraping
python3 find_profiles.py
```

**Features:**
- Dual targets: Waterloo + Recruiters
- Auto-classification
- Saves as `waterloo_1.json`, `recruiter_1.json`, etc.
- Won't stop until BOTH targets met

[Full documentation →](./scraping/README.md)

## 💬 2. Messaging Module

**Location:** `messaging/`

**Status:** Placeholder (not yet implemented)

**Planned features:**
- Send direct messages
- Send connection requests
- Message templates

## 📝 3. Posting Module

**Location:** `posting/`

Post text and images to LinkedIn.

```bash
cd posting
python3 linkedin_poster.py
```

**Features:**
- Post text
- Upload images
- Completely standalone

[Full documentation →](./posting/README.md)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install patchright pandas openpyxl numpy
patchright install chrome
```

### 2. Run Scraper

```bash
cd scraping
python3 find_profiles.py
```

Enter targets:
- Waterloo students: 5
- Recruiters: 3

### 3. Run Poster

```bash
cd posting
python3 linkedin_poster.py
```

Enter post text and optional image path.

## 📊 Output Example

After scraping:

```
scraped_data/
  session_20251108_170000/
    waterloo_1.json
    waterloo_2.json
    waterloo_3.json
    recruiter_1.json
    recruiter_2.json
    summary_all.json
    session_log.txt
```

## 🎯 Key Features

- **Modular:** Each function is independent
- **Persistent Login:** Browser remembers your session
- **Stealth:** Random delays, human-like behavior
- **Type Classification:** Auto-detects profile types
- **Dual Targets:** Scrape multiple categories at once

## 📖 Module Details

| Module | Status | Purpose |
|--------|--------|---------|
| Scraping | ✅ Complete | Find & classify profiles |
| Posting | ✅ Complete | Create LinkedIn posts |
| Messaging | ⏳ Placeholder | Send DMs & requests |

## 🔧 Tech Stack

- **Patchright:** Stealth web automation
- **Python 3.8+:** Core language
- **Pandas:** Data export
- **ChromeDriver:** Browser automation

## ⚠️ Notes

- First run: Manual login required
- After that: Browser remembers login
- All modules are independent
- Scraping module has built-in stealth features
