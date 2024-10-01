import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class TextMatcher:
    def __init__(self):
        self.sentence_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

    def preprocess_text(self, text):
        sentences = re.findall(r"[^.!?]+[.!?]*", text)
        return [s.strip() for s in sentences if s.strip()]

    def compute_similarity_matrix(self, original_sentences, revised_sentences):
        original_embeddings = self.sentence_model.encode(original_sentences)
        revised_embeddings = self.sentence_model.encode(revised_sentences)
        return cosine_similarity(original_embeddings, revised_embeddings)

    def match_texts(self, original_text, revised_text):
        original_sentences = self.preprocess_text(original_text)
        revised_sentences = self.preprocess_text(revised_text)

        similarity_matrix = self.compute_similarity_matrix(
            original_sentences, revised_sentences
        )
        matches = self.find_matches(similarity_matrix)
        split_sentences = self.detect_split_sentences(similarity_matrix)

        return original_sentences, revised_sentences, matches, split_sentences

    def find_matches(self, similarity_matrix, threshold=0.5):
        matches = []
        for i in range(similarity_matrix.shape[0]):
            best_match = np.argmax(similarity_matrix[i])
            if similarity_matrix[i, best_match] > threshold:
                matches.append((i, best_match))
        return matches

    def detect_split_sentences(
        self, similarity_matrix, threshold=0.3, split_threshold=0.8
    ):
        split_sentences = []
        for i in range(similarity_matrix.shape[0]):
            potential_splits = np.where(similarity_matrix[i] > threshold)[0]
            if len(potential_splits) > 1:
                total_similarity = np.sum(similarity_matrix[i, potential_splits])
                if total_similarity > split_threshold:
                    split_sentences.append(
                        (i, (potential_splits[0], potential_splits[-1]))
                    )
        return split_sentences

    def analyze_changes(
        self, original_sentences, revised_sentences, matches, split_sentences
    ):
        changes = []
        matched_original = set(m[0] for m in matches)
        matched_revised = set(m[1] for m in matches)

        for o, r in matches:
            if any(
                o == s[0] and r >= s[1][0] and r <= s[1][1] for s in split_sentences
            ):
                changes.append(("split", o, r))
            elif original_sentences[o] != revised_sentences[r]:
                changes.append(("modified", o, r))

        for o in range(len(original_sentences)):
            if o not in matched_original:
                changes.append(("deleted", o, None))

        for r in range(len(revised_sentences)):
            if r not in matched_revised:
                changes.append(("added", None, r))

        return sorted(changes, key=lambda x: (x[1] if x[1] is not None else x[2]))
