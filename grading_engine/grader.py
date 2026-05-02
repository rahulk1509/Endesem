"""
Exam Grader - Main Grading Engine
==================================
Orchestrates the grading process using multiple AI algorithms.
 
BUGS FIXED:
1. find_question() math matching: num_key was built but never used; 
   ambiguous partial-number matching caused wrong question to be returned.
2. parse_questions_answers() regex: non-greedy (.*?) captured empty string 
   for the last answer; fixed with MULTILINE + explicit newline handling.
3. grade_generic() passed bool (len > 10) as numeric score to calculate_confidence().
4. generate_feedback() crashed with TypeError when correct_answer was None 
   (tried to slice None[:100]).
5. total_marks float drift: now accumulated with round() per step.
"""
 
import re
from ai_algorithms.search.answer_search import AnswerSearcher
from ai_algorithms.bayesian.confidence_scorer import ConfidenceScorer
 
 
class QuestionBank:
    """
    Question and Answer Bank
    Contains correct answers for matching
    """
    
    def __init__(self):
        self.questions = self.load_default_questions()
        
    def load_default_questions(self):
        """Load default question bank for AI course"""
        return {
            # AI Fundamentals
            "what is artificial intelligence": {
                "correct_answers": [
                    "Artificial Intelligence is the simulation of human intelligence processes by machines, especially computer systems",
                    "AI is the ability of machines to perform tasks that typically require human intelligence",
                    "AI refers to systems that can perform tasks requiring human intelligence such as learning, reasoning, and problem-solving",
                    "The simulation of human intelligence in machines programmed to think like humans"
                ],
                "keywords": ["artificial", "intelligence", "machines", "human", "simulation", "learning", "reasoning"],
                "max_marks": 5,
                "type": "definition"
            },
            
            # Search Algorithms
            "what is bfs": {
                "correct_answers": [
                    "BFS (Breadth First Search) is a graph traversal algorithm that explores all neighbors at the current depth before moving to nodes at the next depth level",
                    "Breadth First Search explores nodes level by level, visiting all neighbors before going deeper",
                    "BFS uses a queue to explore all nodes at current depth before moving to next level"
                ],
                "keywords": ["breadth", "first", "search", "graph", "traversal", "queue", "level", "neighbors"],
                "max_marks": 5,
                "type": "definition"
            },
            
            "what is dfs": {
                "correct_answers": [
                    "DFS (Depth First Search) is a graph traversal algorithm that explores as far as possible along each branch before backtracking",
                    "Depth First Search uses a stack to explore deeply into each path before backtracking",
                    "DFS goes deep into one branch before exploring siblings"
                ],
                "keywords": ["depth", "first", "search", "graph", "traversal", "stack", "backtrack", "branch"],
                "max_marks": 5,
                "type": "definition"
            },
            
            "what is a* search": {
                "correct_answers": [
                    "A* is a best-first search algorithm that uses heuristics to find the optimal path by minimizing f(n) = g(n) + h(n)",
                    "A* search combines path cost g(n) with heuristic estimate h(n) to find optimal solutions",
                    "A star is an informed search algorithm that uses evaluation function f(n) = g(n) + h(n)"
                ],
                "keywords": ["a*", "astar", "heuristic", "optimal", "path", "g(n)", "h(n)", "f(n)", "best-first"],
                "max_marks": 5,
                "type": "definition"
            },
            
            "what is heuristic": {
                "correct_answers": [
                    "A heuristic is a function that estimates the cost from the current state to the goal state",
                    "Heuristic provides an estimate of how close a state is to the goal",
                    "A heuristic function guides search by estimating remaining cost to reach goal"
                ],
                "keywords": ["heuristic", "estimate", "cost", "goal", "function", "guide"],
                "max_marks": 4,
                "type": "definition"
            },
            
            # CSP
            "what is constraint satisfaction problem": {
                "correct_answers": [
                    "CSP consists of variables, domains, and constraints that must all be satisfied",
                    "A constraint satisfaction problem has variables with domains and constraints that define valid assignments",
                    "CSP is a problem where we must assign values to variables from their domains while satisfying all constraints"
                ],
                "keywords": ["constraint", "satisfaction", "variables", "domains", "constraints", "assignment"],
                "max_marks": 5,
                "type": "definition"
            },
            
            # Bayesian
            "what is bayesian inference": {
                "correct_answers": [
                    "Bayesian inference uses Bayes theorem to update the probability of a hypothesis based on evidence",
                    "Bayesian inference calculates posterior probability from prior probability and likelihood using Bayes rule",
                    "A method of statistical inference that uses Bayes theorem to update probabilities based on new data"
                ],
                "keywords": ["bayesian", "bayes", "probability", "hypothesis", "evidence", "posterior", "prior", "likelihood"],
                "max_marks": 5,
                "type": "definition"
            },
            
            # MDP
            "what is markov decision process": {
                "correct_answers": [
                    "MDP is a mathematical framework for modeling decision-making with states, actions, transition probabilities, and rewards",
                    "Markov Decision Process has states S, actions A, transition function T, and reward function R",
                    "MDP models sequential decision-making under uncertainty with Markov property"
                ],
                "keywords": ["markov", "decision", "process", "states", "actions", "transitions", "rewards", "mdp"],
                "max_marks": 5,
                "type": "definition"
            },
            
            # RL
            "what is q-learning": {
                "correct_answers": [
                    "Q-learning is a model-free reinforcement learning algorithm that learns action values for state-action pairs",
                    "Q-learning learns optimal policy by updating Q-values using Q(s,a) = Q(s,a) + α(r + γ max Q(s',a') - Q(s,a))",
                    "A reinforcement learning algorithm that learns Q-values without needing a model of the environment"
                ],
                "keywords": ["q-learning", "reinforcement", "learning", "q-value", "policy", "model-free", "action"],
                "max_marks": 5,
                "type": "definition"
            },
            
            "what is reinforcement learning": {
                "correct_answers": [
                    "Reinforcement learning is a type of machine learning where an agent learns by interacting with environment and receiving rewards",
                    "RL is learning through trial and error with rewards and penalties",
                    "Agent learns optimal behavior through actions, states, and reward signals"
                ],
                "keywords": ["reinforcement", "learning", "agent", "environment", "rewards", "actions", "states"],
                "max_marks": 5,
                "type": "definition"
            },
            
            # Math questions
            "calculate 15 27": {
                "correct_answers": ["42", "forty-two", "forty two", "= 42", "is 42"],
                "keywords": ["42"],
                "max_marks": 2,
                "type": "math"
            },
            
            "calculate 25 17": {
                "correct_answers": ["42", "forty-two", "forty two", "= 42"],
                "keywords": ["42"],
                "max_marks": 2,
                "type": "math"
            },
            
            "2 2": {
                "correct_answers": ["4", "four"],
                "keywords": ["4"],
                "max_marks": 2,
                "type": "math"
            },
            
            # Equation solving
            "2x 3 11": {
                "correct_answers": ["x=4", "x = 4", "4", "x is 4"],
                "keywords": ["4", "x"],
                "max_marks": 3,
                "type": "math"
            },
            
            "2x 5 15": {
                "correct_answers": ["x=5", "x = 5", "5"],
                "keywords": ["x", "5"],
                "max_marks": 3,
                "type": "math"
            },
            
            # General knowledge
            "capital france": {
                "correct_answers": ["Paris", "paris"],
                "keywords": ["paris"],
                "max_marks": 2,
                "type": "factual"
            },
            
            "capital india": {
                "correct_answers": ["New Delhi", "Delhi", "new delhi"],
                "keywords": ["delhi", "new delhi"],
                "max_marks": 2,
                "type": "factual"
            },
            
            # Types of search
            "types search algorithms": {
                "correct_answers": [
                    "Uninformed search (BFS, DFS) and Informed search (A*, Greedy)",
                    "Blind search like BFS DFS and heuristic search like A* and Greedy Best First",
                    "Search algorithms include BFS, DFS, A*, Greedy, and Iterative Deepening"
                ],
                "keywords": ["bfs", "dfs", "a*", "greedy", "uninformed", "informed", "heuristic"],
                "max_marks": 5,
                "type": "list"
            }
        }
        
    def find_question(self, question_text):
        """
        Find matching question in bank.
        
        FIX: Math matching now uses the cleaned numeric key directly instead
        of building num_key and discarding it.  The old partial-number check
        (e.g. '1' in '2x+5=15') caused wrong questions to be returned.
        """
        question_lower = question_text.lower()
        
        # Strip common filler words so keys stay short and stable
        clean_q = re.sub(r'\b(what|is|are|the|define|explain|describe|a|an|of|calculate|solve|find)\b', '', question_lower)
        clean_q = re.sub(r'[^\w\s]', ' ', clean_q).strip()
        clean_q = re.sub(r'\s+', ' ', clean_q)
 
        # --- BUG FIX 1: math addition/subtraction ---
        # Build a normalised key like "15 27" and look it up directly.
        calc_match = re.search(r'(\d+)\s*[\+\-\*\/]\s*(\d+)', question_text)
        if calc_match:
            num1, num2 = calc_match.group(1), calc_match.group(2)
            # Try both orderings of the two operands as keys
            for candidate in [f"calculate {num1} {num2}", f"calculate {num2} {num1}",
                               f"{num1} {num2}", f"{num2} {num1}"]:
                if candidate in self.questions:
                    return self.questions[candidate]
 
        # --- BUG FIX 1 continued: equation solving ---
        # Match patterns like "2x + 3 = 11" → normalised key "2x 3 11"
        eq_match = re.search(r'(\d+)x\s*[\+\-]\s*(\d+)\s*=\s*(\d+)', question_text.replace(' ', ''))
        if eq_match:
            a, b, c = eq_match.group(1), eq_match.group(2), eq_match.group(3)
            candidate = f"{a}x {b} {c}"
            if candidate in self.questions:
                return self.questions[candidate]
 
        # Exact / substring match on cleaned question
        for key in self.questions:
            if key in clean_q or clean_q in key:
                return self.questions[key]
                
        # Keyword overlap fallback (≥50 % of key words must appear)
        for key, data in self.questions.items():
            key_words = set(key.split())
            question_words = set(clean_q.split())
            overlap = len(key_words & question_words)
            if key_words and overlap >= len(key_words) * 0.5:
                return data
                
        return None
 
 
class ExamGrader:
    """
    Main grading engine.
    Uses AI algorithms to grade exam papers.
    """
    
    def __init__(self):
        self.question_bank = QuestionBank()
        self.searcher = AnswerSearcher()
        self.confidence_scorer = ConfidenceScorer()
        self.q_table = {}  # For Q-learning (Unit IV)
        
    def parse_questions_answers(self, text):
        """
        Parse question-answer pairs from text.
 
        FIG FIX 2: The original regex used a non-greedy (.*?) with a $ anchor
        in DOTALL mode.  For the *last* Q/A pair the lookahead never matched
        so (.*?) captured an empty string — the last answer was always lost.
 
        Fix: use a greedy match up to the next Q-marker or end-of-string,
        then strip trailing whitespace.
        """
        qa_pairs = []
        
        # Greedy capture for the answer portion so the last answer isn't dropped.
        pattern = r'Q\d*[\.:]\s*(.*?)\n\s*A[\.:]\s*(.*?)(?=\nQ\d*[\.:]|\Z)'
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        
        for i, (question, answer) in enumerate(matches, 1):
            question = question.strip()
            answer = answer.strip()
            if question and answer:          # skip empty pairs
                qa_pairs.append({
                    'number': i,
                    'question': question,
                    'answer': answer
                })
            
        # Fallback: line-by-line parser (unchanged logic, just kept as safety net)
        if not qa_pairs:
            lines = text.strip().split('\n')
            current_q = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if re.match(r'^Q\d*[\.:]', line, re.IGNORECASE) or re.match(r'^\d+\.', line):
                    current_q = re.sub(r'^Q\d*[\.:]\s*|^\d+\.\s*', '', line, flags=re.IGNORECASE)
                elif re.match(r'^A[\.:]', line, re.IGNORECASE) and current_q:
                    answer = re.sub(r'^A[\.:]\s*', '', line, flags=re.IGNORECASE)
                    qa_pairs.append({
                        'number': len(qa_pairs) + 1,
                        'question': current_q,
                        'answer': answer
                    })
                    current_q = None
                    
        return qa_pairs
        
    def grade_single_answer(self, question, student_answer, algorithm="A* Search"):
        """Grade a single answer using the specified algorithm."""
        q_data = self.question_bank.find_question(question)
        
        if not q_data:
            return self.grade_generic(question, student_answer, algorithm)
            
        correct_answers = q_data['correct_answers']
        keywords = q_data['keywords']
        max_marks = q_data['max_marks']
        q_type = q_data['type']
        
        search_result = self.searcher.search(
            student_answer,
            correct_answers,
            algorithm,
            keywords
        )
        
        similarity = search_result['similarity_score']
        nodes_explored = search_result['nodes_explored']
        
        keyword_score = self.searcher.keyword_overlap(student_answer, keywords)
        
        # BUG FIX 3 is downstream — confidence_scorer receives proper floats here.
        marks_result = self.confidence_scorer.calculate_partial_marks(
            max_marks=max_marks,
            keyword_score=keyword_score,
            similarity_score=similarity,
            completeness=min(1.0, len(student_answer) / 100),
            has_steps=(q_type == 'math')
        )
        
        if marks_result['marks'] >= max_marks * 0.9:
            status = "correct"
            icon = "✅"
        elif marks_result['marks'] >= max_marks * 0.5:
            status = "partial"
            icon = "⚠️"
        else:
            status = "incorrect"
            icon = "❌"
            
        return {
            'status': status,
            'icon': icon,
            'marks': marks_result['marks'],
            'max_marks': max_marks,
            'similarity': similarity,
            'keyword_score': keyword_score,
            'confidence': marks_result['confidence'],
            'algorithm': algorithm,
            'nodes_explored': nodes_explored,
            'best_match': search_result['best_match'],
            'feedback': self.generate_feedback(
                student_answer, search_result['best_match'], keywords, status
            )
        }
        
    def grade_generic(self, question, student_answer, algorithm):
        """Grade answer when question is not in bank."""
        keywords = self.searcher.extract_keywords(question)
        keyword_score = self.searcher.keyword_overlap(student_answer, keywords)
 
        # BUG FIX 3: was passing `len(student_answer) > 10` (a bool) as a
        # numeric completeness score.  Now passes a proper float 0.0–1.0.
        completeness_score = min(1.0, len(student_answer) / 50)
 
        confidence = self.confidence_scorer.calculate_confidence(
            keyword_score,
            completeness_score,
            completeness_score          # third param treated as numeric score
        )
        
        max_marks = 5
        marks = round(max_marks * confidence['confidence'], 1)
        
        if marks >= 4:
            status = "correct"
            icon = "✅"
        elif marks >= 2.5:
            status = "partial"
            icon = "⚠️"
        else:
            status = "incorrect"
            icon = "❌"
            
        return {
            'status': status,
            'icon': icon,
            'marks': marks,
            'max_marks': max_marks,
            'similarity': keyword_score,
            'keyword_score': keyword_score,
            'confidence': confidence['confidence'],
            'algorithm': algorithm,
            'nodes_explored': len(keywords),
            'best_match': None,
            'feedback': f"Generic grading applied. Keywords found: {keyword_score:.0%}"
        }
        
    def generate_feedback(self, student_answer, correct_answer, keywords, status):
        """
        Generate helpful feedback.
 
        BUG FIX 4: correct_answer can be None when no match was found in the
        bank.  Slicing None[:100] raised TypeError.  Guard added.
        """
        if status == "correct":
            return "Excellent! Your answer is correct."
        elif status == "partial":
            missing_keywords = [
                kw for kw in keywords
                if kw.lower() not in student_answer.lower()
            ]
            if missing_keywords:
                return f"Good attempt! Consider including: {', '.join(missing_keywords[:3])}"
            return "Good answer but could be more complete."
        else:
            # BUG FIX 4: guard against None before slicing
            if correct_answer is not None:
                return f"Incorrect. Expected answer: {correct_answer[:100]}..."
            return "Incorrect. Please review the concept."
            
    def grade(self, text, algorithm="A* Search", subject="General"):
        """Grade entire exam paper."""
        qa_pairs = self.parse_questions_answers(text)
        
        if not qa_pairs:
            return {
                'success': False,
                'error': 'Could not parse questions and answers from text',
                'questions': [],
                'total_marks': 0,
                'total_max_marks': 0
            }
            
        results = []
        total_marks = 0
        total_max_marks = 0
        
        for qa in qa_pairs:
            result = self.grade_single_answer(
                qa['question'],
                qa['answer'],
                algorithm
            )
            result['question_number'] = qa['number']
            result['question_text'] = qa['question']
            result['student_answer'] = qa['answer']
            
            results.append(result)
            # BUG FIX 5: round per step to avoid float drift
            total_marks = round(total_marks + result['marks'], 1)
            total_max_marks += result['max_marks']
            
        percentage = (total_marks / total_max_marks * 100) if total_max_marks > 0 else 0
        
        if percentage >= 90:
            grade = "A+"
        elif percentage >= 80:
            grade = "A"
        elif percentage >= 70:
            grade = "B+"
        elif percentage >= 60:
            grade = "B"
        elif percentage >= 50:
            grade = "C"
        elif percentage >= 40:
            grade = "D"
        else:
            grade = "F"
            
        return {
            'success': True,
            'questions': results,
            'total_marks': round(total_marks, 1),
            'total_max_marks': total_max_marks,
            'percentage': round(percentage, 1),
            'grade': grade,
            'algorithm_used': algorithm,
            'subject': subject,
            'summary': {
                'correct': sum(1 for r in results if r['status'] == 'correct'),
                'partial': sum(1 for r in results if r['status'] == 'partial'),
                'incorrect': sum(1 for r in results if r['status'] == 'incorrect'),
                'total': len(results)
            }
        }
 
 
# For testing
if __name__ == "__main__":
    grader = ExamGrader()
    
    test_text = """
Q1: What is Artificial Intelligence?
A: AI is the simulation of human intelligence in machines.
 
Q2: Calculate: 15 + 27 = ?
A: 42
 
Q3: What is the capital of France?
A: Paris
 
Q4: Define BFS algorithm.
A: Breadth First Search explores all neighbors at current depth.
 
Q5: What is 2x + 3 = 11? Find x.
A: x = 4
    """
    
    print("Testing Exam Grader")
    print("=" * 60)
    
    results = grader.grade(test_text, algorithm="A* Search")
    
    print(f"\nOverall: {results['total_marks']}/{results['total_max_marks']}")
    print(f"Percentage: {results['percentage']}%")
    print(f"Grade: {results['grade']}")
    print()
    
    for q in results['questions']:
        print(f"Q{q['question_number']}: {q['question_text'][:40]}...")
        print(f"   {q['icon']} {q['marks']}/{q['max_marks']} - {q['status']}")
        print(f"   Feedback: {q['feedback']}")
        print()