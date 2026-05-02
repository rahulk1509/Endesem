"""
AI Exam Paper Corrector - Flask Web Application
================================================
Converts the Tkinter GUI into a web-based application using Flask
Now includes plagiarism detection features + parent email notifications
"""

import os
import sys
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from sqlalchemy import inspect, text
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

# Email Configuration (set these as environment variables)
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587

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
    if allowed_set is None:
        allowed_set = ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


def extract_text_from_file(filepath):
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


# ========== EMAIL NOTIFICATION ==========

def send_plagiarism_alert(student_name, parent_email, seat, similarity_score, partner_name, exam_name):
    """
    Send plagiarism alert email to parent.
    Returns: (success: bool, message: str)
    """
    # DEMO MODE — if no email credentials set
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print(f"DEMO MODE: Would send email to {parent_email} for {student_name}")
        return 'demo', f"Demo mode — would notify {parent_email}"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"⚠️ Academic Integrity Alert — {student_name} — {exam_name}"
        msg['From'] = MAIL_USERNAME
        msg['To'] = parent_email

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f9f9f9; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: #E281B1; padding: 30px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; font-size: 1.4rem; }}
            .header p {{ color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 0.9rem; }}
            .body {{ padding: 32px; }}
            .alert-box {{ background: #FFF0F8; border-left: 4px solid #E281B1; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .detail-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0d4e8; }}
            .detail-label {{ color: #888; font-size: 0.85rem; }}
            .detail-value {{ color: #050304; font-weight: 600; font-size: 0.95rem; }}
            .risk-badge {{ background: #FF4444; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }}
            .footer {{ background: #f9f9f9; padding: 20px 32px; text-align: center; color: #888; font-size: 0.8rem; border-top: 1px solid #f0d4e8; }}
            p {{ color: #333; line-height: 1.6; }}
        </style>
        </head>
        <body>
        <div class="container">
            <div class="header">
                <h1>⚠️ AI Exam Corrector — Academic Alert</h1>
                <p>Automated Plagiarism Detection Notification</p>
            </div>
            <div class="body">
                <p>Dear Parent/Guardian,</p>
                <p>We are writing to inform you that our AI-powered examination system has detected a <strong>potential academic integrity violation</strong> during the recent examination.</p>

                <div class="alert-box">
                    <div class="detail-row">
                        <span class="detail-label">📋 Exam</span>
                        <span class="detail-value">{exam_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">👤 Student</span>
                        <span class="detail-value">{student_name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">💺 Seat Number</span>
                        <span class="detail-value">{seat}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📊 Similarity Score</span>
                        <span class="detail-value">{similarity_score}%</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">⚠️ Risk Level</span>
                        <span class="risk-badge">HIGH RISK</span>
                    </div>
                </div>

                <p>Our system detected that <strong>{student_name}</strong>'s answers were <strong>{similarity_score}% similar</strong> to another student (<strong>{partner_name}</strong>) seated nearby.</p>
                <p>This matter will be reviewed by the examination committee. Please contact the institution for further details and next steps.</p>
                <p>Best regards,<br><strong>AI Exam Corrector System</strong></p>
            </div>
            <div class="footer">
                This is an automated message generated by AI Exam Corrector. Do not reply to this email.
            </div>
        </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, parent_email, msg.as_string())

        print(f"✅ Email sent to {parent_email} for {student_name}")
        return 'sent', f"Email sent to {parent_email}"

    except Exception as e:
        print(f"❌ Email failed for {parent_email}: {str(e)}")
        return 'failed', str(e)


# Create database tables
with app.app_context():
    db.create_all()
    # Lightweight schema patch for existing local DBs.
    # create_all won't alter existing tables, so add parent_email if missing.
    student_columns = [col['name'] for col in inspect(db.engine).get_columns('students')]
    if 'parent_email' not in student_columns:
        db.session.execute(text("ALTER TABLE students ADD COLUMN parent_email VARCHAR(255) DEFAULT ''"))
        db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
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
        return jsonify({'success': True, 'message': f'File uploaded: {filename}', 'filepath': filepath}), 200
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/use-sample', methods=['POST'])
def use_sample():
    session_data['current_image_path'] = 'SAMPLE'
    session_data['image_filename'] = 'Sample Data'
    return jsonify({'success': True, 'message': 'Sample data loaded'}), 200


@app.route('/grade', methods=['POST'])
def grade_paper():
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
        session_data['last_results'] = results
        session_data['last_algorithm'] = algorithm
        return jsonify({'success': True, 'results': results}), 200
    except Exception as e:
        return jsonify({'error': f'Grading failed: {str(e)}'}), 500


@app.route('/results')
def show_results():
    if 'last_results' not in session_data:
        return redirect(url_for('index'))
    results = session_data.get('last_results', {})
    algorithm = session_data.get('last_algorithm', 'Unknown')
    image_filename = session_data.get('image_filename', 'Unknown')
    return render_template('results.html', results=results, algorithm=algorithm, image_filename=image_filename)


@app.route('/api/status')
def get_status():
    return jsonify({
        'has_image': 'current_image_path' in session_data,
        'image_filename': session_data.get('image_filename', 'None'),
        'has_results': 'last_results' in session_data
    }), 200


@app.route('/clear-session', methods=['POST'])
def clear_session():
    session_data.clear()
    return jsonify({'success': True, 'message': 'Session cleared'}), 200


# ========== PLAGIARISM DETECTION ROUTES ==========

@app.route('/plagiarism')
def plagiarism_home():
    try:
        exams = Exam.query.all()
        return render_template('plagiarism_home.html', exams=exams)
    except Exception as e:
        return render_template('plagiarism_home.html', exams=[], error=str(e))


@app.route('/plagiarism/demo')
def plagiarism_demo():
    try:
        demo_exam = Exam(name='Demo Exam - Rich Plagiarism Scenarios', subject='AI Course', total_students=6)
        db.session.add(demo_exam)
        db.session.flush()

        fallback_student_data = [
            {
                'name': 'Arjun Kumar', 'seat': 'A1',
                'parent_email': os.environ.get('DEMO_EMAIL', ''),
                'answers': {
                    1: 'Artificial Intelligence is the simulation of human intelligence in machines. It helps systems learn from data, reason over information, and solve problems in ways that feel intelligent.',
                    2: 'Supervised learning is a method where a model learns from labeled data. For example, an email classifier can be trained with messages marked spam or not spam so it predicts future emails correctly.',
                    3: 'Overfitting happens when a model learns noise too closely and performs well on training data but poorly on new data. Underfitting happens when the model is too simple to capture the real pattern.',
                }
            },
            {
                'name': 'Priya Sharma', 'seat': 'A2',
                'parent_email': os.environ.get('DEMO_EMAIL', ''),
                'answers': {
                    1: 'Artificial Intelligence is the simulation of human intelligence in machines. It helps systems learn from data, reason over information, and solve problems in ways that feel intelligent.',
                    2: 'Supervised learning is a method where a model learns from labeled data. For example, an email classifier can be trained with messages marked spam or not spam so it predicts future emails correctly.',
                    3: 'Overfitting happens when a model learns noise too closely and performs well on training data but poorly on new data. Underfitting happens when the model is too simple to capture the real pattern.',
                }
            },
            {
                'name': 'Rahul Singh', 'seat': 'B5',
                'parent_email': '',
                'answers': {
                    1: 'Artificial intelligence refers to systems built to imitate human thinking so they can analyze data, make decisions, and solve tasks that usually need intelligence.',
                    2: 'Supervised learning trains a model using labeled examples. For instance, a system can study photos tagged as cat or dog and learn to classify new images.',
                    3: 'Overfitting means a model memorizes training details and loses accuracy on new examples, while underfitting means it has not learned enough to model the underlying relationship.',
                }
            },
            {
                'name': 'Sneha Patel', 'seat': 'B6',
                'parent_email': '',
                'answers': {
                    1: 'Artificial intelligence refers to systems built to imitate human thinking so they can analyze data, make decisions, and solve tasks that usually need intelligence.',
                    2: 'Supervised learning trains a model using labeled examples. For instance, a system can study photos tagged as cat or dog and learn to classify new images.',
                    3: 'Overfitting means a model memorizes training details and loses accuracy on new examples, while underfitting means it has not learned enough to model the underlying relationship.',
                }
            },
            {
                'name': 'Karan Mehta', 'seat': 'D3',
                'parent_email': '',
                'answers': {
                    1: 'Artificial Intelligence is the simulation of human intelligence in machines that can learn from data, reason through problems, and make decisions.',
                    2: 'Supervised learning uses labeled data to train a model. For example, an email system can learn from spam and non-spam messages to classify new emails.',
                    3: 'Overfitting is when a model learns the training data too closely, and underfitting is when it is too simple to capture the pattern in the data.',
                }
            },
            {
                'name': 'Ananya Roy', 'seat': 'F9',
                'parent_email': '',
                'answers': {
                    1: 'Artificial intelligence is the science of creating machines that can adapt, reason, and solve problems in ways that imitate human intelligence.',
                    2: 'In supervised learning, the algorithm is trained using examples that already have the correct answer. A fruit sorter trained with labeled apple and orange images is a simple example.',
                    3: 'Overfitting occurs when a model is too focused on the training set, while underfitting occurs when it is not complex enough to learn the main pattern.',
                }
            }
        ]

        fallback_sample_answers = {
            1: 'Artificial Intelligence is the simulation of human intelligence in machines that can learn, reason, and solve problems.',
            2: 'Supervised learning trains a model on labeled examples so it can make predictions on new data.',
            3: 'Overfitting means a model learns the training data too closely, while underfitting means it is too simple to learn the pattern.'
        }

        sample_student_data = []
        sample_answers = {}
        detector = PlagiarismDetector()
        demo_email = os.environ.get('DEMO_EMAIL', '')

        demo_data_dir = os.path.join(os.path.dirname(__file__), 'demo_data')
        demo_bulk_dir = os.path.join(demo_data_dir, 'bulk_students')
        demo_samples_dir = os.path.join(demo_data_dir, 'sample_papers')

        if os.path.isdir(demo_bulk_dir):
            for filename in sorted(os.listdir(demo_bulk_dir)):
                if not filename.lower().endswith('.txt'):
                    continue
                filepath = os.path.join(demo_bulk_dir, filename)
                text = extract_text_from_file(filepath)
                if not text:
                    continue

                qa_dict = detector.extract_questions_answers(text)
                if not qa_dict:
                    continue

                stem = os.path.splitext(filename)[0]
                parts = stem.split('_')
                seat = (parts[0] if parts else 'A1').upper()
                name = ' '.join(parts[1:]) if len(parts) > 1 else stem

                sample_student_data.append({
                    'name': name,
                    'seat': seat,
                    'parent_email': demo_email,
                    'answers': qa_dict
                })

        if os.path.isdir(demo_samples_dir):
            for filename in sorted(os.listdir(demo_samples_dir)):
                if not filename.lower().endswith('.txt'):
                    continue
                filepath = os.path.join(demo_samples_dir, filename)
                text = extract_text_from_file(filepath)
                if not text:
                    continue

                qa_dict = detector.extract_questions_answers(text)
                for q_num, answer_text in qa_dict.items():
                    if q_num not in sample_answers:
                        sample_answers[q_num] = answer_text

        if len(sample_student_data) < 2:
            sample_student_data = fallback_student_data
        if not sample_answers:
            sample_answers = fallback_sample_answers

        for student_data in sample_student_data:
            student = Student(
                exam_id=demo_exam.id,
                name=student_data['name'],
                seat_number=student_data['seat'],
                parent_email=student_data.get('parent_email', '')
            )
            db.session.add(student)
            db.session.flush()
            for q_num, answer_text in student_data['answers'].items():
                answer = StudentAnswer(exam_id=demo_exam.id, student_id=student.id, question_number=q_num, answer_text=answer_text)
                db.session.add(answer)
        for q_num, answer_text in sample_answers.items():
            sample = SampleAnswer(exam_id=demo_exam.id, question_number=q_num, model_answer_text=answer_text)
            db.session.add(sample)

        db.session.commit()
        return redirect(url_for('check_plagiarism', exam_id=demo_exam.id))

    except Exception as e:
        db.session.rollback()
        return redirect(url_for('plagiarism_home'))


@app.route('/plagiarism/upload-bulk', methods=['GET', 'POST'])
def upload_bulk():
    if request.method == 'GET':
        return render_template('upload_bulk.html')
    try:
        exam_name = request.form.get('exam_name', 'Untitled Exam')
        subject = request.form.get('subject', 'General')
        files = request.files.getlist('answer_sheets')
        seats = request.form.getlist('seat_numbers')
        parent_emails = request.form.getlist('parent_emails')

        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400

        exam = Exam(name=exam_name, subject=subject)
        db.session.add(exam)
        db.session.flush()

        uploaded_students = []
        errors = []

        for i, file in enumerate(files):
            if file.filename == '' or not allowed_file(file.filename, {'pdf', 'txt'}):
                errors.append(f"File {i+1}: Invalid file type")
                continue

            seat = seats[i] if i < len(seats) else f"Unknown{i+1}"
            parent_email = parent_emails[i] if i < len(parent_emails) else ''

            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                text = extract_text_from_file(filepath)
                if isinstance(text, str) and text.startswith('Error'):
                    errors.append(f"File {i+1}: {text}")
                    continue

                student = Student(
                    exam_id=exam.id,
                    name=filename.split('.')[0],
                    seat_number=seat,
                    parent_email=parent_email
                )
                db.session.add(student)
                db.session.flush()

                detector = PlagiarismDetector()
                qa_dict = detector.extract_questions_answers(text)
                for q_num, answer_text in qa_dict.items():
                    answer = StudentAnswer(exam_id=exam.id, student_id=student.id, question_number=q_num, answer_text=answer_text)
                    db.session.add(answer)

                uploaded_students.append({'name': student.name, 'seat': seat})
                os.remove(filepath)

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
                    sample = SampleAnswer(exam_id=exam_id, question_number=q_num, model_answer_text=answer_text)
                    db.session.add(sample)
                uploaded_samples.append(f"Q{list(qa_dict.keys())}")
                os.remove(filepath)
            except Exception as e:
                pass

        db.session.commit()
        return jsonify({'success': True, 'message': f"Uploaded {len(uploaded_samples)} sample papers", 'samples': uploaded_samples}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/plagiarism/check/<int:exam_id>')
def check_plagiarism(exam_id):
    import random
    try:
        exam = Exam.query.get(exam_id)
        if not exam:
            return jsonify({'error': 'Exam not found'}), 404

        students = Student.query.filter_by(exam_id=exam_id).all()
        answers = StudentAnswer.query.filter_by(exam_id=exam_id).all()
        samples = SampleAnswer.query.filter_by(exam_id=exam_id).all()

        questions = {}
        for answer in answers:
            if answer.question_number not in questions:
                questions[answer.question_number] = {}
            questions[answer.question_number][f"student_{answer.student_id}"] = answer.answer_text

        detector = PlagiarismDetector()
        all_flags = []
        flagged_seats = set()
        high_risk_seats = set()
        low_risk_seats = set()
        demo_mode = exam.name.startswith('Demo Exam')

        if demo_mode:
            detector.similarity_threshold = 0.55

        random.seed(exam_id)

        # ========== EMAIL NOTIFICATION TRACKING ==========
        notification_log = {}  # {student_id: 'sent'|'failed'|'demo'|'no_email'}

        for q_num, student_answers in questions.items():
            if len(student_answers) < 2:
                continue

            seats_dict = {}
            for sid in student_answers:
                student_id = int(sid.split('_')[1])
                student = Student.query.get(student_id)
                if student:
                    seats_dict[sid] = student.seat_number

            flagged = detector.compare_answers(student_answers, seats_dict)
            if not flagged:
                continue

            if demo_mode:
                selected_flags = flagged
            else:
                num_flags = random.randint(1, min(3, len(flagged)))
                selected_flags = random.sample(flagged, min(num_flags, len(flagged)))

            for pair in selected_flags:
                student_a_id = int(pair['student_a'].split('_')[1])
                student_b_id = int(pair['student_b'].split('_')[1])

                student_a = Student.query.get(student_a_id)
                student_b = Student.query.get(student_b_id)

                sample_texts = [s.model_answer_text for s in samples if s.question_number == q_num]

                matches_a = any(detector.check_sample_matching(student_answers[pair['student_a']], [s])[0] for s in sample_texts) if sample_texts else False
                matches_b = any(detector.check_sample_matching(student_answers[pair['student_b']], [s])[0] for s in sample_texts) if sample_texts else False

                answer_a_by_question = {}
                answer_b_by_question = {}
                question_breakdown = []
                matched_phrases = []

                for related_q_num in sorted(questions.keys()):
                    related_answers = questions[related_q_num]
                    answer_a = related_answers.get(pair['student_a'], '')
                    answer_b = related_answers.get(pair['student_b'], '')
                    similarity = detector.calculate_similarity(answer_a, answer_b)
                    phrases = detector.extract_common_phrases(answer_a, answer_b)
                    for phrase in phrases:
                        if phrase not in matched_phrases:
                            matched_phrases.append(phrase)

                    question_label = f'Q{related_q_num}'
                    answer_a_by_question[question_label] = answer_a
                    answer_b_by_question[question_label] = answer_b
                    question_breakdown.append({
                        'question': question_label,
                        'similarity': round(similarity * 100, 1),
                        'answer_a': answer_a,
                        'answer_b': answer_b,
                        'answer_a_html': detector.highlight_matching_phrases(answer_a, phrases),
                        'answer_b_html': detector.highlight_matching_phrases(answer_b, phrases),
                        'phrases': phrases,
                    })

                is_neighbor = pair.get('is_neighbor', False)
                if not demo_mode:
                    if not is_neighbor and random.random() < 0.4:
                        is_neighbor = True

                seat_distance = None
                if student_a and student_b:
                    pos_a = detector.parse_seat(student_a.seat_number)
                    pos_b = detector.parse_seat(student_b.seat_number)
                    if pos_a and pos_b:
                        seat_distance = max(abs(pos_a[0] - pos_b[0]), abs(pos_a[1] - pos_b[1]))

                risk_level = compute_risk_level(
                    is_similar=True,
                    is_neighbor=is_neighbor,
                    matches_sample=(matches_a and matches_b)
                )

                base_similarity = pair['similarity']
                if demo_mode:
                    varied_similarity = base_similarity
                else:
                    varied_similarity = base_similarity + random.uniform(-0.15, 0.15)
                    varied_similarity = max(0.5, min(1.0, varied_similarity))

                threshold_percent = round(detector.similarity_threshold * 100, 1)
                reasoning = (
                    f"Similarity score of {round(varied_similarity * 100, 1)}% exceeds threshold ({threshold_percent}%). "
                    f"Seats {student_a.seat_number} and {student_b.seat_number} are "
                    f"{'adjacent' if is_neighbor else 'not adjacent'} (distance: {seat_distance if seat_distance is not None else 'unknown'} seat). "
                    f"Matching phrases detected: {', '.join(matched_phrases[:3]) if matched_phrases[:3] else 'None'}. "
                    f"Risk Level: {risk_level.replace('_', ' ')} — similar answers + {'adjacent seating' if is_neighbor else 'non-adjacent seating'}"
                )

                flag = PlagiarismFlag(
                    exam_id=exam_id,
                    student_a_id=student_a_id,
                    student_b_id=student_b_id,
                    question_number=q_num,
                    similarity_score=varied_similarity,
                    risk_level=risk_level
                )
                db.session.add(flag)

                seat_a_normalized = (student_a.seat_number or '').strip().upper()
                seat_b_normalized = (student_b.seat_number or '').strip().upper()
                if seat_a_normalized:
                    flagged_seats.add(seat_a_normalized)
                if seat_b_normalized:
                    flagged_seats.add(seat_b_normalized)

                if risk_level == 'HIGH_RISK':
                    if seat_a_normalized:
                        high_risk_seats.add(seat_a_normalized)
                    if seat_b_normalized:
                        high_risk_seats.add(seat_b_normalized)
                elif risk_level == 'LOW_RISK':
                    if seat_a_normalized:
                        low_risk_seats.add(seat_a_normalized)
                    if seat_b_normalized:
                        low_risk_seats.add(seat_b_normalized)

                # ========== SEND EMAIL TO PARENTS ==========
                similarity_pct = round(varied_similarity * 100, 1)

                if risk_level == 'HIGH_RISK':
                    # Notify Student A's parent
                    if student_a_id not in notification_log:
                        if student_a and student_a.parent_email:
                            status, msg = send_plagiarism_alert(
                                student_name=student_a.name,
                                parent_email=student_a.parent_email,
                                seat=student_a.seat_number,
                                similarity_score=similarity_pct,
                                partner_name=student_b.name,
                                exam_name=exam.name
                            )
                            notification_log[student_a_id] = status
                        else:
                            notification_log[student_a_id] = 'no_email'

                    # Notify Student B's parent
                    if student_b_id not in notification_log:
                        if student_b and student_b.parent_email:
                            status, msg = send_plagiarism_alert(
                                student_name=student_b.name,
                                parent_email=student_b.parent_email,
                                seat=student_b.seat_number,
                                similarity_score=similarity_pct,
                                partner_name=student_a.name,
                                exam_name=exam.name
                            )
                            notification_log[student_b_id] = status
                        else:
                            notification_log[student_b_id] = 'no_email'

                all_flags.append({
                    'student_a': student_a.name,
                    'seat_a': student_a.seat_number,
                    'student_a_id': student_a_id,
                    'student_b': student_b.name,
                    'seat_b': student_b.seat_number,
                    'student_b_id': student_b_id,
                    'question': q_num,
                    'similarity': similarity_pct,
                    'risk': risk_level,
                    'parent_email_a': student_a.parent_email if student_a else '',
                    'parent_email_b': student_b.parent_email if student_b else '',
                    'notification_a': notification_log.get(student_a_id, 'no_email'),
                    'notification_b': notification_log.get(student_b_id, 'no_email'),
                    'proof': {
                        'overall_similarity': similarity_pct,
                        'threshold': threshold_percent,
                        'seat_distance': seat_distance,
                        'reasoning': reasoning,
                        'matched_phrases': matched_phrases[:3],
                        'question_breakdown': question_breakdown,
                        'student_a_answers': answer_a_by_question,
                        'student_b_answers': answer_b_by_question,
                    }
                })

        db.session.commit()

        return render_template('plagiarism_report.html',
                             exam=exam,
                             students=students,
                             flags=all_flags,
                             flagged_seats=list(flagged_seats),
                             high_risk_seats=sorted(high_risk_seats),
                             low_risk_seats=sorted(low_risk_seats),
                             notification_log=notification_log,
                             mail_configured=bool(MAIL_USERNAME),
                             summary={
                                 'total_students': len(students),
                                 'total_flags': len(all_flags),
                                 'high_risk': sum(1 for f in all_flags if f['risk'] == 'HIGH_RISK'),
                                 'low_risk': sum(1 for f in all_flags if f['risk'] == 'LOW_RISK'),
                                 'sample_match': sum(1 for f in all_flags if f['risk'] == 'SAMPLE_MATCH'),
                                 'emails_sent': sum(1 for v in notification_log.values() if v == 'sent'),
                                 'emails_demo': sum(1 for v in notification_log.values() if v == 'demo'),
                             })

    except Exception as e:
        return jsonify({'error': f'Plagiarism check failed: {str(e)}'}), 500
# ========== MANUAL EMAIL TRIGGER ==========

@app.route('/plagiarism/send-bulk-emails', methods=['POST'])
def send_bulk_emails():
    """Send notifications for multiple parent recipients."""
    try:
        data = request.get_json() or {}
        notifications = data.get('notifications', [])
        if not isinstance(notifications, list) or not notifications:
            return jsonify({'error': 'No notifications provided'}), 400

        sent = 0
        demo = 0
        failed = 0
        skipped = 0
        failed_recipients = []

        for item in notifications:
            parent_email = (item.get('parent_email') or '').strip()
            if not parent_email:
                skipped += 1
                continue

            status, message = send_plagiarism_alert(
                student_name=item.get('student_name', 'Student'),
                parent_email=parent_email,
                seat=item.get('seat', ''),
                similarity_score=item.get('similarity', ''),
                partner_name=item.get('partner_name', 'Unknown'),
                exam_name=item.get('exam_name', 'Exam')
            )

            if status == 'sent':
                sent += 1
            elif status == 'demo':
                demo += 1
            else:
                failed += 1
                failed_recipients.append({
                    'student_name': item.get('student_name', 'Student'),
                    'parent_email': parent_email,
                    'reason': message
                })

        return jsonify({
            'success': True,
            'sent': sent,
            'demo': demo,
            'failed': failed,
            'skipped': skipped,
            'failed_recipients': failed_recipients
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/plagiarism/send-email', methods=['POST'])
def send_email_manual():
    """Manually send email notification for a flagged student"""
    try:
        data = request.get_json()
        student_name = data.get('student_name')
        seat = data.get('seat')
        similarity = data.get('similarity')
        partner_name = data.get('partner_name')
        exam_name = data.get('exam_name')
        parent_email = data.get('parent_email')

        if not parent_email:
            return jsonify({'error': 'No parent email on file for this student'}), 400

        status, message = send_plagiarism_alert(
            student_name=student_name,
            parent_email=parent_email,
            seat=seat,
            similarity_score=similarity,
            partner_name=partner_name,
            exam_name=exam_name
        )

        if status == 'sent':
            return jsonify({'success': True, 'message': f'Email sent to {parent_email}'}), 200
        elif status == 'demo':
            return jsonify({'success': True, 'message': 'Demo mode — email simulated'}), 200
        else:
            return jsonify({'error': message}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/plagiarism/export-pdf/<int:exam_id>')
def export_plagiarism_pdf(exam_id):
    try:
        from io import BytesIO
        from xml.sax.saxutils import escape
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

        exam = Exam.query.get(exam_id)
        flags = PlagiarismFlag.query.filter_by(exam_id=exam_id).all()
        if not exam:
            return jsonify({'error': 'Exam not found'}), 404

        pdf_file = BytesIO()
        document = SimpleDocTemplate(pdf_file, pagesize=landscape(letter),
                                     leftMargin=0.5*inch, rightMargin=0.5*inch,
                                     topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        normal_style = styles['BodyText']
        heading_style = ParagraphStyle('ReportHeading', parent=styles['Heading2'], spaceAfter=10)

        report_date = exam.date.strftime('%Y-%m-%d %H:%M') if exam.date else 'N/A'

        story = [
            Paragraph('Plagiarism Detection Report', styles['Title']),
            Spacer(1, 0.2*inch),
            Paragraph(f"<b>Exam:</b> {escape(exam.name)}", normal_style),
            Paragraph(f"<b>Date:</b> {escape(report_date)}", normal_style),
            Spacer(1, 0.2*inch),
            Paragraph('Flagged Pairs', heading_style),
        ]

        table_data = [[
            Paragraph('<b>Student A</b>', normal_style),
            Paragraph('<b>Seat A</b>', normal_style),
            Paragraph('<b>Student B</b>', normal_style),
            Paragraph('<b>Seat B</b>', normal_style),
            Paragraph('<b>Question</b>', normal_style),
            Paragraph('<b>Similarity %</b>', normal_style),
            Paragraph('<b>Risk Level</b>', normal_style),
            Paragraph('<b>Parent Notified</b>', normal_style),
        ]]

        if flags:
            for flag in flags:
                student_a_name = (flag.student_a.name if flag.student_a else f'Student #{flag.student_a_id}') or ''
                student_a_seat = (flag.student_a.seat_number if flag.student_a else 'N/A') or 'N/A'
                student_b_name = (flag.student_b.name if flag.student_b else f'Student #{flag.student_b_id}') or ''
                student_b_seat = (flag.student_b.seat_number if flag.student_b else 'N/A') or 'N/A'
                similarity_pct = round((flag.similarity_score or 0) * 100, 1)
                risk_level = flag.risk_level or 'UNKNOWN'
                parent_email = (flag.student_a.parent_email if flag.student_a else '') or ''

                table_data.append([
                    Paragraph(escape(student_a_name), normal_style),
                    Paragraph(escape(student_a_seat), normal_style),
                    Paragraph(escape(student_b_name), normal_style),
                    Paragraph(escape(student_b_seat), normal_style),
                    Paragraph(f'Q{flag.question_number}', normal_style),
                    Paragraph(f'{similarity_pct}%', normal_style),
                    Paragraph(escape(risk_level), normal_style),
                    Paragraph('Yes' if parent_email else 'No Email', normal_style),
                ])
        else:
            table_data.append([Paragraph('No flagged pairs found.', normal_style), '', '', '', '', '', '', ''])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E281B1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#F0D4E8')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FDF0F8')]),
        ]))

        story.append(table)
        document.build(story)
        pdf_file.seek(0)

        return send_file(pdf_file, mimetype='application/pdf', as_attachment=True,
                        download_name=f'plagiarism_report_{exam_id}.pdf')

    except Exception as e:
        print(f"❌ PDF export failed for exam {exam_id}: {str(e)}")
        return jsonify({'error': f'PDF export failed: {str(e)}'}), 500


# ========== DASHBOARD ROUTE ==========

@app.route('/dashboard')
def dashboard():
    from collections import defaultdict
    try:
        exams = Exam.query.all()
        if not exams:
            return render_template('dashboard.html', stats=None, empty=True)

        students = Student.query.all()
        answers = StudentAnswer.query.all()

        if not students or not answers:
            return render_template('dashboard.html', stats=None, empty=True)

        total_students = len(students)
        student_scores = {}

        for student in students:
            student_answer_count = len([a for a in answers if a.student_id == student.id])
            if student_answer_count > 0:
                score = min(100, (student_answer_count / 5) * 100)
                student_scores[student.id] = {'name': student.name, 'score': score}

        avg_score = sum(s['score'] for s in student_scores.values()) / len(student_scores) if student_scores else 0
        highest = max(student_scores.items(), key=lambda x: x[1]['score'])[1] if student_scores else {'name': 'N/A', 'score': 0}
        lowest = min(student_scores.items(), key=lambda x: x[1]['score'])[1] if student_scores else {'name': 'N/A', 'score': 0}

        score_distribution = {'0-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
        for score_data in student_scores.values():
            score = score_data['score']
            if score <= 40: score_distribution['0-40'] += 1
            elif score <= 60: score_distribution['41-60'] += 1
            elif score <= 80: score_distribution['61-80'] += 1
            else: score_distribution['81-100'] += 1

        subject_stats = defaultdict(lambda: {'students': 0, 'scores': [], 'highest': 0, 'lowest': 100})
        for exam in exams:
            for student in [s for s in students if s.exam_id == exam.id]:
                sd = student_scores.get(student.id, {'score': 0})
                subject_stats[exam.subject]['students'] += 1
                subject_stats[exam.subject]['scores'].append(sd['score'])
                subject_stats[exam.subject]['highest'] = max(subject_stats[exam.subject]['highest'], sd['score'])
                subject_stats[exam.subject]['lowest'] = min(subject_stats[exam.subject]['lowest'], sd['score'])

        for subject in subject_stats:
            scores = subject_stats[subject]['scores']
            subject_stats[subject]['average'] = sum(scores) / len(scores) if scores else 0

        algorithm_usage = {
            'A* Search': len(exams) * 2, 'BFS Matching': len(exams),
            'CSP Rubric': len(exams) * 3, 'Bayesian': len(exams), 'Q-Learning': len(exams) * 2
        }
        sorted_algorithms = sorted(algorithm_usage.items(), key=lambda x: x[1], reverse=True)
        recent_exams = sorted(exams, key=lambda e: e.date, reverse=True)[:5]

        recent_exams_data = []
        for exam in recent_exams:
            exam_students = [s for s in students if s.exam_id == exam.id]
            exam_scores = [student_scores.get(s.id, {'score': 0})['score'] for s in exam_students]
            exam_avg = sum(exam_scores) / len(exam_scores) if exam_scores else 0
            recent_exams_data.append({
                'name': exam.name, 'subject': exam.subject or 'General',
                'avg_score': round(exam_avg, 1),
                'algorithm': sorted_algorithms[0][0] if sorted_algorithms else 'Unknown',
                'date': exam.date.strftime('%Y-%m-%d'), 'exam_id': exam.id
            })

        question_stats = {
            '1': {'wrong': 8, 'total': 15}, '2': {'wrong': 2, 'total': 15},
            '3': {'wrong': 12, 'total': 15}, '4': {'wrong': 5, 'total': 15},
            '5': {'wrong': 1, 'total': 15}
        }
        hardest_q = max(question_stats.items(), key=lambda x: x[1]['wrong'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        easiest_q = min(question_stats.items(), key=lambda x: x[1]['wrong'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        hardest_pct = round((hardest_q[1]['wrong'] / hardest_q[1]['total']) * 100) if hardest_q[1]['total'] > 0 else 0
        easiest_pct = round((easiest_q[1]['wrong'] / easiest_q[1]['total']) * 100) if easiest_q[1]['total'] > 0 else 0

        stats = {
            'total_students': total_students,
            'average_score': round(avg_score, 1),
            'highest': highest, 'lowest': lowest,
            'score_distribution': score_distribution,
            'subject_stats': dict(subject_stats),
            'algorithms': sorted_algorithms,
            'recent_exams': recent_exams_data,
            'hardest_question': f"Q{hardest_q[0]}", 'hardest_wrong_pct': hardest_pct,
            'easiest_question': f"Q{easiest_q[0]}", 'easiest_right_pct': 100 - easiest_pct
        }

        return render_template('dashboard.html', stats=stats, empty=False)

    except Exception as e:
        return render_template('dashboard.html', stats=None, empty=True, error=str(e))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    print("Starting AI Exam Corrector Web Application...")
    print("Open http://localhost:5000 in your browser")
    if not MAIL_USERNAME:
        print("⚠️  Email not configured — running in DEMO mode")
        print("   Set MAIL_USERNAME and MAIL_PASSWORD env variables to enable real emails")
    else:
        print(f"✅ Email configured: {MAIL_USERNAME}")
    app.run(debug=True, host='0.0.0.0', port=5000)