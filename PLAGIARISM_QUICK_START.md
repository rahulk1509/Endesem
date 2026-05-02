# Plagiarism Detection - Quick Start Guide

## Installation (First Time Only)

```bash
cd ai_exam_corrector
pip install -r requirements.txt
```

## Start the Application

```bash
python app.py
```

Open browser: http://localhost:5000

## Using Plagiarism Detection

### Step 1: Go to Plagiarism Home
- Click **"🔍 Plagiarism Detection"** button on main page
- Or visit: http://localhost:5000/plagiarism

### Step 2: Upload Student Answers
1. Click **"📤 Upload Student Answers"**
2. Fill in exam name (e.g., "AI Course Final Exam")
3. Select up to 10 answer sheet files (PDF or TXT)
4. Enter seat number for each file:
   - Format: Row (A-F) + Column (1-10)
   - Examples: A1, B3, C5, F10
5. Click **"📤 Upload & Process"**

Example seating:
```
A1  A2  A3  A4  A5 ...
B1  B2  B3  B4  B5 ...
C1  C2  C3  C4  C5 ...
...
F1  F2  F3  F4  F5 ...
```

### Step 3: (Optional) Upload Sample Answers
1. Click **"📚 Upload Sample Papers"**
2. Select the exam from dropdown
3. Upload up to 10 model/reference answer papers
4. Click **"📚 Upload Samples"**

This helps filter out cases where students legitimately copy the official answer.

### Step 4: Check for Plagiarism
1. Go back to plagiarism home
2. Click **"🔍 Check"** next to your exam
3. System analyzes all answers and detects similar pairs
4. View the report showing:
   - **Summary cards:** Number of HIGH_RISK, LOW_RISK, SAMPLE_MATCH pairs
   - **Seating grid:** Visual representation with flagged pairs highlighted
   - **Detailed table:** Each flagged pair with similarity %

### Step 5: Export Report
- Click **"📥 Export as PDF"** to download the full report
- File saves as: `plagiarism_report_<exam_id>.pdf`

## Understanding Results

### Risk Levels

🔴 **HIGH_RISK** (Red)
- Similarity > 75% + Adjacent seats
- **Action:** Investigate potential cheating

🟠 **LOW_RISK** (Yellow)
- Similarity > 75% + Not adjacent
- **Action:** Review for accidental similarity

🔵 **SAMPLE_MATCH** (Blue)
- Both students copied the model answer (> 85% match)
- **Action:** Not flagged as plagiarism (legitimate)

### Similarity Score
- 0-50%: Different answers (not flagged)
- 50-75%: Similar but below threshold
- 75-100%: **FLAGGED** as similar

## Example Workflow

### Create Sample Answer Files

**File: student1.txt**
```
Q1: What is Artificial Intelligence?
A: Artificial Intelligence is the simulation of human intelligence processes by machines, particularly computer systems. These processes include learning, reasoning, and self-correction.

Q2: Define Machine Learning.
A: Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.
```

**File: student2.txt** (Similar answers, adjacent seat B1)
```
Q1: What is Artificial Intelligence?
A: AI refers to the simulation of human intelligence in computers. It includes learning and reasoning capabilities.

Q2: Define Machine Learning.
A: ML is part of AI where systems learn from data without explicit programming instructions.
```

### Expected Results
- **Q1 Similarity:** ~85% → Flagged
- **Q2 Similarity:** ~80% → Flagged
- **Seating:** A1 and B1 are adjacent → **HIGH_RISK** 🔴
- **Action:** Likely cheating

---

## Answer Sheet Format

Supported formats:

### PDF
- Text-based PDFs (will extract text from all pages)
- Scanned PDFs (if OCR enabled)

### TXT
- Plain text format
- Questions marked: Q1, Q2, Q3, etc.
- Answers marked: A:

### Recommended Format
```
Q1: What is the capital of France?
A: Paris is the capital of France.

Q2: What is 2 + 2?
A: 2 + 2 equals 4.

Q3: Define photosynthesis.
A: Photosynthesis is the process plants use to convert light energy into chemical energy.
```

## Troubleshooting

### No exams appear on home page
- Check that you've uploaded student answers first
- Database must exist: `plagiarism.db`

### PDF upload fails
- Ensure PDF has extractable text (not just images)
- Try converting to TXT instead

### Seat number error
- Format must be: Letter (A-F) + Number (1-10)
- Valid: A1, B3, F10
- Invalid: 1A, AA, 11

### PDF export fails
- On Windows, may need system dependencies for weasyprint
- Alternative: Use browser's print-to-PDF (Ctrl+P)

### Similarity score seems wrong
- Threshold is 75% (0.75)
- Scores below 75% are NOT flagged
- Scores calculated using TF-IDF cosine similarity

## Tips for Best Results

1. **Consistent Formatting:** Use Q1, Q2, Q3 format for all answer sheets
2. **Seat Accuracy:** Enter correct seat numbers (determines risk level)
3. **Model Answers:** Upload sample papers to reduce false positives
4. **Multiple Questions:** System analyzes each question separately
5. **Backup Results:** Export PDF after each check

## Database

- Location: `plagiarism.db` (project root)
- Type: SQLite (no external database needed)
- Auto-created on first use
- Tables: exams, students, student_answers, sample_answers, plagiarism_flags

## Links

- **Home:** http://localhost:5000
- **Plagiarism Detection:** http://localhost:5000/plagiarism
- **Upload Answers:** http://localhost:5000/plagiarism/upload-bulk
- **Upload Samples:** http://localhost:5000/plagiarism/upload-samples

## Support

For detailed documentation, see:
- `PLAGIARISM_FEATURE.md` - Full feature documentation
- `PLAGIARISM_COMPLETION_REPORT.md` - Implementation details
- `requirements.txt` - Dependencies

---

**Happy plagiarism checking! 🔍**
