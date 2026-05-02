# 🚀 Demo Feature - Instant Plagiarism Detection

## What's New?

Added a **"Try Demo"** button to instantly see plagiarism detection in action without uploading files!

## Quick Start

1. Go to: http://localhost:5000/plagiarism
2. Click: **"🚀 Try Demo Now"** (orange card with yellow background)
3. **Boom!** → Instant plagiarism report with demo data

## What the Demo Includes

### 🎓 Demo Exam
- **Name**: "Demo Exam - AI Course"
- **Subject**: AI Course
- **Students**: 4 (A1, A2, B1, B2)

### 👥 Sample Students
```
Student A1 (Seat A1) - Similar answers to A2
Student A2 (Seat A2) - Similar answers to A1 (adjacent seat) ← HIGH RISK
Student B1 (Seat B1) - Different answers
Student B2 (Seat B2) - Different answers
```

### 📝 Questions
```
Q1: What is Artificial Intelligence?
Q2: What is Machine Learning?
Q3: What is Deep Learning?
```

### 🎯 Expected Results
- **A1 & A2**: HIGH_RISK (similar answers + adjacent seats)
- **B1 & B2**: No plagiarism (different answers)
- **A1 & B1**: LOW_RISK (some similarity but not adjacent)

## How It Works

1. **Click "Try Demo"** → `/plagiarism/demo` route is called
2. **Auto-generates**:
   - Exam record in database
   - 4 students with realistic seats
   - Answers for 3 questions
   - Model/sample answers
3. **Auto-runs plagiarism detection**
4. **Shows full report** with:
   - Summary cards (HIGH/LOW/SAMPLE counts)
   - Seating grid with flagged pairs
   - Detailed plagiarism table
   - Export PDF button

## Demo Data Details

### Student Answers (Q1)

**Student A1 (Seat A1):**
```
"Artificial Intelligence is the simulation of human intelligence processes 
by machines, especially computer systems. These processes include learning, 
reasoning, and self-correction."
```

**Student A2 (Seat A2) - 95% Similar:**
```
"AI is the simulation of human intelligence in machines. It includes 
learning and reasoning capabilities."
```

✅ **Result**: HIGH_RISK (similar + adjacent seats A1/A2)

**Student B1 (Seat B1) - Different:**
```
"Artificial Intelligence refers to computer systems that can perform 
tasks requiring intelligence."
```

✅ **Result**: No plagiarism (different content)

### Model Answers

Provided for reference to show how sample matching works:
```
Q1: Artificial Intelligence is the simulation of human intelligence 
    processes by computers, including learning, reasoning, and problem-solving.

Q2: Machine Learning is a subset of AI that enables computers to learn 
    and improve from experience without being explicitly programmed.

Q3: Deep Learning uses artificial neural networks with multiple layers 
    to learn hierarchical representations of data.
```

## Benefits

✅ **No file upload needed** - Instant results
✅ **Realistic data** - Shows how plagiarism detection works
✅ **Multiple scenarios** - HIGH_RISK, LOW_RISK, no plagiarism
✅ **Full features** - See seating grid, visualization, PDF export
✅ **Learning tool** - Understand the system before uploading real data

## How to Use After Demo

1. **See the demo results** - Understand the report format
2. **Export the PDF** - See how PDF export looks
3. **Go back** - Upload your own answer sheets
4. **Compare** - See how real data looks different

## Code Location

### Route: `/plagiarism/demo`
**File**: `app.py` (around line 230)

**What it does**:
1. Creates Exam in database
2. Creates 4 Student records with seats
3. Creates StudentAnswer records (12 total: 4 students × 3 questions)
4. Creates SampleAnswer records (3: one per question)
5. Automatically runs plagiarism detection
6. Redirects to report page

### Template Update: `plagiarism_home.html`
**Added**: New card "🚀 Try Demo" as first card
**Styling**: Orange border, yellow background to stand out

## Customizing Demo Data

Want to change the demo data? Edit `app.py` in the `plagiarism_demo()` function:

```python
sample_student_data = [
    {
        'name': 'Student Name',
        'seat': 'A1',  # Change seat (A-F, 1-10)
        'answers': {
            'Q1': 'Your answer here',
            'Q2': 'Another answer',
            'Q3': 'More answers',
        }
    },
    # Add more students...
]
```

## Tips for Demo

1. **First time?** Click "Try Demo" to see the system in action
2. **Want different scenarios?** Modify the demo data in app.py
3. **Ready for real data?** Use "Upload Bulk" button
4. **Test sample matching?** See how model answers filter matches

## Demo Limitations

- ⚠️ Demo creates new exam each time (doesn't update existing)
- ⚠️ All demo data is temporary (unless you manually keep it)
- ✅ But you can see all features in action!

## Troubleshooting

### Demo button not appearing?
- Refresh the page (Ctrl+F5)
- Check Flask app is running
- Verify plagiarism_home.html was updated

### Demo crashes?
- Check database is working: `plagiarism.db` should exist
- Verify app.py was saved correctly
- Try clearing browser cache and reload

### No plagiarism detected in demo?
- This is normal! Demo has different answers for different seats
- A1 & A2 WILL show HIGH_RISK (similar + adjacent)
- B1 & B2 won't show plagiarism (different answers)

## Future Enhancements

Ideas for expanding demo:
- [ ] Multiple demo scenarios (different difficulty levels)
- [ ] Custom demo builder (configure your own demo)
- [ ] Compare different plagiarism levels
- [ ] Save demo as template

---

**The demo is your instant test drive of the plagiarism system!** 🚀
