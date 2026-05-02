"""
Database Models for AI Exam Corrector
=====================================
Handles storage of exams, students, answers, and plagiarism data.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Exam(db.Model):
    """Represents an exam/test session"""
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(255))
    total_students = db.Column(db.Integer, default=0)
    
    # Relationships
    students = db.relationship('Student', backref='exam', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('StudentAnswer', backref='exam', lazy=True, cascade='all, delete-orphan')
    sample_answers = db.relationship('SampleAnswer', backref='exam', lazy=True, cascade='all, delete-orphan')
    plagiarism_flags = db.relationship('PlagiarismFlag', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exam {self.name}>'


class Student(db.Model):
    """Represents a student taking an exam"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    roll_number = db.Column(db.String(50))
    seat_number = db.Column(db.String(10), nullable=False)  # Format: "A1", "B3", etc.
    parent_email = db.Column(db.String(255), default='')
    
    # Relationships
    answers = db.relationship('StudentAnswer', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name} - {self.seat_number}>'
    
    def parse_seat(self):
        """Parse seat number into (row, column)"""
        if len(self.seat_number) < 2:
            return None
        row = ord(self.seat_number[0].upper()) - ord('A')  # A=0, B=1, etc.
        try:
            col = int(self.seat_number[1:]) - 1  # 1-indexed to 0-indexed
            return (row, col)
        except ValueError:
            return None


class StudentAnswer(db.Model):
    """Stores student answers for each question"""
    __tablename__ = 'student_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudentAnswer Q{self.question_number} - Student {self.student_id}>'


class SampleAnswer(db.Model):
    """Stores model/sample answers for reference"""
    __tablename__ = 'sample_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    model_answer_text = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SampleAnswer Q{self.question_number}>'


class PlagiarismFlag(db.Model):
    """Stores flagged plagiarism cases"""
    __tablename__ = 'plagiarism_flags'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_a_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student_b_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)
    similarity_score = db.Column(db.Float)  # 0.0 to 1.0
    risk_level = db.Column(db.String(50))  # 'HIGH_RISK', 'LOW_RISK', 'SAMPLE_MATCH'
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships for convenience
    student_a = db.relationship('Student', foreign_keys=[student_a_id])
    student_b = db.relationship('Student', foreign_keys=[student_b_id])
    
    def __repr__(self):
        return f'<PlagiarismFlag {self.risk_level} - Q{self.question_number}>'
