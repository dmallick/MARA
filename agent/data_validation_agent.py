import time
import json # Potentially used for logging/debugging data structures

class DataValidationAgent:
    """
    The Data Validation Agent performs quality checks on the synthesized data.
    """
    def __init__(self, name: str, blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "knowledge_synthesized":
            self.execute_task()

    def execute_task(self):
        print(f"\n{self.name}: Knowledge synthesized. Starting data validation.")
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        
        validation_result = {"is_valid": False, "notes": "No data for validation."}

        if synthesized_data and "extracted_entities" in synthesized_data and \
           "nodes" in synthesized_data["extracted_entities"] and \
           "relationships" in synthesized_data["extracted_entities"]:
            
            nodes = synthesized_data["extracted_entities"]["nodes"]
            relationships = synthesized_data["extracted_entities"]["relationships"]

            if nodes.get("articles") and nodes.get("authors") and relationships:
                is_valid = True
                notes = "Graph structure with articles, authors, and relationships is present."
            else:
                is_valid = False
                notes = "Knowledge graph structure is incomplete (missing nodes or relationships)."
            
            validation_result = {"is_valid": is_valid, "notes": notes}
            self.blackboard.set_data("validation_result", validation_result)
            self.blackboard.set_status("data_validated")
            print(f"{self.name}: Data validation complete. Result posted: {validation_result}")
        else:
            error_msg = "No valid knowledge graph structure found for validation."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("data_validation_failed")
            self.blackboard.set_data("final_report", error_msg)
        time.sleep(1)
