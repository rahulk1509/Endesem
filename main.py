"""
AI Exam Paper Corrector - Main Application
==========================================
BUGS FIXED in this file:
1. use_sample() — reset self.current_image = None to clear stale PhotoImage reference.
2. load_image() — Image.Resampling.LANCZOS only exists in Pillow >= 9.1.
   Added hasattr() fallback for older Pillow versions.
"""
 
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
 
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from image_processing.ocr_engine import OCREngine
from grading_engine.grader import ExamGrader
from ai_algorithms.search.answer_search import AnswerSearcher
from ai_algorithms.bayesian.confidence_scorer import ConfidenceScorer
from gui.results_view import ResultsWindow
 
 
class AIExamCorrectorApp:
    """Main application window for AI Exam Corrector"""
 
    def __init__(self, root):
        self.root = root
        self.root.title("📝 AI Exam Paper Corrector - Phase 1")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
 
        self.ocr_engine = OCREngine()
        self.grader = ExamGrader()
        self.searcher = AnswerSearcher()
        self.confidence_scorer = ConfidenceScorer()
 
        self.current_image = None
        self.current_image_path = None
 
        self.setup_ui()
 
    def setup_ui(self):
        """Setup the user interface"""
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
 
        title_label = tk.Label(
            title_frame,
            text="📝 AI Exam Paper Corrector",
            font=('Helvetica', 20, 'bold'),
            fg='white', bg='#2c3e50'
        )
        title_label.pack(pady=15)
 
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
 
        # Left panel
        left_panel = tk.LabelFrame(
            main_frame, text="Upload Answer Sheet",
            font=('Helvetica', 12, 'bold'), bg='#f0f0f0'
        )
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
 
        self.image_frame = tk.Frame(left_panel, bg='#e0e0e0', width=400, height=400)
        self.image_frame.pack(padx=10, pady=10, fill='both', expand=True)
        self.image_frame.pack_propagate(False)
 
        self.image_label = tk.Label(
            self.image_frame,
            text="📸 Drop image here\nor click 'Browse' below",
            font=('Helvetica', 14), bg='#e0e0e0', fg='#666'
        )
        self.image_label.pack(expand=True)
 
        btn_frame = tk.Frame(left_panel, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=10, pady=10)
 
        tk.Button(
            btn_frame, text="📂 Browse Image",
            font=('Helvetica', 11), bg='#3498db', fg='white',
            padx=20, pady=8, command=self.browse_image
        ).pack(side='left', padx=5)
 
        tk.Button(
            btn_frame, text="📋 Use Sample",
            font=('Helvetica', 11), bg='#9b59b6', fg='white',
            padx=20, pady=8, command=self.use_sample
        ).pack(side='left', padx=5)
 
        # Right panel
        right_panel = tk.Frame(main_frame, bg='#f0f0f0', width=300)
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.pack_propagate(False)
 
        subject_frame = tk.LabelFrame(
            right_panel, text="Subject & Settings",
            font=('Helvetica', 11, 'bold'), bg='#f0f0f0'
        )
        subject_frame.pack(fill='x', pady=(0, 10))
 
        tk.Label(subject_frame, text="Subject:", bg='#f0f0f0').pack(anchor='w', padx=10, pady=(10, 0))
        self.subject_var = tk.StringVar(value="General")
        ttk.Combobox(
            subject_frame, textvariable=self.subject_var, width=25,
            values=["General", "Mathematics", "Science", "English", "Computer Science", "AI Course"]
        ).pack(padx=10, pady=5)
 
        tk.Label(subject_frame, text="Question Type:", bg='#f0f0f0').pack(anchor='w', padx=10, pady=(10, 0))
        self.qtype_var = tk.StringVar(value="Mixed")
        ttk.Combobox(
            subject_frame, textvariable=self.qtype_var, width=25,
            values=["Mixed", "MCQ Only", "Short Answer", "Math Problems", "Essay"]
        ).pack(padx=10, pady=5)
 
        algo_frame = tk.LabelFrame(
            right_panel, text="AI Algorithm (Unit I-IV)",
            font=('Helvetica', 11, 'bold'), bg='#f0f0f0'
        )
        algo_frame.pack(fill='x', pady=10)
 
        self.algo_var = tk.StringVar(value="A* Search")
        for text, value in [
            ("A* Search (Unit I)", "A* Search"),
            ("BFS Matching (Unit I)", "BFS"),
            ("CSP Rubric (Unit II)", "CSP"),
            ("Bayesian Scoring (Unit III)", "Bayesian"),
            ("Q-Learning (Unit IV)", "QLearning")
        ]:
            tk.Radiobutton(
                algo_frame, text=text, variable=self.algo_var,
                value=value, bg='#f0f0f0'
            ).pack(anchor='w', padx=10)
 
        tk.Button(
            right_panel, text="🔍 ANALYZE & GRADE",
            font=('Helvetica', 14, 'bold'), bg='#27ae60', fg='white',
            padx=20, pady=15, command=self.grade_paper
        ).pack(fill='x', pady=20)
 
        tk.Button(
            right_panel, text="🎯 Run Demo (No Image)",
            font=('Helvetica', 11), bg='#e74c3c', fg='white',
            padx=20, pady=10, command=self.run_demo
        ).pack(fill='x', pady=5)
 
        self.status_label = tk.Label(
            right_panel, text="Ready to grade...",
            font=('Helvetica', 10), fg='#666', bg='#f0f0f0'
        )
        self.status_label.pack(pady=10)
 
        info_frame = tk.LabelFrame(
            right_panel, text="About This Project",
            font=('Helvetica', 10, 'bold'), bg='#f0f0f0'
        )
        info_frame.pack(fill='both', expand=True, pady=10)
 
        tk.Label(
            info_frame,
            text="\nAI Exam Corrector uses:\n\n"
                 "📌 Unit I: Search Algorithms\n   - A*, BFS, DFS for matching\n\n"
                 "📌 Unit II: CSP\n   - Rubric constraints\n\n"
                 "📌 Unit III: Bayesian\n   - OCR confidence scoring\n\n"
                 "📌 Unit IV: Q-Learning\n   - Adaptive grading\n",
            justify='left', font=('Helvetica', 9), bg='#f0f0f0'
        ).pack(padx=10, pady=5)
 
    def browse_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Answer Sheet Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        )
        if filepath:
            self.load_image(filepath)
 
    def load_image(self, filepath):
        """
        BUG FIX 2: Image.Resampling.LANCZOS only exists in Pillow >= 9.1.
        Older versions expose it directly as Image.LANCZOS.
        """
        try:
            self.current_image_path = filepath
            image = Image.open(filepath)
            display_size = (380, 380)
            # FIX: safe fallback for older Pillow versions
            resample = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
            image.thumbnail(display_size, resample)
            self.current_image = ImageTk.PhotoImage(image)
            self.image_label.configure(image=self.current_image, text="")
            self.status_label.configure(text=f"Loaded: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {str(e)}")
 
    def use_sample(self):
        """
        BUG FIX 1: self.current_image was never reset to None here.
        If an image was previously loaded, the stale PhotoImage reference
        caused display glitches when switching to sample mode.
        """
        self.current_image_path = "SAMPLE"
        self.current_image = None       # FIX: clear stale reference
        self.image_label.configure(
            text="📋 Using Sample Data\n\n"
                 "Q1: What is AI?\nA: Artificial Intelligence\n\n"
                 "Q2: 2+2 = ?\nA: 4\n\n"
                 "Q3: Capital of India?\nA: New Delhi",
            image=""
        )
        self.status_label.configure(text="Sample data loaded")
 
    def grade_paper(self):
        if not self.current_image_path:
            messagebox.showwarning("Warning", "Please upload an image or use sample data first!")
            return
 
        self.status_label.configure(text="Processing...")
        self.root.update()
 
        try:
            algorithm = self.algo_var.get()
            subject = self.subject_var.get()
 
            if self.current_image_path == "SAMPLE":
                extracted_text = """
Q1: What is Artificial Intelligence?
A: AI is the simulation of human intelligence in machines.
 
Q2: Calculate: 15 + 27 = ?
A: 42
 
Q3: What is the capital of France?
A: Paris
 
Q4: Define BFS algorithm.
A: Breadth First Search explores all neighbors at current depth before moving to next level.
 
Q5: What is 2x + 3 = 11? Find x.
A: x = 4
"""
            else:
                extracted_text = self.ocr_engine.extract_text(self.current_image_path)
 
            results = self.grader.grade(extracted_text, algorithm=algorithm, subject=subject)
            self.show_results(results, algorithm)
 
        except Exception as e:
            messagebox.showerror("Error", f"Grading failed: {str(e)}")
            self.status_label.configure(text="Error occurred")
 
    def run_demo(self):
        self.use_sample()
        self.grade_paper()
 
    def show_results(self, results, algorithm):
        ResultsWindow(self.root, results, algorithm)
        self.status_label.configure(text="Grading complete!")
 
 
def main():
    root = tk.Tk()
    app = AIExamCorrectorApp(root)
    root.mainloop()
 
 
if __name__ == "__main__":
    main()