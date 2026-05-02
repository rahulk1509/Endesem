"""
Answer Search Algorithms - Unit I
=================================
Implements BFS, DFS, A*, Greedy search for answer matching.
 
BUGS FIXED:
1. astar_search() heappush crashed with TypeError when two answers had equal
   f_score because Python tried to compare the string 'answer' field.
   Fixed by adding a unique integer tiebreaker as second tuple element.
2. search() result dict now echoes back the actual algorithm used.
"""
 
import re
import heapq
from collections import deque
from difflib import SequenceMatcher
 
 
class AnswerSearcher:
    
    def __init__(self):
        self.nodes_explored = 0
        
    def similarity(self, str1, str2):
        """Calculate similarity between two strings (0 to 1)"""
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        return SequenceMatcher(None, str1, str2).ratio()
        
    def keyword_overlap(self, text, keywords):
        """Calculate keyword overlap score"""
        if not keywords:
            return 0.0
        text_lower = text.lower()
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        return found / len(keywords)
 
    # =========================================
    # BFS - Breadth First Search (Unit I)
    # =========================================
    def bfs_search(self, student_answer, answer_bank):
        self.nodes_explored = 0
        queue = deque(answer_bank)
        best_match = None
        best_score = 0.0
        
        while queue:
            current_answer = queue.popleft()
            self.nodes_explored += 1
            score = self.similarity(student_answer, current_answer)
            if score > best_score:
                best_score = score
                best_match = current_answer
            if score >= 0.95:
                break
                
        return best_match, best_score, self.nodes_explored
 
    # =========================================
    # DFS - Depth First Search (Unit I)
    # =========================================
    def dfs_search(self, student_answer, answer_bank):
        self.nodes_explored = 0
        stack = list(answer_bank)
        best_match = None
        best_score = 0.0
        
        while stack:
            current_answer = stack.pop()
            self.nodes_explored += 1
            score = self.similarity(student_answer, current_answer)
            if score > best_score:
                best_score = score
                best_match = current_answer
            if score >= 0.9:
                break
                
        return best_match, best_score, self.nodes_explored
 
    # =========================================
    # A* Search - Best First with Heuristic (Unit I)
    # =========================================
    def astar_search(self, student_answer, answer_bank, keywords=None):
        self.nodes_explored = 0
        
        if keywords is None:
            keywords = self.extract_keywords(student_answer)
            
        open_set = []
        
        # BUG FIX: Added unique index as tiebreaker (second element) to avoid
        # TypeError when f_scores are equal and Python tries to compare strings.
        for idx, answer in enumerate(answer_bank):
            h_score = self.keyword_overlap(answer, keywords)
            f_score = -h_score
            heapq.heappush(open_set, (f_score, idx, answer, 0))
            
        best_match = None
        best_score = 0.0
        path = []
        
        while open_set:
            f_score, _, current_answer, g_score = heapq.heappop(open_set)
            self.nodes_explored += 1
            
            preview = current_answer[:50] + ("..." if len(current_answer) > 50 else "")
            path.append(preview)
            
            similarity_score = self.similarity(student_answer, current_answer)
            
            if similarity_score > best_score:
                best_score = similarity_score
                best_match = current_answer
                
            if similarity_score >= 0.85:
                break
                
        return best_match, best_score, self.nodes_explored, path
 
    # =========================================
    # Greedy Search (Unit I)
    # =========================================
    def greedy_search(self, student_answer, answer_bank, keywords=None):
        self.nodes_explored = 0
        
        if keywords is None:
            keywords = self.extract_keywords(student_answer)
            
        scored_answers = []
        for answer in answer_bank:
            h_score = self.keyword_overlap(answer, keywords)
            scored_answers.append((h_score, answer))
            
        scored_answers.sort(reverse=True)
        
        best_match = None
        best_score = 0.0
        
        for h_score, answer in scored_answers:
            self.nodes_explored += 1
            similarity_score = self.similarity(student_answer, answer)
            if similarity_score > best_score:
                best_score = similarity_score
                best_match = answer
            if similarity_score >= 0.7:
                break
                
        return best_match, best_score, self.nodes_explored
 
    def extract_keywords(self, text):
        """Extract important keywords from text"""
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
            'neither', 'not', 'only', 'own', 'same', 'than', 'too',
            'very', 'just', 'also', 'now', 'it', 'its', 'this', 'that',
            'these', 'those', 'what', 'which', 'who', 'whom', 'whose'
        }
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        return list(set(keywords))
 
    def search(self, student_answer, answer_bank, algorithm="A* Search", keywords=None):
        """Main search method - delegates to specific algorithm"""
        if algorithm == "BFS":
            match, score, nodes = self.bfs_search(student_answer, answer_bank)
            path = None
        elif algorithm == "DFS":
            match, score, nodes = self.dfs_search(student_answer, answer_bank)
            path = None
        elif algorithm == "Greedy":
            match, score, nodes = self.greedy_search(student_answer, answer_bank, keywords)
            path = None
        else:  # A* Search (default)
            match, score, nodes, path = self.astar_search(student_answer, answer_bank, keywords)
 
        return {
            "best_match": match,
            "similarity_score": score,
            "nodes_explored": nodes,
            "algorithm": algorithm,   # BUG FIX: now echoes actual algorithm used
            "search_path": path
        }
 
 
if __name__ == "__main__":
    searcher = AnswerSearcher()
    
    answer_bank = [
        "Artificial Intelligence is the simulation of human intelligence by machines",
        "AI refers to machines that can perform tasks requiring human intelligence",
        "AI is computer systems able to perform tasks normally requiring human intelligence",
        "Machine learning is a subset of AI that enables systems to learn from data",
        "Deep learning uses neural networks with multiple layers"
    ]
    
    student_answer = "AI is the simulation of human intelligence in machines"
    
    print("Testing Search Algorithms")
    print("=" * 60)
    print(f"Student Answer: {student_answer}\n")
    
    for algo in ["BFS", "DFS", "Greedy", "A* Search"]:
        result = searcher.search(student_answer, answer_bank, algo)
        print(f"{algo}:")
        print(f"  Best Match: {result['best_match'][:60]}...")
        print(f"  Similarity: {result['similarity_score']:.2%}")
        print(f"  Nodes Explored: {result['nodes_explored']}\n")
 