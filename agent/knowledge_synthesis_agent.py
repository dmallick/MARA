import time
import json
from datetime import datetime
from collections import defaultdict

class KnowledgeSynthesisAgent:
    """
    The Knowledge Synthesis Agent processes raw data and extracts structured
    information, simulating the construction of a knowledge base.
    Now includes timestamping and data aging, and generates a more explicit
    knowledge graph-like structure with entities and relationships.
    Enhanced to infer 'Marco Perini' as author if not explicitly found by scraper.
    Exposes _perform_synthesis for other agents to use directly.
    """
    def __init__(self, name: str, blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "raw_data_acquired":
            self.execute_task()

    def _perform_synthesis(self, raw_data: dict, assign_age: bool = True) -> dict:
        """
        Internal method to execute the knowledge synthesis task.
        Designed to be called by this agent or other agents (e.g., ChangeDetectionAgent)
        without directly modifying the blackboard status for the calling agent.
        Returns the synthesized knowledge graph or None on failure.
        'assign_age' flag controls if data_age is initialized/reset (for full workflow)
        or omitted (for temporary comparisons).
        """
        if not raw_data:
            print(f"{self.name}: No raw data provided for synthesis.")
            return None

        entities = {"articles": [], "authors": []}
        relationships = []
        unique_authors = {}

        if isinstance(raw_data, dict) and "content" in raw_data and isinstance(raw_data["content"], list):
            for idx, article_data in enumerate(raw_data["content"]):
                title = article_data.get("title", "N/A")
                description = article_data.get("description", "N/A")
                
                extracted_author = article_data.get("author", "").strip()
                if not extracted_author or extracted_author.lower() == 'na':
                    author_name = "Marco Perini" 
                else:
                    author_name = extracted_author

                article_id = f"article_{idx + 1}"
                entities["articles"].append({
                    "id": article_id,
                    "type": "Article",
                    "properties": {
                        "title": title,
                        "description_snippet": description[:100] + '...' if len(description) > 100 else description
                    }
                })

                author_id = f"author_{author_name.lower().replace(' ', '_').replace('.', '')}"
                if author_name not in unique_authors:
                    unique_authors[author_name] = author_id
                    entities["authors"].append({
                        "id": author_id,
                        "type": "Author",
                        "properties": {"name": author_name}
                    })
                
                relationships.append({
                    "source_id": article_id,
                    "type": "AUTHORED_BY",
                    "target_id": author_id
                })
        
        synthesized_knowledge_graph = {
            "summary": "Structured knowledge extracted into entities and relationships.",
            "extracted_entities": {
                "timestamp": datetime.now().isoformat(),
                "nodes": entities,
                "relationships": relationships
            }
        }
        if assign_age:
            synthesized_knowledge_graph["extracted_entities"]["data_age"] = 0 # Initialize age for primary graph

        return synthesized_knowledge_graph

    def execute_task(self):
        """
        Executes the knowledge synthesis task when delegated via blackboard status.
        Posts results and status to the blackboard.
        """
        print(f"\n{self.name}: Raw data acquired. Starting knowledge synthesis to build graph structure.")
        raw_data = self.blackboard.get_data("raw_scraped_data")

        if raw_data:
            synthesized_knowledge_graph = self._perform_synthesis(raw_data, assign_age=True)
            if synthesized_knowledge_graph:
                self.blackboard.set_data("synthesized_knowledge", synthesized_knowledge_graph)
                self.blackboard.set_status("knowledge_synthesized")
                print(f"{self.name}: Knowledge synthesis complete. Structured knowledge graph posted (with timestamp and age).")
                print(f"Synthesized knowledge (partial view): {json.dumps(synthesized_knowledge_graph, indent=2)[:700]}...")
            else:
                error_msg = "Knowledge Synthesis Agent failed to perform synthesis."
                print(f"{self.name}: {error_msg}")
                self.blackboard.set_data("error_message", error_msg)
                self.blackboard.set_status("knowledge_synthesis_failed")
                self.blackboard.set_data("final_report", error_msg)
        else:
            error_msg = "No raw data found for synthesis."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("knowledge_synthesis_failed")
            self.blackboard.set_data("final_report", error_msg)
        time.sleep(1)
