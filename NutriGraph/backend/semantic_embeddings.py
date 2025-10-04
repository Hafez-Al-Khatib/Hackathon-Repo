"""
Semantic embeddings using sentence-transformers
Works on Python 3.13 without C++ compilation!
"""

from sentence_transformers import SentenceTransformer, util
from typing import List, Tuple, Dict, Optional
import numpy as np


class SemanticSymptomMatcher:
    """
    Uses semantic embeddings to find similar symptoms and understand relationships.
    Works with Python 3.13 - no C++ compiler needed!
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with a lightweight sentence transformer model.
        
        Args:
            model_name: Hugging Face model name (default is small & fast)
        """
        print(f"[SEMANTIC] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.symptom_embeddings = {}
        self.symptom_list = []
        print("[SEMANTIC] Model loaded successfully!")
    
    def add_symptom(self, symptom: str):
        """Add a symptom to the index"""
        if symptom not in self.symptom_embeddings:
            embedding = self.model.encode(symptom, convert_to_tensor=False)
            self.symptom_embeddings[symptom] = embedding
            self.symptom_list.append(symptom)
    
    def find_similar_symptoms(
        self,
        query: str,
        top_k: int = 3,
        threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Find symptoms semantically similar to the query.
        
        Args:
            query: The symptom or question to match
            top_k: Number of similar symptoms to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of (symptom, similarity_score) tuples
        """
        if not self.symptom_embeddings:
            return []
        
        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=False)
        
        # Calculate similarities
        similarities = []
        for symptom, embedding in self.symptom_embeddings.items():
            score = float(util.cos_sim(query_embedding, embedding)[0][0])
            if score >= threshold:
                similarities.append((symptom, score))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def find_opposite_symptoms(
        self,
        symptom: str,
        candidates: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Find symptoms that might be opposite to the given symptom.
        Uses semantic understanding to detect opposites.
        
        Example: "Nauseous" → finds "Feeling Better", "Healthy"
        """
        opposite_phrases = [
            f"not {symptom}",
            f"opposite of {symptom}",
            f"recovered from {symptom}",
            f"feeling better after {symptom}"
        ]
        
        # Get embeddings for opposite concepts
        opposite_embeddings = [
            self.model.encode(phrase, convert_to_tensor=False)
            for phrase in opposite_phrases
        ]
        avg_opposite = np.mean(opposite_embeddings, axis=0)
        
        # Score candidates
        results = []
        for candidate in candidates:
            if candidate in self.symptom_embeddings:
                candidate_emb = self.symptom_embeddings[candidate]
                score = float(util.cos_sim(avg_opposite, candidate_emb)[0][0])
                results.append((candidate, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def are_symptoms_similar(
        self,
        symptom1: str,
        symptom2: str,
        threshold: float = 0.5
    ) -> bool:
        """
        Check if two symptoms are semantically similar.
        
        Example: "Tired" and "Fatigue" → True
        """
        if symptom1 not in self.symptom_embeddings:
            self.add_symptom(symptom1)
        if symptom2 not in self.symptom_embeddings:
            self.add_symptom(symptom2)
        
        emb1 = self.symptom_embeddings[symptom1]
        emb2 = self.symptom_embeddings[symptom2]
        
        similarity = float(util.cos_sim(emb1, emb2)[0][0])
        return similarity >= threshold
    
    def get_symptom_cluster(
        self,
        symptom: str,
        all_symptoms: List[str],
        threshold: float = 0.5
    ) -> List[str]:
        """
        Get all symptoms similar to the given one (clustering).
        
        Example: "Headache" → ["Migraine", "Head Pain", "Headache"]
        """
        similar = self.find_similar_symptoms(symptom, top_k=len(all_symptoms), threshold=threshold)
        return [s for s, score in similar]
    
    def enhance_query(
        self,
        original_symptom: str,
        all_symptoms: List[str],
        similarity_threshold: float = 0.5
    ) -> List[str]:
        """
        Enhance a symptom query by including semantically similar ones.
        
        Args:
            original_symptom: The symptom user asked about
            all_symptoms: All symptoms in the graph
            similarity_threshold: How similar symptoms must be
        
        Returns:
            List of symptoms to query (original + similar ones)
        """
        # Add original
        symptoms_to_query = [original_symptom]
        
        # Add original to index if not there
        if original_symptom not in self.symptom_embeddings:
            self.add_symptom(original_symptom)
        
        # Find similar symptoms from graph
        for symptom in all_symptoms:
            if symptom != original_symptom:
                if self.are_symptoms_similar(original_symptom, symptom, similarity_threshold):
                    symptoms_to_query.append(symptom)
        
        return symptoms_to_query
    
    def get_stats(self) -> Dict:
        """Get statistics about indexed symptoms"""
        return {
            "total_symptoms": len(self.symptom_embeddings),
            "model": "sentence-transformers (Python 3.13 compatible)",
            "symptoms": list(self.symptom_embeddings.keys())
        }


class ConversationContext:
    """
    Manages conversation history for context-aware queries.
    """
    
    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
    
    def add_interaction(
        self,
        user_input: str,
        system_response: str,
        symptoms: List[str] = None
    ):
        """Add an interaction to history"""
        self.history.append({
            "user": user_input,
            "system": system_response,
            "symptoms": symptoms or [],
            "timestamp": None  # Can add timestamp if needed
        })
        
        # Keep only last N interactions
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_recent_symptoms(self, n: int = 3) -> List[str]:
        """Get recently mentioned symptoms"""
        symptoms = []
        for interaction in reversed(self.history):
            symptoms.extend(interaction.get("symptoms", []))
            if len(symptoms) >= n:
                break
        return symptoms[:n]
    
    def get_context_summary(self) -> str:
        """Get a text summary of recent context"""
        if not self.history:
            return "No previous context"
        
        recent = self.history[-3:]
        summary = "Recent context:\n"
        for i, interaction in enumerate(recent, 1):
            summary += f"{i}. User: {interaction['user'][:50]}...\n"
            if interaction.get('symptoms'):
                summary += f"   Symptoms: {', '.join(interaction['symptoms'])}\n"
        
        return summary
    
    def clear(self):
        """Clear conversation history"""
        self.history = []
    
    def to_dict(self) -> List[Dict]:
        """Export history as dictionary"""
        return self.history.copy()
