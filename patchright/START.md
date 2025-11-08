# 🚀 START HERE

## One Command to Run:

```bash
python3 find_waterloo_students.py
```

That's it!

---

## What It Does:

1. Opens browser
2. You log in to LinkedIn
3. **Browser auto-scrolls** (you just watch!)
4. Finds 5 Waterloo students
5. Saves their profiles

---

## First Time Setup:

```bash
pip install -r requirements.txt
```

---

## Example Output:

```
Scrolling through feed automatically...

[1/23] Checking profile... ✗ Not Waterloo
[2/23] Checking profile... ✓ WATERLOO! John (Software Eng) [1/5]
[3/23] Checking profile... ✗ Not Waterloo
[4/23] Checking profile... ✓ WATERLOO! Jane (Math) [2/5]

✅ FOUND 5 WATERLOO STUDENTS!

Saved:
- waterloo_students_TIMESTAMP.json
- waterloo_students_TIMESTAMP.csv
- waterloo_students_TIMESTAMP.xlsx
```

---

## Files Explained:

- **`find_waterloo_students.py`** ← Run this!
- `linkedin_scraper.py` - Core scraper
- `stealth_utils.py` - Makes it look human
- `requirements.txt` - Dependencies

---

## That's It!

Super simple. Just run:

```bash
python3 find_waterloo_students.py
```

🎉

