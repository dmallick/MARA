
from comm.blackboard import Blackboard
import time
from agent.DataAcquisitionAgent import DataAcquisitionAgent
from agent.KnowledgeSynthesisAgent import KnowledgeSynthesisAgent
from agent.DataValidationAgent import DataValidationAgent
from agent.AnalysisAndReportingAgent import AnalysisAndReportingAgent
from agent.HumanInTheLoopAgent import HumanInTheLoopAgent


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

if __name__ == "__main__":
    print("Starting MARA Phase II Development Workflow...")

    # Initialize all agents and pass them the shared blackboard
    orchestrator = OrchestratorAgent("Orchestrator", shared_blackboard) # type: ignore
    data_acquisition = DataAcquisitionAgent("DataAcquisitionAgent", shared_blackboard) # type: ignore
    knowledge_synthesis = KnowledgeSynthesisAgent("KnowledgeSynthesisAgent", shared_blackboard) # type: ignore
    data_validation = DataValidationAgent("DataValidationAgent", shared_blackboard)    # type: ignore
    analysis_reporting = AnalysisAndReportingAgent("AnalysisAndReportingAgent", shared_blackboard) # type: ignore
    human_in_loop = HumanInTheLoopAgent("HumanInTheLoopAgent", shared_blackboard) # type: ignore

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
        print(f"Main: Current status: {shared_blackboard.get_status()}...") # type: ignore

    print("\n--- Workflow Execution Finished ---")
    final_report = shared_blackboard.get_data("final_report") # type: ignore
    if final_report:
        print(final_report)
    else:
        print("No final report was generated. Check blackboard status for details.")

    print(f"Final Blackboard Status: {shared_blackboard.get_status()}") # type: ignore
    print(f"Blackboard Data Keys: {list(shared_blackboard._data.keys())}") # type: ignore