"""
Plagiarism Detection Engine
===========================
Detects similar answers, seating-based cheating, and sample paper matching.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional


class PlagiarismDetector:
    """Detects plagiarism in student answers"""
    
    def __init__(self, similarity_threshold=0.75, sample_threshold=0.85):
        self.similarity_threshold = similarity_threshold
        self.sample_threshold = sample_threshold
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
    
    @staticmethod
    def parse_seat(seat_number: str) -> Optional[Tuple[int, int]]:
        """
        Parse seat number into (row, column).
        Format: "A1", "B3", "C5", etc.
        A=0, B=1, etc. and 1 is 0-indexed to 0.
        """
        try:
            if len(seat_number) < 2:
                return None
            row = ord(seat_number[0].upper()) - ord('A')
            col = int(seat_number[1:]) - 1
            if row < 0 or col < 0:
                return None
            return (row, col)
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def are_neighbors(seat_a: str, seat_b: str, distance=1) -> bool:
        """
        Check if two seats are adjacent (within 1 seat distance).
        Includes horizontal, vertical, and diagonal neighbors.
        """
        pos_a = PlagiarismDetector.parse_seat(seat_a)
        pos_b = PlagiarismDetector.parse_seat(seat_b)
        
        if not pos_a or not pos_b:
            return False
        
        row_diff = abs(pos_a[0] - pos_b[0])
        col_diff = abs(pos_a[1] - pos_b[1])
        
        # Adjacent if both differences ≤ distance (default 1)
        return row_diff <= distance and col_diff <= distance and (row_diff > 0 or col_diff > 0)
    
    def compare_answers(
        self, 
        answers_dict: Dict[str, str],  # {student_id: answer_text}
        seats_dict: Dict[str, str] = None  # {student_id: seat_number}
    ) -> List[Dict]:
        """
        Compare answers for similarity.
        Returns list of flagged pairs: {student_a, student_b, similarity, neighbors}
        """
        if len(answers_dict) < 2:
            return []
        
        student_ids = list(answers_dict.keys())
        answer_texts = [answers_dict[sid] for sid in student_ids]
        
        # Build TF-IDF matrix
        try:
            tfidf_matrix = self.vectorizer.fit_transform(answer_texts)
            similarities = cosine_similarity(tfidf_matrix)
        except Exception as e:
            print(f"Error computing TF-IDF: {e}")
            return []
        
        flagged_pairs = []
        
        # Find similar pairs
        for i in range(len(student_ids)):
            for j in range(i + 1, len(student_ids)):
                similarity_score = float(similarities[i][j])
                
                if similarity_score >= self.similarity_threshold:
                    student_a_id = student_ids[i]
                    student_b_id = student_ids[j]
                    
                    # Check if they are neighbors
                    is_neighbor = False
                    if seats_dict:
                        seat_a = seats_dict.get(student_a_id)
                        seat_b = seats_dict.get(student_b_id)
                        if seat_a and seat_b:
                            is_neighbor = self.are_neighbors(seat_a, seat_b)
                    
                    flagged_pairs.append({
                        'student_a': student_a_id,
                        'student_b': student_b_id,
                        'similarity': similarity_score,
                        'is_neighbor': is_neighbor
                    })
        
        return flagged_pairs
    
    def check_sample_matching(
        self,
        student_answer: str,
        sample_answers: List[str]
    ) -> Tuple[bool, float]:
        """
        Check if student answer matches sample papers.
        Returns (is_match, max_similarity)
        """
        if not sample_answers:
            return False, 0.0
        
        try:
            all_texts = sample_answers + [student_answer]
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(tfidf_matrix)
            
            # Last row is student answer, compare with samples
            student_row = similarities[-1, :-1]  # All samples
            max_similarity = float(np.max(student_row))
            
            return max_similarity >= self.sample_threshold, max_similarity
        except Exception as e:
            print(f"Error checking sample matching: {e}")
            return False, 0.0
    
    def extract_questions_answers(self, text: str) -> Dict[int, str]:
        """
        Extract questions and answers from text.
        Expects format: Q1: question\nA: answer\nQ2: ...
        """
        qa_dict = {}
        
        # Pattern for Q1: ... A: ...
        pattern = r'Q(\d+)[:.]\s*(.*?)\n\s*A[:.]\s*(.*?)(?=\n\nQ\d|$)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for q_num, question, answer in matches:
            try:
                q_num = int(q_num)
                qa_dict[q_num] = answer.strip()
            except ValueError:
                pass
        
        # Fallback pattern if above doesn't work
        if not qa_dict:
            pattern = r'^A[:.]\s*(.*?)(?=\n\nQ\d|$)'
            lines = text.split('\n')
            q_num = 1
            for i, line in enumerate(lines):
                if re.match(r'^A[:.]\s*', line, re.IGNORECASE):
                    answer = re.sub(r'^A[\.:]\s*', '', line, flags=re.IGNORECASE)
                    qa_dict[q_num] = answer.strip()
                    q_num += 1
        
        return qa_dict


def compute_risk_level(
    is_similar: bool,
    is_neighbor: bool,
    matches_sample: bool
) -> str:
    """
    Compute risk level based on similarity, seating, and sample matching.
    """
    if not is_similar:
        return None
    
    if matches_sample:
        return 'SAMPLE_MATCH'
    elif is_neighbor:
        return 'HIGH_RISK'
    else:
        return 'LOW_RISK'
