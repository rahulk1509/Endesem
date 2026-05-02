# Plagiarism Detection Feature

## Overview
The AI Exam Corrector now includes a comprehensive plagiarism detection system designed to identify similar student answers, detect seating-based cheating patterns, and filter legitimate matches (sample paper copies).

## Features

### 1. **Bulk Upload** 📤
- Upload up to 10 student answer sheets at once (PDF or TXT)
- Specify each student's seat number (format: A1, B3, C5, etc.)
- Automatic text extraction from PDFs
- Question-answer parsing with regex

**Route:** `/plagiarism/upload-bulk`

### 2. **Sample Paper Upload** 📚
- Upload model answers (up to 10 files)
- Used as reference to distinguish plagiarism from legitimate sample copying
- Helps identify when students copy the official answer vs. each other

**Route:** `/plagiarism/upload-samples`

### 3. **Plagiarism Detection** 🔍
- **TF-IDF Similarity:** Cosine similarity > 0.75 (75%) flags answers as similar
- **Seating-Based Risk Analysis:**
  - **HIGH RISK:** Similar answers + adjacent seats (cheating likely)
  - **LOW RISK:** Similar answers + distant seats (accidental similarity)
  - **SAMPLE MATCH:** Both students copied the model answer (not plagiarism)
- Question-by-question analysis

**Route:** `/plagiarism/check/<exam_id>`

### 4. **Visual Report** 📊
- Seating grid with flagged pairs highlighted
- Summary cards: HIGH_RISK, LOW_RISK, SAMPLE_MATCH counts
- Detailed table with Student A/B, Seats, Similarity %, Risk Level
- Color-coded risk levels (Red=HIGH, Yellow=LOW, Blue=SAMPLE)

**Route:** `/plagiarism_report.html` (rendered from check route)

### 5. **PDF Export** 📥
- Export full report as PDF using weasyprint
- Includes: exam details, flagged pairs table, risk classifications

**Route:** `/plagiarism/export-pdf/<exam_id>`

## Database Schema

### Models (SQLAlchemy ORM)

#### Exam
- `id` (PK): Exam identifier
- `name`: Exam name (e.g., "AI Course Final")
- `date`: Timestamp
- `subject`: Subject (e.g., "AI Course")
- `total_students`: Count of students

#### Student
- `id` (PK)
- `exam_id` (FK): References Exam
- `name`: Student name
- `seat_number`: Format "A1", "B3", etc. (6 rows A-F, 10 columns 1-10)

#### StudentAnswer
- `id` (PK)
- `exam_id, student_id` (FKs)
- `question_number`: Q1, Q2, Q3, etc.
- `answer_text`: Student's answer

#### SampleAnswer
- `id` (PK)
- `exam_id` (FK)
- `question_number`
- `model_answer_text`: Official/model answer

#### PlagiarismFlag
- `id` (PK)
- `exam_id, student_a_id, student_b_id` (FKs)
- `question_number`
- `similarity_score`: 0.0-1.0
- `risk_level`: HIGH_RISK, LOW_RISK, or SAMPLE_MATCH

## Architecture

### Key Components

#### `plagiarism.py` - Core Detection Logic
- **PlagiarismDetector class**
  - `parse_seat(seat_number)` → (row, col) tuple
  - `are_neighbors(seat_a, seat_b)` → bool (Manhattan distance ≤ 1)
  - `compare_answers(answers_dict, seats_dict)` → list of flagged pairs
  - `check_sample_matching(answer_text, sample_answers)` → bool
  - `extract_questions_answers(text)` → dict {q_num: answer_text}

- **compute_risk_level()** function
  - Determines risk based on similarity + adjacency + sample matching

#### `models.py` - Database Models
- SQLAlchemy ORM models with relationships
- Cascade deletes to maintain referential integrity

#### `app.py` - Flask Routes
- `/plagiarism` → Home page with exam list
- `/plagiarism/upload-bulk` → Upload student answers
- `/plagiarism/upload-samples` → Upload model answers
- `/plagiarism/check/<exam_id>` → Run detection & render report
- `/plagiarism/export-pdf/<exam_id>` → Generate PDF

### Templates
- **plagiarism_home.html** - Navigation hub, exam list
- **upload_bulk.html** - Multi-file upload with seat numbers
- **upload_samples.html** - Model answer upload
- **plagiarism_report.html** - Results with seating grid & risk table

## Workflow

```
1. Go to /plagiarism (home page)
   ↓
2. Click "Upload Student Answers"
   → Fill exam name, select up to 10 files, enter seat numbers
   → PDFs auto-extract text
   ↓
3. Click "Upload Sample Papers"
   → Select the exam from dropdown
   → Upload up to 10 model answer files
   ↓
4. Click "Check Plagiarism" (from home page or exam list)
   → System compares all student answers question-by-question
   → Flags pairs with similarity > 75%
   → Assigns risk levels based on seating
   ↓
5. View report with:
   → Summary cards (HIGH/LOW/SAMPLE counts)
   → Seating grid with flagged pairs highlighted
   → Detailed table with all suspicious pairs
   ↓
6. Export as PDF using "📥 Export PDF" button
```

## Seat Parsing

Seats follow a standard classroom layout:
- **Rows:** A, B, C, D, E, F (6 rows)
- **Columns:** 1-10 (10 seats per row)
- **Format:** "A1", "B3", "F10", etc.

**Neighbor Detection:**
- Adjacent seats: distance ≤ 1 (horizontal, vertical, diagonal)
- A1 neighbors: A2, B1, B2
- A10 neighbors: A9, B9, B10
- C5 neighbors: B4, B5, B6, C4, C6, D4, D5, D6

## Risk Levels

### HIGH_RISK 🔴
- Similarity > 75% AND adjacent seats
- Indicates likely cheating (students sitting next to each other with similar answers)

### LOW_RISK 🟠
- Similarity > 75% AND NOT adjacent seats
- May indicate accidental similarity or copying from non-adjacent student

### SAMPLE_MATCH 🔵
- Both students have > 85% similarity to model answer
- Not flagged as plagiarism (legitimate matches)
- Only filtered if samples are uploaded

## Similarity Calculation

Uses **TF-IDF + Cosine Similarity** from scikit-learn:
1. Vectorize each answer using TF-IDF (removes stop words, lowercase)
2. Compute cosine similarity between all pairs (range: 0.0 to 1.0)
3. Flag pairs with score > 0.75 (configurable in PlagiarismDetector class)

Example:
```
Answer A: "The capital of France is Paris"
Answer B: "France's capital is Paris"
Similarity: ~0.92 (very similar, both mention France, capital, Paris)
```

## Sample Matching Logic

When checking plagiarism, for each flagged pair:
1. Get model answers for that question
2. Check student A's answer against model → similarity_to_model_a
3. Check student B's answer against model → similarity_to_model_b
4. If BOTH > 0.85 → mark as SAMPLE_MATCH (not plagiarism)
5. Otherwise → HIGH_RISK or LOW_RISK based on seating

This filters out cases where students legitimately copy the official answer.

## Text Extraction

### PDF Processing
- Uses PyPDF2 to extract text from all pages
- Handles scanned PDFs (text-based extraction, no OCR)

### Question-Answer Parsing
Regex pattern: `Q\d+:.*\nA:.*`
- Looks for "Q#:" followed by answer starting with "A:"
- Greedy matching to avoid missing the last answer
- Handles variations (Q1, Q01, q1, etc.)

Example input:
```
Q1: What is AI?
A: Artificial Intelligence is machine learning.

Q2: Define ML.
A: Machine Learning is learning from data.
```

Parsed output:
```python
{
    '1': 'Artificial Intelligence is machine learning.',
    '2': 'Machine Learning is learning from data.'
}
```

## Dependencies

### New Packages (added to requirements.txt)
- **PyPDF2** - PDF text extraction
- **scikit-learn** - TF-IDF vectorizer and cosine similarity
- **numpy** - Numerical operations
- **SQLAlchemy** - ORM
- **Flask-SQLAlchemy** - Flask-SQLAlchemy integration
- **weasyprint** - PDF generation

### Installation
```bash
pip install -r requirements.txt
```

## Database Location
- SQLite database: `plagiarism.db` (created on first run)
- Located in project root directory
- Auto-created when app starts

## Error Handling

### Common Issues

**No plagiarism routes found:**
- Check that models.py and plagiarism.py are in project root
- Verify Flask app context: `with app.app_context(): db.create_all()`

**PDF extraction fails:**
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Try with TXT files instead

**weasyprint PDF export fails on Windows:**
- May require system-level dependencies (libffi, Cairo)
- Fallback: Use browser's print-to-PDF functionality

**Seat number format invalid:**
- Must be format "A1", "B3", "F10" (letter + number)
- Row must be A-F, column must be 1-10

## Testing

### Manual Testing Steps

1. **Setup Database:**
   ```bash
   python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
   ```

2. **Start Flask app:**
   ```bash
   python app.py
   ```

3. **Test Bulk Upload:**
   - Go to http://localhost:5000/plagiarism
   - Click "Upload Bulk"
   - Create sample TXT files with Q/A format
   - Upload with seat numbers A1, A2, B1, etc.

4. **Test Plagiarism Detection:**
   - Create 2-3 answer files with similar answers
   - Assign them adjacent seats
   - Run plagiarism check
   - Verify HIGH_RISK flags

5. **Test Sample Matching:**
   - Upload model answer with same content as students
   - Run check
   - Verify marked as SAMPLE_MATCH (not HIGH_RISK)

## Future Enhancements

- [ ] Advanced seating layouts (flexible configuration)
- [ ] Batch plagiarism checks across multiple exams
- [ ] Configurable similarity thresholds per question
- [ ] Integration with OCR for handwritten exam sheets
- [ ] Plagiarism history and trends
- [ ] API endpoints for integration with other systems
- [ ] Student feedback reports (without flagging details)

## Support

For issues or questions about the plagiarism feature:
1. Check PLAGIARISM_FEATURE.md (this file)
2. Review error messages in Flask output
3. Check database: `plagiarism.db` should exist after first run
4. Verify all dependencies installed: `pip install -r requirements.txt`
