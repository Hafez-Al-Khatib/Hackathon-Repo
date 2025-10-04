"""
Enhanced NutriGraph with Symptom nodes as first-class entities
"""

import networkx as nx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from pyvis.network import Network


class EnhancedNutriGraph:
    """
    Knowledge graph for meal-symptom correlation analysis.
    
    Node Types:
        - Meal: Individual meal instances (with timestamp)
        - Ingredient: Food items
        - Nutrient: Nutritional properties
        - UserLog: Log entries (with timestamp and sentiment)
        - Symptom: Unique symptoms/feelings (NEW!)
    
    Edge Types:
        - CONTAINS: Meal → Ingredient
        - HAS_NUTRIENT: Ingredient → Nutrient
        - LOGGED_NEAR: Meal → UserLog (time-based correlation)
        - EXPERIENCED: UserLog → Symptom (NEW!)
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.meal_counter = 0
        self.log_counter = 0
        
    def add_meal(
        self, 
        ingredients_json: Dict[str, List[str]], 
        nutrients_json: Dict[str, List[str]], 
        timestamp: Optional[str] = None, 
        photo_url: Optional[str] = None
    ) -> str:
        """
        Add a meal to the graph with all its ingredients and nutrients.
        
        Args:
            ingredients_json: {"ingredients": ["avocado", "tomato", ...]}
            nutrients_json: {"avocado": ["Healthy Fats", ...], ...}
            timestamp: ISO format timestamp
            photo_url: Path to meal photo
        
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
            photo_url=photo_url,
            label=f"Meal {self.meal_counter}"
        )
        
        # Get ingredients list
        ingredients_list = ingredients_json.get("ingredients", [])
        
        # Process each ingredient
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
            
            # Create CONTAINS edge
            self.graph.add_edge(
                meal_id,
                ingredient_id,
                edge_type="CONTAINS",
                label="contains"
            )
            
            # Process nutrients for this ingredient
            nutrients_list = nutrients_json.get(ingredient_name, [])
            
            for nutrient_name in nutrients_list:
                # Create or get Nutrient node
                nutrient_id = f"nutrient_{nutrient_name.lower().replace(' ', '_')}"
                
                if nutrient_id not in self.graph:
                    self.graph.add_node(
                        nutrient_id,
                        node_type="Nutrient",
                        name=nutrient_name,
                        label=nutrient_name
                    )
                
                # Create HAS_NUTRIENT edge
                if not self.graph.has_edge(ingredient_id, nutrient_id):
                    self.graph.add_edge(
                        ingredient_id,
                        nutrient_id,
                        edge_type="HAS_NUTRIENT",
                        label="has nutrient"
                    )
        
        return meal_id
    
    def add_user_log(
        self, 
        symptom: str, 
        sentiment: str = "neutral",
        timestamp: Optional[str] = None,
        time_window_hours: int = 3
    ) -> str:
        """
        Add a user symptom log with separate Symptom node.
        
        Args:
            symptom: The symptom name (e.g., "Bloated", "High Energy")
            sentiment: "positive", "negative", or "neutral"
            timestamp: ISO format timestamp
            time_window_hours: How many hours back to correlate with meals
        
        Returns:
            log_id: The ID of the created log node
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Create UserLog node (WITHOUT symptom as attribute)
        log_id = f"log_{self.log_counter}"
        self.log_counter += 1
        
        self.graph.add_node(
            log_id,
            node_type="UserLog",
            sentiment=sentiment,
            timestamp=timestamp,
            symptom=symptom,  # Store symptom name in node data
            label=f"{symptom}\n({sentiment})"  # Show symptom + sentiment
        )
        
        # Create or get Symptom node
        symptom_id = f"symptom_{symptom.lower().replace(' ', '_')}"
        
        if symptom_id not in self.graph:
            self.graph.add_node(
                symptom_id,
                node_type="Symptom",
                name=symptom,
                label=symptom
            )
        
        # Create EXPERIENCED edge (UserLog → Symptom)
        self.graph.add_edge(
            log_id,
            symptom_id,
            edge_type="EXPERIENCED",
            label="experienced"
        )
        
        # Find meals within time window and create LOGGED_NEAR edges
        log_time = datetime.fromisoformat(timestamp)
        time_window = timedelta(hours=time_window_hours)
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "Meal":
                meal_time_str = node_data.get("timestamp")
                if not meal_time_str:
                    continue
                
                meal_time = datetime.fromisoformat(meal_time_str)
                time_diff = log_time - meal_time
                
                # Create edge if meal was within time window before log
                if timedelta(seconds=0) < time_diff <= time_window:
                    hours_ago = round(time_diff.total_seconds() / 3600, 1)
                    self.graph.add_edge(
                        node_id,
                        log_id,
                        edge_type="LOGGED_NEAR",
                        label=f"{hours_ago}h after meal"
                    )
        
        return log_id
    
    def query_ingredients_for_symptom(self, symptom: str) -> List[tuple]:
        """
        Query which ingredients are correlated with a specific symptom.
        
        This traverses: Symptom ← EXPERIENCED ← UserLog ← LOGGED_NEAR ← Meal → CONTAINS → Ingredient
        
        Args:
            symptom: The symptom to query (e.g., "High Energy", "Bloated")
        
        Returns:
            List of (ingredient_name, count) tuples sorted by frequency
        """
        symptom_id = f"symptom_{symptom.lower().replace(' ', '_')}"
        
        if symptom_id not in self.graph:
            return []
        
        ingredient_counts = {}
        
        # Find all UserLogs that experienced this symptom
        user_logs = list(self.graph.predecessors(symptom_id))
        
        for log_id in user_logs:
            # Find meals logged near this UserLog
            meals = list(self.graph.predecessors(log_id))
            
            for meal_id in meals:
                # Find ingredients in this meal
                ingredients = list(self.graph.successors(meal_id))
                
                for ingredient_id in ingredients:
                    ingredient_data = self.graph.nodes[ingredient_id]
                    if ingredient_data.get("node_type") == "Ingredient":
                        ingredient_name = ingredient_data.get("name", ingredient_id)
                        ingredient_counts[ingredient_name] = ingredient_counts.get(ingredient_name, 0) + 1
        
        # Sort by count (most frequent first)
        sorted_ingredients = sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_ingredients
    
    def get_symptom_frequency(self, symptom: str) -> int:
        """
        Get how many times a symptom has been experienced.
        
        Args:
            symptom: The symptom name
        
        Returns:
            Count of UserLogs that experienced this symptom
        """
        symptom_id = f"symptom_{symptom.lower().replace(' ', '_')}"
        
        if symptom_id not in self.graph:
            return 0
        
        # Count incoming EXPERIENCED edges
        return len(list(self.graph.predecessors(symptom_id)))
    
    def get_all_symptoms(self) -> List[Dict[str, Any]]:
        """
        Get all unique symptoms the user has experienced.
        
        Returns:
            List of dicts with symptom info and frequency
        """
        symptoms = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "Symptom":
                symptom_name = node_data.get("name", node_id)
                frequency = len(list(self.graph.predecessors(node_id)))
                
                symptoms.append({
                    "name": symptom_name,
                    "frequency": frequency,
                    "node_id": node_id
                })
        
        # Sort by frequency
        symptoms.sort(key=lambda x: x["frequency"], reverse=True)
        
        return symptoms
    
    def get_co_occurring_symptoms(self, symptom: str) -> List[tuple]:
        """
        Find symptoms that often occur together with the given symptom.
        
        This finds other symptoms experienced in the same UserLog or nearby time.
        
        Args:
            symptom: The symptom to analyze
        
        Returns:
            List of (other_symptom, co_occurrence_count) tuples
        """
        symptom_id = f"symptom_{symptom.lower().replace(' ', '_')}"
        
        if symptom_id not in self.graph:
            return []
        
        co_occurrence_counts = {}
        
        # Find all UserLogs that experienced this symptom
        user_logs = list(self.graph.predecessors(symptom_id))
        
        for log_id in user_logs:
            log_time_str = self.graph.nodes[log_id].get("timestamp")
            if not log_time_str:
                continue
            
            log_time = datetime.fromisoformat(log_time_str)
            
            # Find other UserLogs within 1 hour
            for other_log_id, other_log_data in self.graph.nodes(data=True):
                if other_log_data.get("node_type") == "UserLog" and other_log_id != log_id:
                    other_time_str = other_log_data.get("timestamp")
                    if not other_time_str:
                        continue
                    
                    other_time = datetime.fromisoformat(other_time_str)
                    time_diff = abs((log_time - other_time).total_seconds())
                    
                    # Within 1 hour
                    if time_diff <= 3600:
                        # Find symptoms in this other log
                        other_symptoms = list(self.graph.successors(other_log_id))
                        for other_symptom_id in other_symptoms:
                            if self.graph.nodes[other_symptom_id].get("node_type") == "Symptom":
                                if other_symptom_id != symptom_id:
                                    other_symptom_name = self.graph.nodes[other_symptom_id].get("name")
                                    co_occurrence_counts[other_symptom_name] = co_occurrence_counts.get(other_symptom_name, 0) + 1
        
        sorted_co_occurrences = sorted(co_occurrence_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_co_occurrences
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the graph"""
        stats = {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "meals": 0,
            "ingredients": 0,
            "nutrients": 0,
            "user_logs": 0,
            "symptoms": 0  # NEW!
        }
        
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("node_type", "")
            if node_type == "Meal":
                stats["meals"] += 1
            elif node_type == "Ingredient":
                stats["ingredients"] += 1
            elif node_type == "Nutrient":
                stats["nutrients"] += 1
            elif node_type == "UserLog":
                stats["user_logs"] += 1
            elif node_type == "Symptom":
                stats["symptoms"] += 1
        
        return stats
    
    def visualize(self, output_path: str = "graph_viz.html"):
        """Create an interactive visualization of the graph"""
        net = Network(
            height="750px",
            width="100%",
            directed=True,
            notebook=False
        )
        
        # Color mapping for node types
        color_map = {
            "Meal": "#ff6b6b",           # Red
            "Ingredient": "#4ecdc4",      # Teal
            "Nutrient": "#95e1d3",        # Light green
            "UserLog": "#ffe66d",         # Yellow
            "Symptom": "#a8dadc"          # Light blue
        }
        
        # Add nodes with colors and detailed info
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get("node_type", "Unknown")
            label = node_data.get("label", node_id)
            color = color_map.get(node_type, "#cccccc")
            
            # Create detailed hover title
            if node_type == "UserLog":
                symptom = node_data.get("symptom", "Unknown")
                sentiment = node_data.get("sentiment", "neutral")
                timestamp = node_data.get("timestamp", "")
                title = f"UserLog: {symptom}\nSentiment: {sentiment}\nTime: {timestamp}"
            elif node_type == "Symptom":
                name = node_data.get("name", label)
                title = f"Symptom: {name}"
            elif node_type == "Meal":
                timestamp = node_data.get("timestamp", "")
                title = f"Meal\nTime: {timestamp}"
            else:
                title = f"{node_type}: {label}"
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                title=title
            )
        
        # Add edges
        for source, target, edge_data in self.graph.edges(data=True):
            edge_label = edge_data.get("label", "")
            net.add_edge(source, target, label=edge_label, arrows="to")
        
        # Physics settings
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
        
        net.save_graph(output_path)
        return output_path


if __name__ == "__main__":
    print("=" * 80)
    print("ENHANCED NUTRIGRAPH - SYMPTOM NODES DEMO")
    print("=" * 80)
    
    graph = EnhancedNutriGraph()
    
    # Add a meal
    print("\n[1] Adding avocado salad meal...")
    meal1_id = graph.add_meal(
        {"ingredients": ["avocado", "cherry tomatoes", "cucumber"]},
        {
            "avocado": ["Healthy Fats", "Fiber"],
            "cherry tomatoes": ["Vitamin C", "Antioxidants"],
            "cucumber": ["Hydration", "Vitamin K"]
        },
        timestamp="2025-10-04T12:00:00"
    )
    print(f"   Created: {meal1_id}")
    
    # Log multiple symptoms from natural language
    print("\n[2] User logs: 'Feeling energetic but slightly bloated'")
    log1_id = graph.add_user_log("High Energy", "positive", "2025-10-04T14:00:00")
    log2_id = graph.add_user_log("Bloated", "negative", "2025-10-04T14:00:00")
    print(f"   Created: {log1_id} (High Energy)")
    print(f"   Created: {log2_id} (Bloated)")
    
    # Add another meal
    print("\n[3] Adding pizza meal...")
    meal2_id = graph.add_meal(
        {"ingredients": ["cheese", "tomato sauce", "dough"]},
        {
            "cheese": ["Protein", "Calcium", "Fat"],
            "tomato sauce": ["Vitamin C", "Lycopene"],
            "dough": ["Carbohydrates"]
        },
        timestamp="2025-10-05T18:00:00"
    )
    print(f"   Created: {meal2_id}")
    
    # Log symptom
    print("\n[4] User logs: 'Feeling so bloated and sluggish'")
    log3_id = graph.add_user_log("Bloated", "negative", "2025-10-05T20:00:00")
    log4_id = graph.add_user_log("Sluggish", "negative", "2025-10-05T20:00:00")
    print(f"   Created: {log3_id} (Bloated again!)")
    print(f"   Created: {log4_id} (Sluggish)")
    
    # Query insights
    print("\n[5] QUERY: What makes me feel bloated?")
    bloated_ingredients = graph.query_ingredients_for_symptom("Bloated")
    print("   Correlated ingredients:")
    for ingredient, count in bloated_ingredients:
        print(f"     - {ingredient}: {count} time(s)")
    
    # Get symptom frequency
    print("\n[6] How many times felt 'Bloated'?")
    bloated_count = graph.get_symptom_frequency("Bloated")
    print(f"   Bloated: {bloated_count} times")
    
    # Get all symptoms
    print("\n[7] All symptoms experienced:")
    all_symptoms = graph.get_all_symptoms()
    for symptom_info in all_symptoms:
        print(f"   - {symptom_info['name']}: {symptom_info['frequency']} time(s)")
    
    # Get co-occurring symptoms
    print("\nSymptoms that co-occur with 'Bloated':")
    co_symptoms = graph.get_co_occurring_symptoms("Bloated")
    if co_symptoms:
        for symptom, count in co_symptoms:
            print(f"   - {symptom}: {count} time(s)")
    else:
        print("   (none found)")
    
    # Stats
    print("\nGraph Statistics:")
    stats = graph.get_stats()
    print(f"   Total Nodes:  {stats['total_nodes']}")
    print(f"   Total Edges:  {stats['total_edges']}")
    print(f"   Meals:        {stats['meals']}")
    print(f"   Ingredients:  {stats['ingredients']}")
    print(f"   Nutrients:    {stats['nutrients']}")
    print(f"   User Logs:    {stats['user_logs']}")
    print(f"   Symptoms:     {stats['symptoms']} <- NEW!")

    print("\nCreating visualization...")
    viz_path = graph.visualize("enhanced_graph_viz.html")
    print(f"   Saved to: {viz_path}")
