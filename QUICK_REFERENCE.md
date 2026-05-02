# 🚀 Flask Web App - Quick Reference

## ⚡ TL;DR - Get Started in 30 Seconds

```bash
# 1. Navigate to project
cd ai_exam_corrector

# 2. Install (if not done)
pip install -r requirements.txt

# 3. Run
python app.py

# 4. Open browser
http://localhost:5000
```

---

## 📋 What Was Added

| File/Folder | Purpose | Size |
|------------|---------|------|
| `app.py` | Flask server & routes | 165 lines |
| `templates/` | HTML pages | 4 files |
| `static/css/style.css` | Styling | 400 lines |
| `static/js/main.js` | Upload/grade logic | 150 lines |
| `static/js/results.js` | Results page | 50 lines |
| `WEBAPP_README.md` | Detailed docs | 180 lines |
| `FLASK_SETUP_GUIDE.md` | Setup guide | 200 lines |
| `setup.py` | Auto-install script | 20 lines |

---

## 🎯 Main Features

### Upload
- Drag & drop or click to browse
- Supported: PNG, JPG, JPEG, BMP, GIF (max 16MB)
- Live preview

### Grade
- Choose algorithm: A*, BFS, CSP, Bayesian, Q-Learning
- Select subject: General, Math, Science, English, CS, AI
- Pick question type: Mixed, MCQ, Short Answer, Math, Essay
- Get instant results

### Results
- Overall score with progress bar
- Question-by-question breakdown
- Student vs expected answers
- Similarity & confidence metrics
- Print or download report

---

## 🔌 API Endpoints

```
GET  /                    → Home page
POST /upload              → Upload image
POST /use-sample          → Load demo data
POST /grade               → Grade the paper
GET  /results             → Show results
GET  /api/status          → Check session status
POST /clear-session       → Clear session
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 in use | Edit `app.py`, change port to 5001 |
| Flask not found | Run: `pip install Flask` |
| Image upload fails | Check `uploads/` dir, file size < 16MB |
| Slow performance | Disable debug: `debug=False` in `app.py` |

---

## 📁 Project Structure

```
ai_exam_corrector/
├── app.py                    ← Flask app (NEW)
├── templates/                ← HTML files (NEW)
│   ├── index.html
│   ├── results.html
│   ├── 404.html
│   └── 500.html
├── static/                   ← CSS/JS (NEW)
│   ├── css/style.css
│   └── js/main.js, results.js
├── uploads/                  ← Uploaded images (NEW)
├── requirements.txt          ← Updated with Flask
├── main.py                   ← Tkinter GUI (still works)
├── grading_engine/
├── image_processing/
├── ai_algorithms/
└── [other files...]
```

---

## 🎨 Customization

### Change Theme Colors
Edit `static/css/style.css`:
```css
/* Primary color */
.btn-primary { background: #3498db; }

/* Dark header */
.navbar { background: #2c3e50; }
```

### Add New Subject
Edit `templates/index.html`:
```html
<option value="History">History</option>
```

### Change Port
Edit bottom of `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

---

## 🚀 Deploy to Production

### Using Gunicorn (recommended)
```bash
pip install gunicorn
gunicorn -w 4 app:app
```

### Using Flask's built-in server (for production warning)
Edit `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

### Cloud Platforms
- **Heroku**: Add `Procfile`, push to GitHub, deploy
- **AWS**: Use EC2 + Docker
- **DigitalOcean**: Droplet + Gunicorn + Nginx
- **PythonAnywhere**: Upload files + reload

---

## 📊 Features Comparison

| Feature | Web App | Desktop GUI |
|---------|---------|-----------|
| Interface | Modern web UI | Tkinter |
| Upload images | ✅ | ✅ |
| Sample data | ✅ | ✅ |
| Algorithm selection | ✅ | ✅ |
| Results display | ✅ | ✅ |
| Export reports | ✅ | Limited |
| Mobile friendly | ✅ | ❌ |
| Easy deploy | ✅ | ❌ |

---

## 💡 Pro Tips

1. **Debug JavaScript**: Open browser DevTools (F12)
2. **Check uploads**: See `uploads/` folder for uploaded images
3. **Monitor logs**: Flask shows request logs in terminal
4. **Cache busting**: Ctrl+Shift+R in browser to reload CSS/JS
5. **Test all algorithms**: Try each of the 5 algorithms

---

## 🆚 Run Both Versions

```bash
# Terminal 1
cd ai_exam_corrector
python app.py

# Terminal 2 (new terminal)
cd ai_exam_corrector
python main.py
```

Web app runs on http://localhost:5000
Desktop GUI opens in separate window

---

## 📞 Support

- Check `WEBAPP_README.md` for detailed documentation
- Check `FLASK_SETUP_GUIDE.md` for comprehensive setup
- Check original `README.md` for algorithm details
- View browser console (F12) for JavaScript errors
- Check terminal for Flask errors

---

## ✅ Everything Ready!

Your project now has:
- ✅ Full Flask web application
- ✅ Responsive modern UI
- ✅ File upload with drag & drop
- ✅ All algorithms integrated
- ✅ Beautiful results display
- ✅ Export functionality
- ✅ Error handling
- ✅ Complete documentation

**Start now**: `python app.py` → `http://localhost:5000` 🚀

---

*Last updated: 2026-05-02*
