"""
NutriGraph - Graph Construction Test
Proves the graph architecture works with the pipeline output
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import networkx as nx
from pyvis.network import Network
from typing import Optional, Union, Dict, List, Any

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class NutriGraph:
    """
    Implements the NutriGraph architecture:
    - Node Types: Meal, Ingredient, Nutrient, UserLog
    - Edge Types: CONTAINS, HAS_NUTRIENT, LOGGED_NEAR
    """
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.meal_counter = 0
        self.log_counter = 0
        
    def add_meal(self, ingredients_json: Dict[str, List[str]], nutrients_json: Dict[str, List[str]], timestamp: Optional[str] = None, photo_url: Optional[str] = None) -> str:
        """
        Add a meal to the graph with all its ingredients and nutrients.
        
        Args:
            ingredients_json: {"ingredients": ["ingredient1", "ingredient2", ...]}
            nutrients_json: {"ingredient1": ["Nutrient1", "Nutrient2"], ...}
            timestamp: Optional meal timestamp (defaults to now)
            photo_url: Optional path to meal photo
        
        Returns:
            meal_id: The ID of the created meal node
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        # Create Meal node
        meal_id = f"meal_{self.meal_counter}"
        self.meal_counter += 1
        
        self.graph.add_node(
            meal_id,
            node_type="Meal",
            timestamp=timestamp,
            photo_url=photo_url or "N/A",
            label=f"Meal\n{timestamp.split('T')[0]}"
        )
        
        # Process ingredients
        ingredients_list = ingredients_json.get("ingredients", [])
        
        for ingredient_name in ingredients_list:
            # Create or get Ingredient node
            ingredient_id = f"ingredient_{ingredient_name.lower().replace(' ', '_')}"
            
            if ingredient_id not in self.graph:
                self.graph.add_node(
                    ingredient_id,
                    node_type="Ingredient",
                    name=ingredient_name,
                    label=ingredient_name.title()
                )
            
            # Create CONTAINS edge: Meal -> Ingredient
            self.graph.add_edge(
                meal_id,
                ingredient_id,
                edge_type="CONTAINS",
                label="contains"
            )
            
            # Add nutrients for this ingredient
            nutrients_list = nutrients_json.get(ingredient_name, [])
            
            for nutrient_name in nutrients_list:
                # Create or get Nutrient node
                nutrient_id = f"nutrient_{nutrient_name.lower().replace(' ', '_')}" # Possible issue: if LLM returns similar ingredient names, named differently.
                
                if nutrient_id not in self.graph:
                    self.graph.add_node(
                        nutrient_id,
                        node_type="Nutrient",
                        name=nutrient_name,
                        label=nutrient_name
                    )
                
                # Create HAS_NUTRIENT edge: Ingredient -> Nutrient
                self.graph.add_edge(
                    ingredient_id,
                    nutrient_id,
                    edge_type="HAS_NUTRIENT",
                    label="has"
                )
        
        return meal_id
    
    def add_user_log(self, symptom, sentiment, timestamp=None, time_window_hours=3):
        """
        Add a user symptom/feeling log and correlate it with recent meals.
        
        Args:
            symptom: The symptom name (e.g., "High Energy", "Headache")
            sentiment: "positive" or "negative"
            timestamp: Optional log timestamp (defaults to now)
            time_window_hours: How many hours back to look for meal correlations
        
        Returns:
            log_id: The ID of the created log node
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        # Create UserLog node
        log_id = f"log_{self.log_counter}"
        self.log_counter += 1
        
        self.graph.add_node(
            log_id,
            node_type="UserLog",
            symptom=symptom,
            sentiment=sentiment,
            timestamp=timestamp,
            label=f"{symptom}\n({sentiment})"
        )
        """
        # Find recent meals and create LOGGED_NEAR edges
        # Possible upgrade to use time windows between meals
        # For this prototype we'll just connect to all existing meals
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "Meal":
                self.graph.add_edge(
                    node_id,
                    log_id,
                    edge_type="LOGGED_NEAR",
                    label="logged near"
                )
            # Core issue to solve is daily reset or something
            """
        # Fix to previous test: Only parse LOGGED_NEAR based on timestamp difference
        log_time = datetime.now().fromisoformat(timestamp)
        timewindow = timedelta(hours=time_window_hours)

        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "Meal":
                meal_time_str = node_data.get("timestamp")
                if not meal_time_str:
                    continue
                
                meal_time = datetime.fromisoformat(meal_time_str)

                difference = log_time - meal_time

                if timedelta(seconds=0) < difference <= timewindow:
                    rounded_diff = round(difference.total_seconds() / 3600, 1)
                    self.graph.add_edge(
                        node_id,
                        log_id,
                        edge_type="LOGGED_NEAR",
                        label=f"logged near {rounded_diff} hours ago"
                    )
        
        return log_id
    
    def query_ingredients_for_symptom(self, symptom):
        """
        Query which ingredients are correlated with a symptom.
        This is the key insight-generation query.
        
        Returns:
            List of (ingredient_name, correlation_count) tuples
        """
        ingredient_counts = {}
        
        # Find all UserLog nodes with this symptom
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "UserLog" and node_data.get("symptom") == symptom:
                # Traverse backwards: UserLog <- LOGGED_NEAR <- Meal <- CONTAINS <- Ingredient
                for meal_id in self.graph.predecessors(node_id):
                    meal_data = self.graph.nodes[meal_id]
                    if meal_data.get("node_type") == "Meal":
                        for ingredient_id in self.graph.successors(meal_id):
                            ingredient_data = self.graph.nodes[ingredient_id]
                            if ingredient_data.get("node_type") == "Ingredient":
                                ingredient_name = ingredient_data.get("name")
                                ingredient_counts[ingredient_name] = ingredient_counts.get(ingredient_name, 0) + 1
        
        # Sort by correlation count
        return sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_stats(self):
        """Get graph statistics"""
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "meals": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "Meal"),
            "ingredients": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "Ingredient"),
            "nutrients": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "Nutrient"),
            "user_logs": sum(1 for _, d in self.graph.nodes(data=True) if d.get("node_type") == "UserLog")
        }
        return stats
    
    def visualize(self, output_path="nutrigraph_viz.html"):
        net = Network(height="750px", width="100%", bgcolor="#1a1a1a", font_color="white", directed=True)
        
        # Define colors for node types
        node_colors = {
            "Meal": "#FF6B6B",      # Red
            "Ingredient": "#4ECDC4",  # Teal
            "Nutrient": "#95E1D3",    # Light green
            "UserLog": "#FFE66D"      # Yellow
        }
        
        # Add nodes with styling
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("node_type", "Unknown")
            label = node_data.get("label", node_id)
            color = node_colors.get(node_type, "#CCCCCC")
            
            # Size based on type
            size = 30 if node_type == "Meal" else 20
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                size=size,
                title=f"{node_type}: {node_id}"
            )
        
        # Add edges
        for source, target, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get("edge_type", "unknown")
            net.add_edge(source, target, title=edge_type, arrows="to")
        
        # Configure physics
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 100,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
          }
        }
        """)
        
        # Save - use save_graph instead of show to avoid template issues
        try:
            net.save_graph(output_path)
        except Exception as e:
            # Fallback: generate HTML manually
            print(f"Warning: pyvis save_graph failed ({e}), using fallback method")
            net.write_html(output_path, notebook=False)
        
        return output_path

if __name__ == "__main__":
    print("=" * 80)
    print("NUTRIGRAPH - GRAPH CONSTRUCTION TEST")
    print("=" * 80)
    
    # Initialize graph
    graph = NutriGraph()
    
    # Sample data (from our successful pipeline test)
    ingredients_json = {
        "ingredients": [
            "avocado",
            "cherry tomatoes",
            "red onion",
            "cucumber",
            "cilantro",
            "jalapeño",
            "black pepper"
        ]
    }
    
    nutrients_json = {
        "avocado": ["Healthy Fats", "Fiber", "Potassium"],
        "cherry tomatoes": ["Vitamin C", "Vitamin K", "Potassium"],
        "red onion": ["Vitamin C", "Fiber", "Antioxidants"],
        "cucumber": ["Water", "Vitamin K", "Potassium"],
        "cilantro": ["Vitamin K", "Vitamin C", "Antioxidants"],
        "jalapeño": ["Vitamin C", "Vitamin B6", "Capsaicin"],
        "black pepper": ["Manganese", "Vitamin K", "Antioxidants"]
    }
    
    print(f"Loaded {len(ingredients_json['ingredients'])} ingredients")
    print(f"Loaded nutrients for {len(nutrients_json)} ingredients")
    
    # Add meal to graph
    print("\n[STEP 2] Constructing graph from meal data...")
    print("-" * 80)
    
    meal_id = graph.add_meal(
        ingredients_json,
        nutrients_json,
        timestamp="2025-10-04T12:00:00",
        photo_url="images/avocado-salad.jpg"
    )
    
    print(f"Created meal node: {meal_id}")
    print(f"Graph stats: {json.dumps(graph.get_stats(), indent=2)}")
    
    # Simulate user logging a symptom
    print("\n[STEP 3] Adding user symptom logs...")
    print("-" * 80)
    
    log1 = graph.add_user_log(
        symptom="High Energy",
        sentiment="positive",
        timestamp="2025-10-04T15:00:00"
    )
    print(f"Added user log: {log1} (High Energy)")
    
    ingredients_json2 = {
        "ingredients": ["chicken breast", "broccoli", "rice"]
    }
    nutrients_json2 = {
        "chicken breast": ["Protein", "Low Fat"],
        "broccoli": ["Fiber", "Vitamin C"],
        "rice": ["Carbohydrates", "Energy"]
    }
    
    meal_id2 = graph.add_meal(
        ingredients_json2,
        nutrients_json2,
        timestamp="2025-10-04T18:00:00"
    )
    print(f"Added second meal: {meal_id2}")
    print("Query: 'What ingredients correlate with High Energy?'")
    
    results = graph.query_ingredients_for_symptom("High Energy")
    print(f"\nResults ({len(results)} ingredients found):")
    for ingredient, count in results[:5]:  # Top 5
        print(f"  - {ingredient}: {count} correlation(s)")
    
    # Final stats
    stats = graph.get_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    output_path = Path(__file__).parent / "nutrigraph_viz.html"
    graph.visualize(str(output_path))
    
