from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import networkx as nx
import re

class TextMatcher:
    def __init__(self):
        self.sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.tfidf_vectorizer = TfidfVectorizer()

    def preprocess_text(self, text):
        # Remove extra whitespace and split into sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return sentences

    def compute_similarity_matrix(self, original_sentences, revised_sentences):
        # Compute embeddings
        original_embeddings = self.sentence_model.encode(original_sentences)
        revised_embeddings = self.sentence_model.encode(revised_sentences)
        
        # Compute cosine similarity
        similarity_matrix = cosine_similarity(original_embeddings, revised_embeddings)
        return similarity_matrix

    def find_optimal_matching(self, similarity_matrix, threshold=0.7):
        G = nx.Graph()
        rows, cols = similarity_matrix.shape
        
        # Add nodes for original and revised sentences
        G.add_nodes_from([f'o{i}' for i in range(rows)], bipartite=0)
        G.add_nodes_from([f'r{j}' for j in range(cols)], bipartite=1)
        
        # Add edges with weights based on similarity
        for i in range(rows):
            for j in range(cols):
                if similarity_matrix[i, j] > threshold:
                    G.add_edge(f'o{i}', f'r{j}', weight=similarity_matrix[i, j])
        
        # Find maximum weight matching
        matching = nx.max_weight_matching(G)
        
        # Convert matching to list of tuples (original_index, revised_index)
        result = []
        for match in matching:
            if match[0].startswith('o'):
                result.append((int(match[0][1:]), int(match[1][1:])))
            else:
                result.append((int(match[1][1:]), int(match[0][1:])))
        
        return sorted(result)

    def match_texts(self, original_text, revised_text):
        original_sentences = self.preprocess_text(original_text)
        revised_sentences = self.preprocess_text(revised_text)

        similarity_matrix = self.compute_similarity_matrix(original_sentences, revised_sentences)
        matches = self.find_optimal_matching(similarity_matrix)

        return original_sentences, revised_sentences, matches

    def get_unmatched_sentences(self, original_sentences, revised_sentences, matches):
        matched_original = set(m[0] for m in matches)
        matched_revised = set(m[1] for m in matches)
        
        unmatched_original = [i for i in range(len(original_sentences)) if i not in matched_original]
        unmatched_revised = [j for j in range(len(revised_sentences)) if j not in matched_revised]
        
        return unmatched_original, unmatched_revised

    def analyze_changes(self, original_sentences, revised_sentences, matches):
        changes = []
        unmatched_original, unmatched_revised = self.get_unmatched_sentences(original_sentences, revised_sentences, matches)
        
        for o, r in matches:
            if original_sentences[o] != revised_sentences[r]:
                changes.append(("modified", o, r))
        
        for o in unmatched_original:
            changes.append(("deleted", o, None))
        
        for r in unmatched_revised:
            changes.append(("added", None, r))
        
        return sorted(changes, key=lambda x: (x[1] if x[1] is not None else x[2]))

# Example usage:
if __name__ == "__main__":
    matcher = TextMatcher()
    original = "The quick brown fox jumps over the lazy dog. It was a sunny day."
    revised = "On a bright day, the agile brown fox leapt over the sleepy dog. The weather was perfect."
    
    orig_sentences, rev_sentences, matches = matcher.match_texts(original, revised)
    changes = matcher.analyze_changes(orig_sentences, rev_sentences, matches)
    
    print("Original sentences:", orig_sentences)
    print("Revised sentences:", rev_sentences)
    print("Matches:", matches)
    print("Changes:", changes)