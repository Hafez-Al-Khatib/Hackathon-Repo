"""
LLM-based reasoning engine that combines graph structure with language understanding
"""

from typing import List, Dict, Optional, Tuple
import json


class GraphAwareLLMReasoner:
    """
    Enhances LLM reasoning with graph structure insights.
    Combines symbolic graph analysis with natural language generation.
    """
    
    def __init__(self, llm_model, graph, embedding_engine):
        self.llm = llm_model
        self.graph = graph
        self.embeddings = embedding_engine
    
    def answer_with_structure(
        self,
        question: str,
        symptom: str,
        basic_correlations: List[Tuple[str, int]]
    ) -> Dict:
        """
        Generate answer using both correlations and structural insights.
        
        Args:
            question: User's original question
            symptom: Extracted symptom
            basic_correlations: List of (ingredient, count) from graph query
        
        Returns:
            Dict with answer, reasoning steps, and structural insights
        """
        # Get structural insights if embeddings available
        structural_insights = []
        if self.embeddings.is_trained and basic_correlations:
            top_ingredient = basic_correlations[0][0]
            
            # Find similar ingredients
            similar = self.embeddings.get_similar_nodes(
                top_ingredient,
                top_k=3,
                node_type='ingredient'
            )
            
            if similar:
                structural_insights.append({
                    "type": "similar_ingredients",
                    "primary": top_ingredient,
                    "similar": [s[0] for s in similar],
                    "explanation": f"Structurally similar to {top_ingredient} in the graph"
                })
        
        # Build enhanced prompt
        prompt = self._build_reasoning_prompt(
            question,
            symptom,
            basic_correlations,
            structural_insights
        )
        
        # Get LLM response
        response = self.llm.generate_content(prompt)
        answer = response.text.strip()
        
        # Parse reasoning steps if provided
        reasoning_steps = self._extract_reasoning_steps(answer)
        
        return {
            "answer": answer,
            "reasoning_steps": reasoning_steps,
            "structural_insights": structural_insights,
            "confidence": self._estimate_confidence(basic_correlations)
        }
    
    def _build_reasoning_prompt(
        self,
        question: str,
        symptom: str,
        correlations: List[Tuple[str, int]],
        structural_insights: List[Dict]
    ) -> str:
        """Build enhanced prompt with graph context."""
        
        corr_text = "\n".join([
            f"- {ing}: seen {count} time(s)"
            for ing, count in correlations[:5]
        ])
        
        structural_text = ""
        if structural_insights:
            for insight in structural_insights:
                if insight["type"] == "similar_ingredients":
                    similar = ", ".join(insight["similar"])
                    structural_text += f"\nGraph analysis shows {insight['primary']} is structurally similar to: {similar}"
        
        prompt = f"""You're analyzing food and health data from a personal knowledge graph.

Question: {question}
Detected symptom: {symptom}

Data from graph:
{corr_text}
{structural_text}

Provide a clear, helpful answer that:
1. Explains what the data shows
2. Suggests why these foods might be related
3. Keeps it conversational and practical

Answer:"""
        
        return prompt
    
    def _extract_reasoning_steps(self, text: str) -> List[str]:
        """Extract numbered steps or bullet points from LLM response."""
        steps = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '-', '•')):
                clean = line.lstrip('0123456789.-•• \t')
                if clean:
                    steps.append(clean)
        return steps
    
    def _estimate_confidence(self, correlations: List[Tuple[str, int]]) -> str:
        """Estimate confidence based on data quantity."""
        if not correlations:
            return "low"
        
        max_count = correlations[0][1]
        num_items = len(correlations)
        
        if max_count >= 5 and num_items >= 3:
            return "high"
        elif max_count >= 3 or num_items >= 2:
            return "medium"
        else:
            return "low"
    
    def explain_prediction(
        self,
        predicted_symptom: str,
        meal_ingredients: List[str]
    ) -> Dict:
        """
        Explain why a symptom might occur given ingredients.
        Uses graph paths and embeddings.
        """
        paths = []
        
        # Find graph paths from ingredients to symptom
        for ingredient in meal_ingredients[:3]:
            try:
                if self.graph.graph.has_node(ingredient) and \
                   self.graph.graph.has_node(predicted_symptom):
                    
                    path = self.graph.find_path(ingredient, predicted_symptom)
                    if path:
                        paths.append({
                            "from": ingredient,
                            "to": predicted_symptom,
                            "path": path
                        })
            except:
                continue
        
        # Build explanation prompt
        prompt = f"""Explain why someone might experience "{predicted_symptom}" after eating: {', '.join(meal_ingredients)}

Based on the data patterns, provide a simple explanation focusing on nutritional properties."""
        
        response = self.llm.generate_content(prompt)
        
        return {
            "explanation": response.text.strip(),
            "graph_paths": paths,
            "confidence": "medium" if paths else "low"
        }
