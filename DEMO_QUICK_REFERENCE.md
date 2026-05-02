# 🚀 Try Demo - Quick Reference

## One Click Away From Plagiarism Detection!

### 👇 How to Try Demo

```
1. Start app:        python app.py
2. Open browser:     http://localhost:5000/plagiarism
3. Click button:     "🚀 Try Demo Now" (orange card)
4. Wait 2 seconds:   Report loads automatically
5. See results:      Plagiarism detection demo!
```

## 📊 What You'll See

### Summary Cards
- **HIGH_RISK: 1** (Student A1 & A2 - adjacent seats with similar answers)
- **LOW_RISK: 0**
- **SAMPLE_MATCH: 0**

### Seating Grid
```
A1[RED] A2[RED] A3    A4    ...
B1      B2      B3    B4    ...
...
```
Red = flagged seats (A1 & A2)

### Flagged Pairs Table
```
| Student A | Seat A | Student B | Seat B | Question | Similarity | Risk     |
|-----------|--------|-----------|--------|----------|------------|----------|
| Student A1| A1     | Student A2| A2     | Q1       | 95%        | HIGH_RISK|
```

### Features You Can Try
- ✅ View seating grid visualization
- ✅ See similarity percentages
- ✅ Click "📥 Export as PDF" button
- ✅ Go back and upload real data

## 🎓 Demo Data Explained

### Question 1: "What is AI?"

**Student A1** (Seat A1):
```
"Artificial Intelligence is the simulation of human intelligence 
processes by machines, especially computer systems. These processes 
include learning, reasoning, and self-correction."
```

**Student A2** (Seat A2) - Similar answer:
```
"AI is the simulation of human intelligence in machines. It includes 
learning and reasoning capabilities."
```

✅ **Result**: HIGH_RISK (95% similar + adjacent seats A1, A2)

**Student B1** (Seat B1) - Different answer:
```
"Artificial Intelligence refers to computer systems that can perform 
tasks requiring intelligence."
```

✅ **Result**: No plagiarism (different content from A1 & A2)

## 🎯 Why Demo is Useful

| Scenario | Benefit |
|----------|---------|
| **First time user** | See system in action immediately |
| **Testing features** | Try seating grid, visualization, PDF export |
| **Understanding results** | See HIGH_RISK example with real data |
| **Before uploading** | Understand report format first |
| **Demos to others** | Show system capability quickly |

## 🔄 After Demo - What's Next?

### Option 1: Upload Real Data
1. Go back (← link at bottom)
2. Click "📤 Upload Student Answers"
3. Upload your answer sheets
4. Check plagiarism with real data

### Option 2: Customize Demo
1. Edit `app.py` (line 230+)
2. Change student names, seats, answers
3. Refresh and try demo again

### Option 3: Try Sample Upload
1. Click "📚 Upload Sample Papers"
2. Upload model/reference answers
3. See sample matching in action

## ⚡ Key Differences: Demo vs Real Data

| Aspect | Demo | Real Upload |
|--------|------|-------------|
| **Time** | Instant | Depends on file size |
| **Setup** | None | Upload files + seats |
| **Data** | Pre-loaded | Your answers |
| **Purpose** | Learn system | Detect real plagiarism |

## 🆘 Troubleshooting Demo

### Demo button not visible?
→ Refresh page (Ctrl+F5)

### Demo crashes?
→ Make sure database exists: `plagiarism.db`

### No plagiarism detected?
→ Normal! Demo is designed to show HIGH_RISK for A1 & A2 only

### Want different results?
→ Edit `sample_student_data` in app.py and re-run

## 💡 Tips

- 💡 Try demo first to understand the system
- 💡 Then upload your real answer sheets
- 💡 Compare how real data looks different
- 💡 Use "Export PDF" to save reports
- 💡 Share demo report with others

## 🎨 Visual Location

On the Plagiarism Detection home page:

```
┌─────────────────────────────────────────────────────────┐
│                  Plagiarism Detection                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 🚀 TRY DEMO  │  │ 📤 Upload    │  │ 📚 Samples   │ │
│  │ [ORANGE]     │  │ [BLUE]       │  │ [BLUE]       │ │
│  │ ← CLICK HERE │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐                                      │
│  │ 🔎 Check     │                                      │
│  │ [BLUE]       │                                      │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

## 📝 What Gets Created in Demo

**In Database (plagiarism.db)**:
- 1 Exam: "Demo Exam - AI Course"
- 4 Students: A1, A2, B1, B2
- 12 Answers: 4 students × 3 questions
- 3 Sample Answers: Reference answers
- 1+ Plagiarism Flags: Detected issues

**Total**: ~20 database records created

## 🎬 Demo Lifecycle

```
Click "Try Demo"
    ↓
Database records created (exam, students, answers, samples)
    ↓
Plagiarism detection runs automatically
    ↓
Results saved to database
    ↓
Report page loads with results
    ↓
User sees HIGH_RISK detection for A1 & A2
    ↓
User can export PDF, view grid, etc.
    ↓
Next time user clicks "Try Demo" → Creates NEW fresh demo
```

---

**Status**: ✅ Ready to use!
**Time to see results**: ~2 seconds
**No files needed**: ✅ Instant demo
