# LinkedIn Waterloo Student Finder

Simple scraper that automatically finds Waterloo students from your LinkedIn feed.

## ✨ Features

- **Auto-scrolling**: Browser scrolls automatically through your feed
- **Waterloo detection**: Finds students who went to University of Waterloo
- **Program extraction**: Identifies their program (Software Eng, CS, Math, etc.)
- **Multiple formats**: Saves as JSON, CSV, and Excel

## 🚀 Quick Start

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Run

```bash
python3 find_waterloo_students.py
```

### 3. What Happens

1. Browser opens
2. Log in to LinkedIn manually
3. Press Enter
4. **Browser scrolls automatically** (just watch!)
5. Finds 5 Waterloo students (or however many you want)
6. Saves data to `scraped_data/`

## 📊 Output

Files saved in `scraped_data/`:
- `waterloo_students_TIMESTAMP.json` - Full profile data
- `waterloo_students_TIMESTAMP.csv` - Spreadsheet
- `waterloo_students_TIMESTAMP.xlsx` - Excel file

### Data Collected

For each Waterloo student:
- Name
- Program (Software Engineering, Math, CS, etc.)
- Headline
- Location
- Bio
- Experience (with dates)
- Education
- Profile URL

## 💡 How It Works

1. Opens your LinkedIn feed
2. Scrolls automatically to load more profiles
3. Collects profile URLs
4. Visits each profile
5. Checks education for "Waterloo"
6. Saves Waterloo students
7. Stops when target reached (default: 5)

## ⚙️ Customize

When you run the script, it asks:

```
Find how many Waterloo students? (default: 5):
```

Just enter a number (e.g., `10`) or press Enter for 5.

## 🛡️ Safety

- Uses stealth browser (Patchright)
- Human-like delays
- Persistent session (stay logged in)
- No aggressive scraping
- Respects LinkedIn's structure

## 📁 Project Files

```
linkedin-scraper/
├── find_waterloo_students.py   ← Main script (RUN THIS!)
├── linkedin_scraper.py          ← Core scraper class
├── stealth_utils.py             ← Human-like behavior
├── requirements.txt             ← Dependencies
├── example_usage.py             ← More examples
└── scraped_data/                ← Output folder
    ├── waterloo_students_*.json
    ├── waterloo_students_*.csv
    └── waterloo_students_*.xlsx
```

## 🆘 Troubleshooting

### "Browser not opening"

Close all Chrome windows first:
```bash
pkill Chrome
python3 find_waterloo_students.py
```

### "No profiles found"

- Make sure you're logged into LinkedIn
- Check your feed has posts
- Try again later (feed updates)

### "Could not find Waterloo students"

- Your feed might not have Waterloo connections
- Try increasing the number: enter `10` or `20` when prompted
- Connect with more Waterloo people first

## 🎯 Example Session

```bash
$ python3 find_waterloo_students.py

============================================================
WATERLOO STUDENT FINDER
============================================================
Find how many Waterloo students? (default: 5): 5

✓ Will search for 5 Waterloo students

============================================================
SEARCHING FOR WATERLOO STUDENTS
============================================================
Scrolling through feed automatically...

[1/23] Checking profile... ✗ Not Waterloo
[2/23] Checking profile... ✓ WATERLOO! John Doe (Software Engineering) [1/5]
[3/23] Checking profile... ✗ Not Waterloo
[4/23] Checking profile... ✓ WATERLOO! Jane Smith (Mathematics) [2/5]
...

============================================================
✅ FOUND 5 WATERLOO STUDENTS!
============================================================

Profiles:
1. John Doe - Software Engineering
2. Jane Smith - Mathematics
3. Bob Chen - Computer Science
4. Alice Wong - Engineering
5. Mike Lee - Mathematics

✅ DONE!
Check the files in: scraped_data/
```

## 📚 Advanced Usage

Check `example_usage.py` for more ways to use the scraper:
- Scrape specific profile URLs
- Collect from feed without filtering
- Custom data extraction

## ⚠️ Legal Note

- Only scrape publicly available data
- Respect LinkedIn's Terms of Service
- For educational/personal use only
- Don't abuse or spam

## 🎉 That's It!

Simple, clean, effective. Just run:

```bash
python3 find_waterloo_students.py
```

And watch it find Waterloo students automatically! 🚀
