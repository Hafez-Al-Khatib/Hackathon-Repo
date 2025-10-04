"""
Graph Embedding Engine using Node2Vec
Converts graph structure into vector embeddings for similarity search
"""

import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Optional
from node2vec import Node2Vec
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from pathlib import Path


class GraphEmbeddingEngine:
    """
    Manages graph embeddings using Node2Vec algorithm.
    Enables structural similarity search and pattern discovery.
    """
    
    def __init__(self, graph: nx.Graph, cache_dir: str = "embeddings_cache"):
        self.graph = graph
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.model = None
        self.embeddings = {}
        self.is_trained = False
    
    def train_embeddings(
        self,
        dimensions: int = 128,
        walk_length: int = 30,
        num_walks: int = 200,
        p: float = 1.0,
        q: float = 1.0,
        workers: int = 4
    ) -> Dict:
        """
        Train Node2Vec embeddings on the graph.
        
        Args:
            dimensions: Embedding vector size
            walk_length: Length of random walks
            num_walks: Number of walks per node
            p: Return parameter (controls likelihood of revisiting nodes)
            q: In-out parameter (controls exploration vs exploitation)
            workers: Number of parallel workers
        
        Returns:
            Dict with training stats
        """
        if self.graph.number_of_nodes() < 5:
            return {
                "status": "skipped",
                "reason": "Not enough nodes",
                "node_count": self.graph.number_of_nodes()
            }
        
        try:
            # Initialize Node2Vec
            node2vec = Node2Vec(
                self.graph,
                dimensions=dimensions,
                walk_length=walk_length,
                num_walks=num_walks,
                p=p,
                q=q,
                workers=workers,
                quiet=True
            )
            
            # Train the model
            self.model = node2vec.fit(window=10, min_count=1, batch_words=4)
            
            # Extract embeddings
            self.embeddings = {
                node: self.model.wv[node] 
                for node in self.graph.nodes()
            }
            
            self.is_trained = True
            
            # Save to cache
            self._save_cache()
            
            return {
                "status": "success",
                "node_count": len(self.embeddings),
                "dimensions": dimensions,
                "total_walks": num_walks * self.graph.number_of_nodes()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_similar_nodes(
        self,
        node_id: str,
        top_k: int = 5,
        node_type: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Find nodes most similar to the given node.
        
        Args:
            node_id: Node to find similarities for
            top_k: Number of similar nodes to return
            node_type: Optional filter by node type (ingredient, symptom, etc.)
        
        Returns:
            List of (node_id, similarity_score) tuples
        """
        if not self.is_trained or node_id not in self.embeddings:
            return []
        
        target_embedding = self.embeddings[node_id].reshape(1, -1)
        similarities = []
        
        for other_id, other_embedding in self.embeddings.items():
            if other_id == node_id:
                continue
            
            # Filter by node type if specified
            if node_type:
                if not self.graph.nodes[other_id].get('type') == node_type:
                    continue
            
            # Compute cosine similarity
            sim = cosine_similarity(
                target_embedding,
                other_embedding.reshape(1, -1)
            )[0][0]
            
            similarities.append((other_id, float(sim)))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_node_embedding(self, node_id: str) -> Optional[np.ndarray]:
        """Get the embedding vector for a specific node."""
        return self.embeddings.get(node_id)
    
    def compute_pattern_embedding(self, node_ids: List[str]) -> Optional[np.ndarray]:
        """
        Compute aggregate embedding for a pattern (multiple nodes).
        Uses mean pooling.
        """
        embeddings = [
            self.embeddings[nid] 
            for nid in node_ids 
            if nid in self.embeddings
        ]
        
        if not embeddings:
            return None
        
        return np.mean(embeddings, axis=0)
    
    def find_similar_patterns(
        self,
        pattern_nodes: List[str],
        candidate_nodes: List[str],
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Find candidate nodes most similar to a pattern.
        Useful for "what else might cause X?" queries.
        """
        if not self.is_trained:
            return []
        
        pattern_embedding = self.compute_pattern_embedding(pattern_nodes)
        if pattern_embedding is None:
            return []
        
        similarities = []
        for candidate in candidate_nodes:
            if candidate in self.embeddings:
                sim = cosine_similarity(
                    pattern_embedding.reshape(1, -1),
                    self.embeddings[candidate].reshape(1, -1)
                )[0][0]
                similarities.append((candidate, float(sim)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def _save_cache(self):
        """Save embeddings to disk."""
        cache_file = self.cache_dir / "embeddings.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump({
                'embeddings': self.embeddings,
                'is_trained': self.is_trained
            }, f)
    
    def _load_cache(self) -> bool:
        """Load embeddings from disk if available."""
        cache_file = self.cache_dir / "embeddings.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data['embeddings']
                    self.is_trained = data['is_trained']
                return True
            except:
                return False
        return False
    
    def get_stats(self) -> Dict:
        """Get embedding engine statistics."""
        return {
            "is_trained": self.is_trained,
            "total_embeddings": len(self.embeddings),
            "embedding_dimension": len(next(iter(self.embeddings.values()))) if self.embeddings else 0,
            "graph_nodes": self.graph.number_of_nodes()
        }
