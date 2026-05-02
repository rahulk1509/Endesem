# 🌐 AI Exam Paper Corrector - Web Application

This is a **Flask-based web version** of the AI Exam Corrector. It provides the same functionality as the Tkinter GUI but as a modern web application.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation & Setup

#### Option 1: Automatic Setup
```bash
cd ai_exam_corrector
python setup.py
```

#### Option 2: Manual Setup
```bash
cd ai_exam_corrector
pip install -r requirements.txt
```

### Run the Application

```bash
cd ai_exam_corrector
python app.py
```

You'll see:
```
Starting AI Exam Corrector Web Application...
Open http://localhost:5000 in your browser
```

Then open your browser and go to: **http://localhost:5000**

## 📁 New Project Structure

```
ai_exam_corrector/
├── app.py                          # Flask application (NEW)
├── main.py                         # Original Tkinter GUI (still available)
├── requirements.txt                # Updated with Flask dependencies
│
├── templates/                      # HTML templates (NEW)
│   ├── index.html                  # Home page
│   ├── results.html                # Results display
│   ├── 404.html                    # Error pages
│   └── 500.html
│
├── static/                         # Static files (NEW)
│   ├── css/
│   │   └── style.css               # Styling
│   └── js/
│       ├── main.js                 # Home page logic
│       └── results.js              # Results page logic
│
├── uploads/                        # Uploaded images (NEW - auto-created)
├── setup.py                        # Quick setup script (NEW)
│
├── image_processing/               # Existing modules
├── grading_engine/
├── ai_algorithms/
├── gui/
└── [other existing files]
```

## 🎯 Features

### Web Interface (New)
✅ **Image Upload** - Drag & drop or click to browse
✅ **Sample Data** - Test without uploading
✅ **Algorithm Selection** - Choose from 5 algorithms (A*, BFS, CSP, Bayesian, Q-Learning)
✅ **Subject Selection** - General, Mathematics, Science, English, Computer Science, AI Course
✅ **Question Type** - Mixed, MCQ, Short Answer, Math, Essay
✅ **Live Results** - Detailed question-by-question feedback
✅ **Print & Download** - Export grading reports
✅ **Responsive Design** - Works on desktop and mobile

### Still Available
✅ **Tkinter GUI** - Run `python main.py` for the desktop version
✅ **All AI Algorithms** - Same grading logic as before
✅ **Sample Data** - Built-in demo mode

## 🔧 Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify `app.py`:
```python
# Change the last line from:
app.run(debug=True, host='0.0.0.0', port=5000)

# To:
app.run(debug=True, host='0.0.0.0', port=5001)  # or any free port
```

### Flask Not Installing
If Flask won't install:
```bash
python -m pip install --upgrade pip
pip install Flask Werkzeug
```

### Image Upload Not Working
- Ensure the `uploads/` directory is writable
- Check file size (max 16MB)
- Supported formats: PNG, JPG, JPEG, BMP, GIF

## 📊 API Endpoints

The Flask app exposes these API endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Home page |
| `/upload` | POST | Upload image |
| `/use-sample` | POST | Load sample data |
| `/grade` | POST | Grade the paper |
| `/results` | GET | Display results |
| `/api/status` | GET | Get session status |
| `/clear-session` | POST | Clear session |

## 🎨 Customization

### Change Theme
Edit `static/css/style.css` to modify colors, fonts, etc.

### Modify Algorithms
Edit `ai_algorithms/` modules - same as before

### Add New Subject
Edit `templates/index.html` and add to the subject dropdown

## 🔄 Dual Mode

You can now run **both versions**:

```bash
# Terminal 1: Web version
cd ai_exam_corrector
python app.py

# Terminal 2: Desktop GUI (in another terminal)
cd ai_exam_corrector
python main.py
```

## 🐛 Debug Mode

The Flask app runs in debug mode by default. This means:
- ✅ Auto-reload on code changes
- ✅ Detailed error messages
- ✅ Debugger available
- ⚠️ Only for development (disable for production)

To disable debug mode, edit `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## 📚 Original Documentation

See `README.md` for original project details including:
- Algorithm explanations
- Lab experiments covered
- Presentation points

## 🎓 Project Info

- **Course**: Introduction to Artificial Intelligence
- **Deliverable**: End Semester Project
- **Version**: Phase 1 with Web Interface

---

**Happy Grading!** 📝✨
