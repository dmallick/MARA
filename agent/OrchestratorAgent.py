

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
    def __init__(self, name: str, blackboard):
        from blackboard import Blackboard
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
