import os
import time
import json
import threading
from collections import defaultdict

from scrapegraphai.graphs import SmartScraperGraph

# --- 1. Blackboard Implementation (Central Shared Repository) ---
# The Blackboard acts as the central communication and data-sharing medium
# for all agents. It holds the current state of the research process,
# and agents interact with it to post information, retrieve tasks, and share findings.
class Blackboard:
    def __init__(self):
        # Stores shared data, indexed by data type or task ID
        self._data = {}
        # Stores the current status of the overall workflow or specific tasks
        self._status = "idle"
        # A simple mechanism for agents to "observe" changes (for later, more complex eventing)
        self._observers = defaultdict(list)
        # Lock for safe concurrent access to the blackboard
        self._lock = threading.Lock()

    def set_data(self, key: str, value):
        """Posts data to the blackboard under a specific key."""
        with self._lock:
            self._data[key] = value
            print(f"Blackboard: Data '{key}' posted.")
            self._notify_observers(key) # Notify any agents observing this key

    def get_data(self, key: str):
        """Retrieves data from the blackboard."""
        with self._lock:
            return self._data.get(key)

    def set_status(self, new_status: str):
        """Updates the overall system status on the blackboard."""
        with self._lock:
            self._status = new_status
            print(f"Blackboard: Status updated to '{new_status}'.")
            self._notify_observers("status") # Notify agents observing overall status

    def get_status(self):
        """Retrieves the current system status."""
        with self._lock:
            return self._status

    def register_observer(self, key: str, agent_callback):
        """
        Allows an agent to register a callback function to be notified
        when data under 'key' changes. (Simplified for this phase)
        """
        with self._lock:
            self._observers[key].append(agent_callback)
            print(f"Blackboard: Agent registered as observer for '{key}'.")

    def _notify_observers(self, key: str):
        """Notifies registered observers that data under 'key' has changed."""
        for callback in self._observers[key]:
            # In a real system, this might involve threading or a message queue
            # to avoid blocking. For simplicity, direct call for now.
            try:
                callback(key, self._data.get(key) if key != "status" else self._status)
            except Exception as e:
                print(f"Blackboard: Error notifying observer for '{key}': {e}")

# Instantiate the central blackboard
shared_blackboard = Blackboard()


# --- 2. Agent Definitions (Modular Python Classes) ---

# Each agent is now represented as a Python class, encapsulating its logic
# and providing a clear interface for interaction with the blackboard.

class OrchestratorAgent:
    """
    The Orchestrator Agent's role is expanded beyond the MVP to include
    more sophisticated task decomposition and delegation based on user queries.
    It oversees the entire research workflow.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")

    def run(self, user_query: str):
        """
        Receives the initial user query, decomposes it, and delegates tasks
        by updating the blackboard.
        """
        print(f"{self.name}: Received user query: '{user_query}'")
        self.blackboard.set_data("user_query", user_query)
        
        # Simulate intelligent task decomposition
        if "articles" in user_query.lower() and "description" in user_query.lower():
            task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
            print(f"{self.name}: Decomposed query. Delegating 'web_scrape' task.")
            self.blackboard.set_data("current_task", task)
            self.blackboard.set_status("task_delegated_to_data_acquisition")
        else:
            print(f"{self.name}: Query not recognized for current capabilities. Setting status to 'unsupported_query'.")
            self.blackboard.set_status("unsupported_query")
            self.blackboard.set_data("final_report", "Orchestrator: The current system can only process queries related to 'articles' and 'description' for web scraping.")
        time.sleep(1) # Simulate processing time


class DataAcquisitionAgent:
    """
    The Data Acquisition Agent is responsible for gathering raw data, primarily
    through web scraping, and posting it to the blackboard.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        # Register to observe status changes on the blackboard
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        """Callback triggered when observed blackboard data changes."""
        if key == "status" and value == "task_delegated_to_data_acquisition":
            self.execute_task()

    def execute_task(self):
        """Executes the data acquisition task when delegated."""
        print(f"\n{self.name}: Task delegated. Starting web scraping.")
        
        task = self.blackboard.get_data("current_task")
        if not task or task["type"] != "web_scrape":
            print(f"{self.name}: No valid web_scrape task found on blackboard.")
            self.blackboard.set_status("data_acquisition_failed")
            return

        user_query_for_scraper = self.blackboard.get_data("user_query")
        source_url = task.get("source_url", "https://example.com") # Default or get from task

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"{self.name}: OPENAI_API_KEY environment variable not set. Cannot proceed with scraping.")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", "Error: OPENAI_API_KEY is not set.")
            return

        graph_config = {
           "llm": {
              "api_key": openai_key,
              "model": "openai/gpt-4o",
           },
        }

        try:
            # Use ScrapeGraphAI to perform the intelligent scraping
            scraper = SmartScraperGraph(
                prompt=user_query_for_scraper,
                source=source_url,
                config=graph_config
            )
            result = scraper.run()
            
            # Post the scraped data to the blackboard
            self.blackboard.set_data("raw_scraped_data", result)
            self.blackboard.set_status("raw_data_acquired")
            print(f"{self.name}: Scraping complete. Raw data posted to blackboard.")
            print(f"Raw scraped data (partial view): {json.dumps(result, indent=2)[:500]}...") # Print first 500 chars
        except Exception as e:
            print(f"{self.name}: An error occurred during scraping - {e}")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", f"Error: Web scraping failed with error: {e}")
        time.sleep(1)


class KnowledgeSynthesisAgent:
    """
    (Stub) The Knowledge Synthesis Agent will process raw data and build
    a structured knowledge base (e.g., a temporal knowledge graph).
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "raw_data_acquired":
            self.execute_task()

    def execute_task(self):
        print(f"\n{self.name}: Raw data acquired. Starting knowledge synthesis (stub).")
        raw_data = self.blackboard.get_data("raw_scraped_data")
        if raw_data:
            # Placeholder for complex knowledge graph construction logic
            synthesized_data = {"processed_summary": f"Synthesized knowledge from {len(json.dumps(raw_data))} bytes of raw data."}
            self.blackboard.set_data("synthesized_knowledge", synthesized_data)
            self.blackboard.set_status("knowledge_synthesized")
            print(f"{self.name}: Knowledge synthesis complete (stub). Knowledge posted.")
        else:
            print(f"{self.name}: No raw data found for synthesis.")
            self.blackboard.set_status("knowledge_synthesis_failed")
        time.sleep(1)


class DataValidationAgent:
    """
    (Stub) The Data Validation Agent will perform quality checks on the data.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "knowledge_synthesized":
            self.execute_task()

    def execute_task(self):
        print(f"\n{self.name}: Knowledge synthesized. Starting data validation (stub).")
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        if synthesized_data:
            # Placeholder for actual validation logic
            validation_result = {"is_valid": True, "notes": "Data appears valid (stub)."}
            self.blackboard.set_data("validation_result", validation_result)
            self.blackboard.set_status("data_validated")
            print(f"{self.name}: Data validation complete (stub). Result posted.")
        else:
            print(f"{self.name}: No synthesized data found for validation.")
            self.blackboard.set_status("data_validation_failed")
        time.sleep(1)


class AnalysisAndReportingAgent:
    """
    The Analysis & Reporting Agent monitors the blackboard for 'data_validated' status.
    Once data is available, it processes it and generates the final report.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "data_validated":
            self.execute_task()
        elif key == "status" and (value == "data_acquisition_failed" or value == "unsupported_query"):
            # If a previous step failed, this agent can still try to report the failure
            self.execute_failure_report()

    def execute_task(self):
        print(f"\n{self.name}: Data validated. Generating final report.")
        raw_data = self.blackboard.get_data("raw_scraped_data") # Use raw data for direct report in MVP
        # In full phase II, it would use synthesized_knowledge and validation_result
        
        report_text = "### MARA Research Report\n\n"
        if raw_data:
            report_text += "#### Scraped Articles Overview:\n\n"
            if isinstance(raw_data, dict) and "articles" in raw_data:
                for article in raw_data["articles"]:
                    title = article.get("title", "N/A")
                    description = article.get("description", "N/A")
                    author = article.get("author", "N/A")
                    report_text += f"- **Title:** {title}\n  - **Description:** {description}\n  - **Author:** {author}\n\n"
            else:
                report_text += f"Raw data structure not as expected: {raw_data}\n\n"
        else:
            report_text += "No scraped data available for reporting.\n\n"

        # Also include insights from synthesis and validation stubs
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        validation_result = self.blackboard.get_data("validation_result")

        if synthesized_data:
            report_text += f"#### Knowledge Synthesis Summary:\n{synthesized_data.get('processed_summary', 'N/A')}\n\n"
        if validation_result:
            report_text += f"#### Data Validation Status:\nIs Valid: {validation_result.get('is_valid', 'N/A')}\nNotes: {validation_result.get('notes', 'N/A')}\n\n"

        self.blackboard.set_data("final_report", report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Report generated and posted to blackboard.")
        time.sleep(1)

    def execute_failure_report(self):
        """Generates a simple report if a previous step failed."""
        failure_message = self.blackboard.get_data("final_report")
        if not failure_message:
            failure_message = "An unknown error occurred during the research process."
        
        report_text = f"### MARA Research Report - Process Failed\n\n"
        report_text += f"Reason for failure: {failure_message}\n\n"
        report_text += "Please review the process logs for more details."
        
        self.blackboard.set_data("final_report", report_text)
        self.blackboard.set_status("failed")
        print(f"{self.name}: Failure report generated and posted to blackboard.")
        time.sleep(1)


class HumanInTheLoopAgent:
    """
    (Stub) The Human-in-the-Loop Agent will facilitate user feedback.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" == "complete" or value == "failed":
            self.execute_feedback_prompt()

    def execute_feedback_prompt(self):
        print(f"\n{self.name}: Workflow complete/failed. Prompting for human feedback (stub).")
        # In a real system, this would involve a UI prompt
        feedback_prompt = "Human-in-the-Loop: Do you want to provide feedback or refine the query? (stub)"
        self.blackboard.set_data("human_feedback_prompt", feedback_prompt)
        print(f"{self.name}: Human feedback prompt posted.")
        time.sleep(1)


# --- MAIN WORKFLOW EXECUTION ---

if __name__ == "__main__":
    print("Starting MARA Phase II Development Workflow...")

    # Initialize all agents and pass them the shared blackboard
    orchestrator = OrchestratorAgent("Orchestrator", shared_blackboard)
    data_acquisition = DataAcquisitionAgent("DataAcquisitionAgent", shared_blackboard)
    knowledge_synthesis = KnowledgeSynthesisAgent("KnowledgeSynthesisAgent", shared_blackboard)
    data_validation = DataValidationAgent("DataValidationAgent", shared_blackboard)
    analysis_reporting = AnalysisAndReportingAgent("AnalysisAndReportingAgent", shared_blackboard)
    human_in_loop = HumanInTheLoopAgent("HumanInTheLoopAgent", shared_blackboard)

    print("\n--- Initiating Research Process ---")
    user_initial_query = "List me all the articles on the page with their description and the author."
    orchestrator.run(user_initial_query)

    # In a fully asynchronous system, agents would run in their own threads
    # and react to blackboard changes. For this sequential example, we simulate
    # the flow by allowing each agent to "run" after the blackboard is updated.
    # The observers mechanism in the Blackboard class is a step towards true reactivity.

    # Wait for the process to complete or fail
    max_wait_time = 30 # seconds
    start_time = time.time()
    while shared_blackboard.get_status() not in ["complete", "failed", "unsupported_query"] and \
          (time.time() - start_time) < max_wait_time:
        time.sleep(2) # Poll the blackboard status every 2 seconds
        print(f"Main: Current status: {shared_blackboard.get_status()}...")

    print("\n--- Workflow Execution Finished ---")
    final_report = shared_blackboard.get_data("final_report")
    if final_report:
        print(final_report)
    else:
        print("No final report was generated. Check blackboard status for details.")

    print(f"Final Blackboard Status: {shared_blackboard.get_status()}")
    print(f"Blackboard Data Keys: {list(shared_blackboard._data.keys())}")
