import os
import time
import json
import threading
from collections import defaultdict
from datetime import datetime

# Import each agent class individually from its dedicated file
from agent.orchestrator_agent import OrchestratorAgent
from agent.data_acquisition_agent import DataAcquisitionAgent
from agent.knowledge_synthesis_agent import KnowledgeSynthesisAgent
from agent.data_validation_agent import DataValidationAgent
from agent.analysis_reporting_agent import AnalysisAndReportingAgent
from agent.data_refresh_agent import DataRefreshAgent
from agent.human_in_the_loop_agent import HumanInTheLoopAgent
from agent.knowledge_query_agent import KnowledgeQueryAgent
from agent.change_detection_agent import ChangeDetectionAgent # NEW: Import ChangeDetectionAgent

# --- 1. Blackboard Implementation (Central Shared Repository) ---
class Blackboard:
    def __init__(self):
        self._data = {}
        self._status = "idle"
        self._observers = defaultdict(list)
        self._lock = threading.RLock()

    def set_data(self, key: str, value):
        """Posts data to the blackboard under a specific key."""
        with self._lock:
            self._data[key] = value
            print(f"Blackboard: Data '{key}' posted. Value: {value}")
            self._notify_observers(key)

    def get_data(self, key: str):
        """Retrieves data from the blackboard."""
        print(f"Blackboard - get_data: Attempting to acquire lock for key: '{key}'")
        with self._lock:
            retrieved_value = self._data.get(key)
            print(f"Blackboard - get_data: Lock acquired for key: '{key}'. Value: {retrieved_value}")
            return retrieved_value

    def set_status(self, new_status: str):
        """Updates the overall system status on the blackboard."""
        with self._lock:
            self._status = new_status
            print(f"Blackboard: Status updated to '{new_status}'.")
            self._notify_observers("status")

    def get_status(self):
        """Retrieves the current system status."""
        with self._lock:
            return self._status

    def register_observer(self, key: str, agent_callback):
        """
        Allows an agent to register a callback function to be notified
        when data under 'key' changes.
        """
        with self._lock:
            self._observers[key].append(agent_callback)
            print(f"Blackboard: Agent registered as observer for '{key}'.")

    def _notify_observers(self, key: str):
        """Notifies registered observers that data under 'key' has changed."""
        callbacks_to_run = []
        with self._lock:
            if key in self._observers:
                callbacks_to_run = list(self._observers[key])

        for callback in callbacks_to_run:
            try:
                callback_value = self.get_data(key) if key != "status" else self.get_status()
                callback(key, callback_value)
            except Exception as e:
                print(f"Blackboard: Error notifying observer for '{key}': {e}")
    
    def age_data(self, key: str):
        """
        Increments the 'data_age' for a specific data entry on the blackboard
        if it has a 'data_age' attribute.
        """
        with self._lock:
            if key in self._data and isinstance(self._data[key], dict) and \
               "extracted_entities" in self._data[key] and \
               "data_age" in self._data[key]["extracted_entities"]:
                self._data[key]["extracted_entities"]["data_age"] += 1
                print(f"Blackboard: Data '{key}' aged to {self._data[key]['extracted_entities']['data_age']} cycles.")
                self._notify_observers(key)


# --- MAIN WORKFLOW EXECUTION ---

if __name__ == "__main__":
    print("Starting MARA Phase II Development Workflow...")

    shared_blackboard = Blackboard() # Instantiate the central blackboard here

    # Instantiate agents, now imported from their individual modules
    orchestrator = OrchestratorAgent("Orchestrator", shared_blackboard)
    data_acquisition = DataAcquisitionAgent("DataAcquisitionAgent", shared_blackboard, max_retries=3, retry_delay=5)
    knowledge_synthesis = KnowledgeSynthesisAgent("KnowledgeSynthesisAgent", shared_blackboard)
    data_validation = DataValidationAgent("DataValidationAgent", shared_blackboard)
    analysis_reporting = AnalysisAndReportingAgent("AnalysisAndReportingAgent", shared_blackboard)
    data_refresh = DataRefreshAgent("DataRefreshAgent", shared_blackboard, stale_threshold=2)
    human_in_loop = HumanInTheLoopAgent("HumanInTheLoopAgent", shared_blackboard)
    knowledge_query = KnowledgeQueryAgent("KnowledgeQueryAgent", shared_blackboard)
    # NEW: Instantiate ChangeDetectionAgent, passing required dependencies
    change_detection = ChangeDetectionAgent("ChangeDetectionAgent", shared_blackboard, data_acquisition, knowledge_synthesis) 

    print("\n--- Initiating Research Process ---")
    user_initial_query = "List me all the articles on the page with their description and the author."
    orchestrator.run(user_initial_query)

    max_wait_time = 360 
    start_time = time.time()
    
    run_cycles = 0
    while True:
        current_status = shared_blackboard.get_status()
        print(f"\nMain Loop Cycle {run_cycles}: Current status: {current_status}...")
        
        if run_cycles > 0 and \
           "synthesized_knowledge" in shared_blackboard._data and \
           current_status not in ["awaiting_re_orchestration", "task_delegated_to_data_acquisition", 
                                  "summarize_requested", "filter_by_author_requested", "visualize_requested", 
                                  "query_requested", "check_for_changes_requested", "prolific_author_requested"]: # Added new statuses
             shared_blackboard.age_data("synthesized_knowledge") 

        if current_status == "awaiting_re_orchestration":
            orchestrator.process_feedback() 
        elif current_status == "age_data_requested":
            shared_blackboard.age_data("synthesized_knowledge")
            shared_blackboard.set_status("complete")
            print("Main: Data aging complete via human command. Please request a new report to see updated age.")

        if shared_blackboard.get_data("human_feedback") and shared_blackboard.get_data("human_feedback").lower() == "exit" and \
           current_status in ["complete", "failed", "unsupported_query", "complete_with_feedback", 
                              "changes_detected", "no_changes_detected"]: # Added new statuses
            print("Main: User explicitly exited the process.")
            break
        elif current_status in ["failed", "unsupported_query", "timed_out"]:
             break
        
        if (time.time() - start_time) > max_wait_time:
            print("Main: Workflow timed out.")
            shared_blackboard.set_status("timed_out") 
            break
        
        run_cycles += 1
        time.sleep(2)

    print("\n--- Workflow Execution Finished ---")
    final_report = shared_blackboard.get_data("final_report")
    if final_report:
        print(final_report)
    else:
        print("No final report was generated. Check blackboard status for details.")

    human_feedback_received = shared_blackboard.get_data("human_feedback")
    if human_feedback_received:
        print(f"\nHuman Feedback Captured: {human_feedback_received}")

    print(f"Final Blackboard Status: {shared_blackboard.get_status()}")
    print(f"Blackboard Data Keys: {list(shared_blackboard._data.keys())}")
