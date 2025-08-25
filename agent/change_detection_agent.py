import time
import json
from collections import defaultdict
from datetime import datetime

class ChangeDetectionAgent:
    """
    The Change Detection Agent monitors external data sources for new information
    or changes. It performs a lightweight data acquisition and synthesis,
    then compares the new knowledge snapshot with the existing synthesized knowledge
    on the blackboard to identify new articles.
    """
    def __init__(self, name: str, blackboard, data_acquisition_agent, knowledge_synthesis_agent):
        self.name = name
        self.blackboard = blackboard
        self.data_acquisition_agent = data_acquisition_agent
        self.knowledge_synthesis_agent = knowledge_synthesis_agent
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        """Callback triggered when observed blackboard status changes."""
        if key == "status" and value == "check_for_changes_requested":
            self.execute_change_detection()

    def execute_change_detection(self):
        """
        Performs a comparison between the current knowledge graph and a fresh scrape
        to detect new articles.
        """
        print(f"\n{self.name}: Task received: Check for changes. Initiating comparison.")
        
        current_synthesized_data = self.blackboard.get_data("synthesized_knowledge")

        if not current_synthesized_data or "extracted_entities" not in current_synthesized_data:
            report_text = f"Change Detection: No existing knowledge graph found to compare against."
            self.blackboard.set_data("change_detection_report", report_text)
            self.blackboard.set_status("no_changes_detected") # Or a more specific error status
            print(f"{self.name}: {report_text}")
            return

        current_article_titles = {
            article['properties']['title'].lower() 
            for article in current_synthesized_data["extracted_entities"].get("nodes", {}).get("articles", [])
        }

        # --- Perform a fresh, lightweight scrape and synthesis for comparison ---
        user_query_for_scraper = self.blackboard.get_data("user_query") # Reuse original query context
        source_url = "https://perinim.github.io/projects" # Fixed source for this demo

        print(f"{self.name}: Performing temporary data acquisition for comparison...")
        raw_data_for_comparison = self.data_acquisition_agent._perform_acquisition(user_query_for_scraper, source_url)
        
        if not raw_data_for_comparison:
            report_text = f"Change Detection: Failed to acquire fresh data for comparison."
            self.blackboard.set_data("change_detection_report", report_text)
            self.blackboard.set_status("no_changes_detected")
            print(f"{self.name}: {report_text}")
            return

        print(f"{self.name}: Performing temporary knowledge synthesis for comparison...")
        candidate_knowledge_graph = self.knowledge_synthesis_agent._perform_synthesis(raw_data_for_comparison)

        if not candidate_knowledge_graph or "extracted_entities" not in candidate_knowledge_graph:
            report_text = f"Change Detection: Failed to synthesize candidate knowledge graph for comparison."
            self.blackboard.set_data("change_detection_report", report_text)
            self.blackboard.set_status("no_changes_detected")
            print(f"{self.name}: {report_text}")
            return
        
        candidate_article_titles = {
            article['properties']['title'].lower() 
            for article in candidate_knowledge_graph["extracted_entities"].get("nodes", {}).get("articles", [])
        }

        # --- Compare the two sets of article titles ---
        new_articles_titles = candidate_article_titles - current_article_titles

        report_text = f"### MARA Change Detection Report\n\n"
        report_text += f"**Timestamp:** {datetime.now().isoformat()}\n\n"

        if new_articles_titles:
            report_text += f"**Detected Changes: New Articles Found!**\n\n"
            report_text += f"The following new article(s) were identified:\n"
            for title in new_articles_titles:
                report_text += f"- '{title.title()}'\n"
            
            # Optionally, trigger a full refresh here or just report
            # For this iteration, we just report. Orchestrator can decide to refresh.
            self.blackboard.set_data("change_detection_report", report_text)
            self.blackboard.set_status("changes_detected")
            print(f"{self.name}: Changes detected and reported.")
        else:
            report_text += "**Detected Changes: None.**\n\n"
            report_text += "No new articles were found compared to the current knowledge graph."
            self.blackboard.set_data("change_detection_report", report_text)
            self.blackboard.set_status("no_changes_detected")
            print(f"{self.name}: No changes detected.")
        time.sleep(1)
