"""
API endpoints for graph embeddings and enhanced reasoning
"""

from fastapi import HTTPException, Query
from typing import Optional


def create_embedding_endpoints(app, graph, embedding_engine, reasoning_engine):
    """
    Register embedding-related API endpoints.
    
    Args:
        app: FastAPI application
        graph: NutriGraph instance
        embedding_engine: GraphEmbeddingEngine instance
        reasoning_engine: GraphAwareLLMReasoner instance
    
    Returns:
        embeddings_trained flag (list for mutability)
    """
    
    embeddings_trained = [False]
    
    @app.post("/graph/embeddings/train")
    async def train_embeddings(
        dimensions: int = 128,
        walk_length: int = 30,
        num_walks: int = 200
    ):
        """Train Node2Vec embeddings on current graph structure."""
        try:
            if graph.graph.number_of_nodes() < 5:
                return {
                    "status": "skipped",
                    "reason": "Need at least 5 nodes to train embeddings",
                    "current_nodes": graph.graph.number_of_nodes()
                }
            
            result = embedding_engine.train_embeddings(
                dimensions=dimensions,
                walk_length=walk_length,
                num_walks=num_walks
            )
            
            if result["status"] == "success":
                embeddings_trained[0] = True
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/graph/embeddings/status")
    async def get_embedding_status():
        """Check if embeddings are trained and get stats."""
        return embedding_engine.get_stats()
    
    @app.get("/graph/embeddings/similar/{node_id}")
    async def get_similar_nodes(
        node_id: str,
        top_k: int = Query(5, ge=1, le=20),
        node_type: Optional[str] = None
    ):
        """Find nodes similar to the given node."""
        if not embedding_engine.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Embeddings not trained. Call /graph/embeddings/train first"
            )
        
        similar = embedding_engine.get_similar_nodes(
            node_id,
            top_k=top_k,
            node_type=node_type
        )
        
        return {
            "node_id": node_id,
            "similar_nodes": [
                {"node": node, "similarity": score}
                for node, score in similar
            ]
        }
    
    @app.get("/insight/enhanced")
    async def get_enhanced_insight(symptom: str):
        """
        Get insight with enhanced reasoning using graph structure.
        Requires embeddings to be trained.
        """
        # Get basic correlations
        correlations = graph.query_ingredients_for_symptom(symptom)
        
        if not correlations:
            return {
                "symptom": symptom,
                "answer": f"No data yet for '{symptom}'. Log more meals and symptoms.",
                "correlations": [],
                "enhanced": False
            }
        
        # Use enhanced reasoning if available
        if embedding_engine.is_trained:
            result = reasoning_engine.answer_with_structure(
                question=f"What causes {symptom}?",
                symptom=symptom,
                basic_correlations=correlations
            )
            
            return {
                "symptom": symptom,
                "answer": result["answer"],
                "correlations": [
                    {"ingredient": ing, "count": count}
                    for ing, count in correlations[:5]
                ],
                "reasoning_steps": result.get("reasoning_steps", []),
                "structural_insights": result.get("structural_insights", []),
                "confidence": result.get("confidence", "medium"),
                "enhanced": True
            }
        else:
            # Fallback to basic
            return {
                "symptom": symptom,
                "correlations": [
                    {"ingredient": ing, "count": count}
                    for ing, count in correlations[:5]
                ],
                "enhanced": False,
                "message": "Train embeddings for enhanced insights"
            }
    
    @app.post("/predict/symptom")
    async def predict_symptom(ingredients: list[str]):
        """
        Predict potential symptoms for given ingredients.
        Requires embeddings to be trained.
        """
        if not embedding_engine.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Embeddings not trained"
            )
        
        # Find symptoms connected to these ingredients
        all_symptoms = set()
        for ingredient in ingredients:
            if graph.graph.has_node(ingredient):
                # Get neighboring symptoms
                neighbors = graph.graph.neighbors(ingredient)
                for neighbor in neighbors:
                    if graph.graph.nodes[neighbor].get('type') == 'symptom':
                        all_symptoms.add(neighbor)
        
        if not all_symptoms:
            return {
                "ingredients": ingredients,
                "predictions": [],
                "message": "No patterns found for these ingredients"
            }
        
        # Score symptoms by structural similarity
        predictions = []
        for symptom in all_symptoms:
            # Get explanation
            explanation = reasoning_engine.explain_prediction(
                symptom,
                ingredients
            )
            
            predictions.append({
                "symptom": symptom,
                "explanation": explanation["explanation"],
                "confidence": explanation["confidence"]
            })
        
        return {
            "ingredients": ingredients,
            "predictions": predictions
        }
    
    return embeddings_trained
