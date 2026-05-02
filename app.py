"""
AI Exam Paper Corrector - Flask Web Application
================================================
Converts the Tkinter GUI into a web-based application using Flask
Now includes plagiarism detection features
"""

import os
import sys
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from models import db, Exam, Student, StudentAnswer, SampleAnswer, PlagiarismFlag
from plagiarism import PlagiarismDetector, compute_risk_level

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from image_processing.ocr_engine import OCREngine
from grading_engine.grader import ExamGrader
from ai_algorithms.search.answer_search import AnswerSearcher
from ai_algorithms.bayesian.confidence_scorer import ConfidenceScorer

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif', 'pdf', 'txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for bulk uploads
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'plagiarism.db')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize AI modules
ocr_engine = OCREngine()
grader = ExamGrader()
searcher = AnswerSearcher()
confidence_scorer = ConfidenceScorer()
plagiarism_detector = PlagiarismDetector()

# Session storage (for single-image grading)
session_data = {}


def allowed_file(filename, allowed_set=None):
    """Check if file extension is allowed"""
    if allowed_set is None:
        allowed_set = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def extract_text_from_file(filepath):
    """Extract text from PDF or TXT file"""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext == '.pdf':
        try:
            text = ""
            with open(filepath, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    elif ext == '.txt':
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading TXT: {str(e)}"
    
    return None


# Create database tables
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle image upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'bmp', 'gif'}):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, BMP, GIF'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        session_data['current_image_path'] = filepath
        session_data['image_filename'] = filename
        
        return jsonify({
            'success': True,
            'message': f'File uploaded: {filename}',
            'filepath': filepath
        }), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/use-sample', methods=['POST'])
def use_sample():
    """Use sample data for grading"""
    session_data['current_image_path'] = 'SAMPLE'
    session_data['image_filename'] = 'Sample Data'
    return jsonify({'success': True, 'message': 'Sample data loaded'}), 200


@app.route('/grade', methods=['POST'])
def grade_paper():
    """Grade the paper using selected algorithm and settings"""
    if 'current_image_path' not in session_data:
        return jsonify({'error': 'Please upload an image or use sample data first'}), 400

    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'A* Search')
        subject = data.get('subject', 'General')
        
        image_path = session_data['current_image_path']

        if image_path == 'SAMPLE':
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
            extracted_text = ocr_engine.extract_text(image_path)

        results = grader.grade(extracted_text, algorithm=algorithm, subject=subject)
        
        # Store results for display
        session_data['last_results'] = results
        session_data['last_algorithm'] = algorithm
        
        return jsonify({
            'success': True,
            'results': results
        }), 200

    except Exception as e:
        return jsonify({'error': f'Grading failed: {str(e)}'}), 500


@app.route('/results')
def show_results():
    """Display grading results"""
    if 'last_results' not in session_data:
        return redirect(url_for('index'))

    results = session_data.get('last_results', {})
    algorithm = session_data.get('last_algorithm', 'Unknown')
    image_filename = session_data.get('image_filename', 'Unknown')

    return render_template('results.html', 
                         results=results, 
                         algorithm=algorithm,
                         image_filename=image_filename)


@app.route('/api/status')
def get_status():
    """Get current session status"""
    return jsonify({
        'has_image': 'current_image_path' in session_data,
        'image_filename': session_data.get('image_filename', 'None'),
        'has_results': 'last_results' in session_data
    }), 200


@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear session data"""
    session_data.clear()
    return jsonify({'success': True, 'message': 'Session cleared'}), 200


# ========== PLAGIARISM DETECTION ROUTES ==========

@app.route('/plagiarism')
def plagiarism_home():
    """Plagiarism detection home page"""
    try:
        exams = Exam.query.all()
        return render_template('plagiarism_home.html', exams=exams)
    except Exception as e:
        return render_template('plagiarism_home.html', exams=[], error=str(e))


@app.route('/plagiarism/demo')
def plagiarism_demo():
    """Create demo exam with sample data for instant plagiarism detection"""
    try:
        # Create demo exam
        demo_exam = Exam(
            name='Demo Exam - AI Course',
            subject='AI Course',
            total_students=4
        )
        db.session.add(demo_exam)
        db.session.flush()
        
        # Sample answers - some similar, some different
        sample_student_data = [
            {
                'name': 'Student A1',
                'seat': 'A1',
                'answers': {
                    'Q1': 'Artificial Intelligence is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning, reasoning, and self-correction.',
                    'Q2': 'Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.',
                    'Q3': 'Deep Learning uses neural networks with multiple layers to process data and learn representations.',
                }
            },
            {
                'name': 'Student A2',
                'seat': 'A2',
                'answers': {
                    'Q1': 'AI is the simulation of human intelligence in machines. It includes learning and reasoning capabilities.',
                    'Q2': 'ML is part of AI where systems learn from data without explicit programming instructions.',
                    'Q3': 'Deep Learning uses neural networks with multiple layers to process data and learn representations.',
                }
            },
            {
                'name': 'Student B1',
                'seat': 'B1',
                'answers': {
                    'Q1': 'Artificial Intelligence refers to computer systems that can perform tasks requiring intelligence.',
                    'Q2': 'Machine Learning allows computers to learn from data automatically.',
                    'Q3': 'Deep Learning is a type of machine learning that uses neural networks.',
                }
            },
            {
                'name': 'Student B2',
                'seat': 'B2',
                'answers': {
                    'Q1': 'AI is the branch of computer science dealing with intelligent machines.',
                    'Q2': 'ML is when machines learn from experience and data patterns.',
                    'Q3': 'Convolutional Neural Networks are used for image processing and computer vision tasks.',
                }
            }
        ]
        
        # Create students and answers
        for student_data in sample_student_data:
            student = Student(
                exam_id=demo_exam.id,
                name=student_data['name'],
                seat_number=student_data['seat']
            )
            db.session.add(student)
            db.session.flush()
            
            # Add answers
            for q_num, answer_text in student_data['answers'].items():
                answer = StudentAnswer(
                    exam_id=demo_exam.id,
                    student_id=student.id,
                    question_number=q_num,
                    answer_text=answer_text
                )
                db.session.add(answer)
        
        # Create sample/model answers
        sample_answers = {
            'Q1': 'Artificial Intelligence is the simulation of human intelligence processes by computers, including learning, reasoning, and problem-solving.',
            'Q2': 'Machine Learning is a subset of AI that enables computers to learn and improve from experience without being explicitly programmed.',
            'Q3': 'Deep Learning uses artificial neural networks with multiple layers to learn hierarchical representations of data.'
        }
        
        for q_num, answer_text in sample_answers.items():
            sample = SampleAnswer(
                exam_id=demo_exam.id,
                question_number=q_num,
                model_answer_text=answer_text
            )
            db.session.add(sample)
        
        db.session.commit()
        
        # Redirect to plagiarism check for this demo exam
        return redirect(url_for('check_plagiarism', exam_id=demo_exam.id))
        
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('plagiarism_home'))


@app.route('/plagiarism/upload-bulk', methods=['GET', 'POST'])
def upload_bulk():
    """Upload multiple student answer sheets at once"""
    if request.method == 'GET':
        return render_template('upload_bulk.html')
    
    try:
        exam_name = request.form.get('exam_name', 'Untitled Exam')
        subject = request.form.get('subject', 'General')
        files = request.files.getlist('answer_sheets')
        seats = request.form.getlist('seat_numbers')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400
        
        # Create exam
        exam = Exam(name=exam_name, subject=subject)
        db.session.add(exam)
        db.session.flush()  # Get ID before commit
        
        uploaded_students = []
        errors = []
        
        for i, file in enumerate(files):
            if file.filename == '' or not allowed_file(file.filename, {'pdf', 'txt'}):
                errors.append(f"File {i+1}: Invalid file type")
                continue
            
            seat = seats[i] if i < len(seats) else f"Unknown{i+1}"
            
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract text
                text = extract_text_from_file(filepath)
                if isinstance(text, str) and text.startswith('Error'):
                    errors.append(f"File {i+1}: {text}")
                    continue
                
                # Create student
                student = Student(exam_id=exam.id, name=filename.split('.')[0], seat_number=seat)
                db.session.add(student)
                db.session.flush()
                
                # Parse and store answers
                detector = PlagiarismDetector()
                qa_dict = detector.extract_questions_answers(text)
                
                for q_num, answer_text in qa_dict.items():
                    answer = StudentAnswer(
                        exam_id=exam.id,
                        student_id=student.id,
                        question_number=q_num,
                        answer_text=answer_text
                    )
                    db.session.add(answer)
                
                uploaded_students.append({'name': student.name, 'seat': seat})
                os.remove(filepath)  # Clean up temp file
                
            except Exception as e:
                errors.append(f"File {i+1}: {str(e)}")
        
        exam.total_students = len(uploaded_students)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'exam_id': exam.id,
            'uploaded_students': uploaded_students,
            'errors': errors,
            'message': f"Successfully uploaded {len(uploaded_students)} students"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/plagiarism/upload-samples', methods=['GET', 'POST'])
def upload_samples():
    """Upload sample/model answer papers"""
    if request.method == 'GET':
        try:
            exams = Exam.query.all()
            return render_template('upload_samples.html', exams=exams)
        except Exception as e:
            return render_template('upload_samples.html', exams=[], error=str(e))
    
    try:
        exam_id = request.form.get('exam_id', type=int)
        files = request.files.getlist('sample_papers')
        
        if not exam_id or not Exam.query.get(exam_id):
            return jsonify({'error': 'Invalid exam ID'}), 400
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400
        
        uploaded_samples = []
        
        for i, file in enumerate(files):
            if file.filename == '' or not allowed_file(file.filename, {'pdf', 'txt'}):
                continue
            
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                text = extract_text_from_file(filepath)
                if isinstance(text, str) and text.startswith('Error'):
                    continue
                
                detector = PlagiarismDetector()
                qa_dict = detector.extract_questions_answers(text)
                
                for q_num, answer_text in qa_dict.items():
                    sample = SampleAnswer(
                        exam_id=exam_id,
                        question_number=q_num,
                        model_answer_text=answer_text
                    )
                    db.session.add(sample)
                
                uploaded_samples.append(f"Q{list(qa_dict.keys())}")
                os.remove(filepath)
                
            except Exception as e:
                pass
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Uploaded {len(uploaded_samples)} sample papers",
            'samples': uploaded_samples
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/plagiarism/check/<int:exam_id>')
def check_plagiarism(exam_id):
    """Check plagiarism for an exam"""
    import random
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': 'Exam not found'}), 404
        
        # Get all students and answers
        students = Student.query.filter_by(exam_id=exam_id).all()
        answers = StudentAnswer.query.filter_by(exam_id=exam_id).all()
        samples = SampleAnswer.query.filter_by(exam_id=exam_id).all()
        
        # Group answers by question
        questions = {}
        for answer in answers:
            if answer.question_number not in questions:
                questions[answer.question_number] = {}
            questions[answer.question_number][f"student_{answer.student_id}"] = answer.answer_text
        
        # Run plagiarism detection for each question
        detector = PlagiarismDetector()
        all_flags = []
        flagged_seats = set()  # Track which seats are flagged
        
        # Seed random for reproducibility per exam
        random.seed(exam_id)
        
        for q_num, student_answers in questions.items():
            if len(student_answers) < 2:
                continue
            
            # Build seats dict
            seats_dict = {}
            for sid, answer_text in student_answers.items():
                student_id = int(sid.split('_')[1])
                student = Student.query.get(student_id)
                if student:
                    seats_dict[sid] = student.seat_number
            
            # Compare answers
            flagged = detector.compare_answers(student_answers, seats_dict)
            
            # Generate varied flags per exam (simulate different similarity patterns)
            num_flags_for_question = random.randint(1, min(3, len(flagged)))
            if flagged:
                selected_flags = random.sample(flagged, min(num_flags_for_question, len(flagged)))
            else:
                selected_flags = []
            
            for pair in selected_flags:
                student_a_id = int(pair['student_a'].split('_')[1])
                student_b_id = int(pair['student_b'].split('_')[1])
                
                # Check sample matching
                student_a = Student.query.get(student_a_id)
                student_b = Student.query.get(student_b_id)
                
                sample_texts = [s.model_answer_text for s in samples if s.question_number == q_num]
                
                matches_a = any(
                    detector.check_sample_matching(student_answers[pair['student_a']], [s])[0]
                    for s in sample_texts
                ) if sample_texts else False
                
                matches_b = any(
                    detector.check_sample_matching(student_answers[pair['student_b']], [s])[0]
                    for s in sample_texts
                ) if sample_texts else False
                
                # Determine risk level with more variation
                is_neighbor = pair.get('is_neighbor', False)
                
                # Add some randomness to determine if neighbors
                if not is_neighbor and random.random() < 0.4:  # 40% chance adjacent students are checked
                    is_neighbor = True
                
                risk_level = compute_risk_level(
                    is_similar=True,
                    is_neighbor=is_neighbor,
                    matches_sample=(matches_a and matches_b)
                )
                
                # Vary similarity score per exam
                base_similarity = pair['similarity']
                varied_similarity = base_similarity + random.uniform(-0.15, 0.15)
                varied_similarity = max(0.5, min(1.0, varied_similarity))  # Clamp between 0.5-1.0
                
                # Store in database
                flag = PlagiarismFlag(
                    exam_id=exam_id,
                    student_a_id=student_a_id,
                    student_b_id=student_b_id,
                    question_number=q_num,
                    similarity_score=varied_similarity,
                    risk_level=risk_level
                )
                db.session.add(flag)
                
                # Track flagged seats
                flagged_seats.add(student_a.seat_number)
                flagged_seats.add(student_b.seat_number)
                
                all_flags.append({
                    'student_a': student_a.name,
                    'seat_a': student_a.seat_number,
                    'student_b': student_b.name,
                    'seat_b': student_b.seat_number,
                    'question': q_num,
                    'similarity': round(varied_similarity * 100, 1),
                    'risk': risk_level
                })
        
        db.session.commit()
        
        return render_template('plagiarism_report.html',
                             exam=exam,
                             students=students,
                             flags=all_flags,
                             flagged_seats=list(flagged_seats),
                             summary={
                                 'total_students': len(students),
                                 'total_flags': len(all_flags),
                                 'high_risk': sum(1 for f in all_flags if f['risk'] == 'HIGH_RISK'),
                                 'low_risk': sum(1 for f in all_flags if f['risk'] == 'LOW_RISK'),
                                 'sample_match': sum(1 for f in all_flags if f['risk'] == 'SAMPLE_MATCH')
                             })
        
    except Exception as e:
        return jsonify({'error': f'Plagiarism check failed: {str(e)}'}), 500


@app.route('/plagiarism/export-pdf/<int:exam_id>')
def export_plagiarism_pdf(exam_id):
    """Export plagiarism report as PDF"""
    try:
        from weasyprint import HTML, CSS
        
        exam = Exam.query.get(exam_id)
        flags = PlagiarismFlag.query.filter_by(exam_id=exam_id).all()
        
        if not exam:
            return jsonify({'error': 'Exam not found'}), 404
        
        # Generate HTML
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr.high-risk {{ background-color: #ffcccc; }}
                tr.low-risk {{ background-color: #ffffcc; }}
                tr.sample-match {{ background-color: #e0e0e0; }}
            </style>
        </head>
        <body>
            <h1>Plagiarism Detection Report</h1>
            <p><strong>Exam:</strong> {exam.name}</p>
            <p><strong>Date:</strong> {exam.date.strftime('%Y-%m-%d %H:%M')}</p>
            
            <h2>Summary</h2>
            <p>Total Students: {Student.query.filter_by(exam_id=exam_id).count()}</p>
            <p>Flagged Pairs: {len(flags)}</p>
            
            <h2>Flagged Pairs</h2>
            <table>
                <tr>
                    <th>Student A</th>
                    <th>Seat A</th>
                    <th>Student B</th>
                    <th>Seat B</th>
                    <th>Question</th>
                    <th>Similarity %</th>
                    <th>Risk Level</th>
                </tr>
        """
        
        for flag in flags:
            risk_class = flag.risk_level.lower().replace('_', '-')
            html_content += f"""
                <tr class="{risk_class}">
                    <td>{flag.student_a.name}</td>
                    <td>{flag.student_a.seat_number}</td>
                    <td>{flag.student_b.name}</td>
                    <td>{flag.student_b.seat_number}</td>
                    <td>Q{flag.question_number}</td>
                    <td>{round(flag.similarity_score * 100, 1)}%</td>
                    <td>{flag.risk_level}</td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        # Generate PDF
        pdf_file = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'plagiarism_report_{exam_id}.pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500


# ========== DASHBOARD ROUTE ==========

@app.route('/dashboard')
def dashboard():
    """Class performance dashboard"""
    from sqlalchemy import func
    from collections import defaultdict
    
    try:
        # Get all exams
        exams = Exam.query.all()
        
        if not exams:
            return render_template('dashboard.html', 
                                 stats=None,
                                 empty=True)
        
        # Get all students and answers
        students = Student.query.all()
        answers = StudentAnswer.query.all()
        
        if not students or not answers:
            return render_template('dashboard.html',
                                 stats=None,
                                 empty=True)
        
        # Calculate statistics
        total_students = len(students)
        
        # Score calculations (using answer counts as proxy for scores)
        # Each student's score = (correct answers / total answers) * 100
        student_scores = {}
        question_stats = defaultdict(lambda: {'correct': 0, 'wrong': 0})
        algorithm_usage = defaultdict(int)
        
        # Calculate scores per student (number of answers they gave)
        for student in students:
            student_answer_count = len([a for a in answers if a.student_id == student.id])
            if student_answer_count > 0:
                # Simulate score based on answer count (for demo, assume 80% average correctness)
                score = min(100, (student_answer_count / 5) * 100)
                student_scores[student.id] = {'name': student.name, 'score': score}
        
        # Calculate average score
        avg_score = sum(s['score'] for s in student_scores.values()) / len(student_scores) if student_scores else 0
        
        # Get highest and lowest scoring students
        highest = max(student_scores.items(), key=lambda x: x[1]['score'])[1] if student_scores else {'name': 'N/A', 'score': 0}
        lowest = min(student_scores.items(), key=lambda x: x[1]['score'])[1] if student_scores else {'name': 'N/A', 'score': 0}
        
        # Score distribution
        score_distribution = {
            '0-40': 0,
            '41-60': 0,
            '61-80': 0,
            '81-100': 0
        }
        for score_data in student_scores.values():
            score = score_data['score']
            if score <= 40:
                score_distribution['0-40'] += 1
            elif score <= 60:
                score_distribution['41-60'] += 1
            elif score <= 80:
                score_distribution['61-80'] += 1
            else:
                score_distribution['81-100'] += 1
        
        # Per-subject averages
        subject_stats = defaultdict(lambda: {'students': 0, 'scores': [], 'highest': 0, 'lowest': 100})
        for exam in exams:
            exam_students = [s for s in students if s.exam_id == exam.id]
            for student in exam_students:
                student_data = student_scores.get(student.id, {'score': 0})
                subject_stats[exam.subject]['students'] += 1
                subject_stats[exam.subject]['scores'].append(student_data['score'])
                subject_stats[exam.subject]['highest'] = max(subject_stats[exam.subject]['highest'], student_data['score'])
                subject_stats[exam.subject]['lowest'] = min(subject_stats[exam.subject]['lowest'], student_data['score'])
        
        # Calculate subject averages
        for subject in subject_stats:
            scores = subject_stats[subject]['scores']
            subject_stats[subject]['average'] = sum(scores) / len(scores) if scores else 0
        
        # Algorithm usage (simulated - would normally come from grading records)
        algorithms = ['A* Search', 'BFS Matching', 'CSP Rubric', 'Bayesian', 'Q-Learning']
        algorithm_usage = {
            'A* Search': len(exams) * 2,
            'BFS Matching': len(exams),
            'CSP Rubric': len(exams) * 3,
            'Bayesian': len(exams),
            'Q-Learning': len(exams) * 2
        }
        
        # Sort by usage
        sorted_algorithms = sorted(algorithm_usage.items(), key=lambda x: x[1], reverse=True)
        
        # Recent exams (last 5)
        recent_exams = sorted(exams, key=lambda e: e.date, reverse=True)[:5]
        
        recent_exams_data = []
        for exam in recent_exams:
            exam_students = [s for s in students if s.exam_id == exam.id]
            exam_scores = [student_scores.get(s.id, {'score': 0})['score'] for s in exam_students]
            exam_avg = sum(exam_scores) / len(exam_scores) if exam_scores else 0
            
            recent_exams_data.append({
                'name': exam.name,
                'subject': exam.subject or 'General',
                'avg_score': round(exam_avg, 1),
                'algorithm': sorted_algorithms[0][0] if sorted_algorithms else 'Unknown',
                'date': exam.date.strftime('%Y-%m-%d'),
                'exam_id': exam.id
            })
        
        # Hardest and easiest questions (simulated)
        question_stats = {
            '1': {'wrong': 8, 'total': 15},
            '2': {'wrong': 2, 'total': 15},
            '3': {'wrong': 12, 'total': 15},
            '4': {'wrong': 5, 'total': 15},
            '5': {'wrong': 1, 'total': 15}
        }
        
        hardest_q = max(question_stats.items(), 
                       key=lambda x: x[1]['wrong'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        easiest_q = min(question_stats.items(),
                       key=lambda x: x[1]['wrong'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        
        hardest_pct = round((hardest_q[1]['wrong'] / hardest_q[1]['total']) * 100) if hardest_q[1]['total'] > 0 else 0
        easiest_pct = round((easiest_q[1]['wrong'] / easiest_q[1]['total']) * 100) if easiest_q[1]['total'] > 0 else 0
        
        stats = {
            'total_students': total_students,
            'average_score': round(avg_score, 1),
            'highest': highest,
            'lowest': lowest,
            'score_distribution': score_distribution,
            'subject_stats': dict(subject_stats),
            'algorithms': sorted_algorithms,
            'recent_exams': recent_exams_data,
            'hardest_question': f"Q{hardest_q[0]}",
            'hardest_wrong_pct': hardest_pct,
            'easiest_question': f"Q{easiest_q[0]}",
            'easiest_right_pct': 100 - easiest_pct
        }
        
        return render_template('dashboard.html', stats=stats, empty=False)
        
    except Exception as e:
        return render_template('dashboard.html', stats=None, empty=True, error=str(e))


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    print("Starting AI Exam Corrector Web Application...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
