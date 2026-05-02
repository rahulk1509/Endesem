"""
Plagiarism Detection Engine
===========================
Detects similar answers, seating-based cheating, and sample paper matching.
"""

import html
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class PlagiarismDetector:
    """Detects plagiarism in student answers"""

    def __init__(self, similarity_threshold=0.75, sample_threshold=0.85):
        self.similarity_threshold = similarity_threshold
        self.sample_threshold = sample_threshold
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')

    @staticmethod
    def parse_seat(seat_number: str) -> Optional[Tuple[int, int]]:
        """Parse seat number into (row, column). Format: A1, B3, C5, etc."""
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
        """Check if two seats are adjacent (within 1 seat distance)."""
        pos_a = PlagiarismDetector.parse_seat(seat_a)
        pos_b = PlagiarismDetector.parse_seat(seat_b)

        if not pos_a or not pos_b:
            return False

        row_diff = abs(pos_a[0] - pos_b[0])
        col_diff = abs(pos_a[1] - pos_b[1])

        return row_diff <= distance and col_diff <= distance and (row_diff > 0 or col_diff > 0)

    def compare_answers(
        self,
        answers_dict: Dict[str, str],
        seats_dict: Dict[str, str] = None
    ) -> List[Dict]:
        """
        Compare answers for similarity.
        Returns list of flagged pairs with student_a, student_b, similarity, is_neighbor.
        """
        if len(answers_dict) < 2:
            return []

        student_ids = list(answers_dict.keys())
        answer_texts = [answers_dict[sid] for sid in student_ids]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(answer_texts)
            similarities = cosine_similarity(tfidf_matrix)
        except Exception as e:
            print(f"Error computing TF-IDF: {e}")
            return []

        flagged_pairs = []

        for i in range(len(student_ids)):
            for j in range(i + 1, len(student_ids)):
                similarity_score = float(similarities[i][j])

                if similarity_score >= self.similarity_threshold:
                    student_a_id = student_ids[i]
                    student_b_id = student_ids[j]

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

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate cosine similarity between two answer texts."""
        if not text_a or not text_b:
            return 0.0

        try:
            tfidf_matrix = self.vectorizer.fit_transform([text_a, text_b])
            return float(cosine_similarity(tfidf_matrix)[0][1])
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def extract_common_phrases(
        self,
        text_a: str,
        text_b: str,
        min_words: int = 5,
        max_phrases: int = 3,
    ) -> List[str]:
        """Extract common contiguous phrases using SequenceMatcher blocks."""
        if not text_a or not text_b:
            return []

        words_a = re.findall(r"\b[\w'-]+\b", text_a.lower())
        words_b = re.findall(r"\b[\w'-]+\b", text_b.lower())

        if len(words_a) < min_words or len(words_b) < min_words:
            return []

        matcher = SequenceMatcher(None, words_a, words_b)
        phrases: List[str] = []
        seen = set()

        for block in matcher.get_matching_blocks():
            if block.size < min_words:
                continue
            phrase = " ".join(words_a[block.a:block.a + block.size]).strip()
            if phrase and phrase not in seen:
                seen.add(phrase)
                phrases.append(phrase)

        return phrases[:max_phrases]

    def highlight_matching_phrases(self, text: str, phrases: List[str]) -> str:
        """Return HTML with matching phrases highlighted."""
        if not text:
            return ""

        if not phrases:
            return html.escape(text)

        spans = []
        for phrase in sorted({p.lower() for p in phrases if p}, key=len, reverse=True):
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            for match in pattern.finditer(text):
                spans.append((match.start(), match.end()))

        if not spans:
            return html.escape(text)

        spans.sort()
        merged_spans = []
        for start, end in spans:
            if not merged_spans or start > merged_spans[-1][1]:
                merged_spans.append([start, end])
            else:
                merged_spans[-1][1] = max(merged_spans[-1][1], end)

        highlighted = []
        last_index = 0
        for start, end in merged_spans:
            highlighted.append(html.escape(text[last_index:start]))
            highlighted.append(
                f'<span class="matching-phrase">{html.escape(text[start:end])}</span>'
            )
            last_index = end

        highlighted.append(html.escape(text[last_index:]))
        return ''.join(highlighted)

    def check_sample_matching(
        self,
        student_answer: str,
        sample_answers: List[str]
    ) -> Tuple[bool, float]:
        """Check if student answer matches sample papers."""
        if not sample_answers:
            return False, 0.0

        try:
            all_texts = sample_answers + [student_answer]
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(tfidf_matrix)
            student_row = similarities[-1, :-1]
            max_similarity = float(np.max(student_row))
            return max_similarity >= self.sample_threshold, max_similarity
        except Exception as e:
            print(f"Error checking sample matching: {e}")
            return False, 0.0

    def extract_questions_answers(self, text: str) -> Dict[int, str]:
        """Extract questions and answers from text."""
        qa_dict = {}

        pattern = r'Q(\d+)[:.]\s*(.*?)\n\s*A[:.]\s*(.*?)(?=\n\nQ\d|$)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

        for q_num, question, answer in matches:
            try:
                qa_dict[int(q_num)] = answer.strip()
            except ValueError:
                pass

        if not qa_dict:
            lines = text.split('\n')
            q_num = 1
            for line in lines:
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
    """Compute risk level based on similarity, seating, and sample matching."""
    if not is_similar:
        return None

    if matches_sample:
        return 'SAMPLE_MATCH'
    elif is_neighbor:
        return 'HIGH_RISK'
    else:
        return 'LOW_RISK'