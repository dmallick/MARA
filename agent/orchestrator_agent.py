import time
import json
import os # Needed for OpenAI API key check in some task types

class OrchestratorAgent:
    """
    The Orchestrator Agent's role is expanded beyond the MVP to include
    more sophisticated task decomposition and delegation based on user queries.
    It oversees the entire research workflow.
    """
    def __init__(self, name: str, blackboard):
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
        
        if "articles" in user_query.lower() and "description" in user_query.lower() and "author" in user_query.lower():
            task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
            print(f"{self.name}: Decomposed query. Delegating 'web_scrape' task. Task object to set: {task}")
            
            self.blackboard.set_data("current_task", task)
            self.blackboard.set_status("task_delegated_to_data_acquisition")
        else:
            print(f"{self.name}: Query not recognized for current capabilities. Setting status to 'unsupported_query'.")
            self.blackboard.set_status("unsupported_query")
            self.blackboard.set_data("final_report", "Orchestrator: The current system can only process queries related to 'articles', 'description', and 'author' for web scraping.")
        time.sleep(1)

    def process_feedback(self):
        """
        Processes human feedback and potentially delegates new tasks based on it.
        """
        print(f"\n{self.name}: Processing human feedback.")
        feedback = self.blackboard.get_data("human_feedback")
        original_query = self.blackboard.get_data("user_query")

        if feedback and "summarize key findings" in feedback.lower():
            print(f"{self.name}: Human requested summary of key findings. Delegating summary task to Analysis & Reporting Agent.")
            summary_task = {"type": "summarize_findings", "from_data_key": "synthesized_knowledge", "original_query": original_query}
            self.blackboard.set_data("current_task", summary_task)
            self.blackboard.set_status("summarize_requested")
        elif feedback and "articles by author" in feedback.lower():
            author_keyword_index = feedback.lower().find("articles by author")
            author_name_start_index = author_keyword_index + len("articles by author")
            author_name = feedback[author_name_start_index:].strip("?. ").strip()
            if author_name:
                print(f"{self.name}: Human requested articles by author '{author_name}'. Delegating filter task to Analysis & Reporting Agent.")
                filter_task = {"type": "filter_by_author", "author": author_name, "from_data_key": "raw_scraped_data", "original_query": original_query}
                self.blackboard.set_data("current_task", filter_task)
                self.blackboard.set_status("filter_by_author_requested")
            else:
                print(f"{self.name}: Could not extract author name from feedback: '{feedback}'.")
                self.blackboard.set_status("complete_with_feedback")
        elif feedback and "show article distribution by author" in feedback.lower():
            print(f"{self.name}: Human requested article distribution by author. Delegating visualization task to Analysis & Reporting Agent.")
            viz_task = {"type": "visualize_author_distribution", "from_data_key": "raw_scraped_data", "original_query": original_query}
            self.blackboard.set_data("current_task", viz_task)
            self.blackboard.set_status("visualize_requested")
        elif feedback and "refresh data" in feedback.lower():
            print(f"{self.name}: Human requested data refresh. Re-delegating data acquisition task.")
            refresh_task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
            self.blackboard.set_data("current_task", refresh_task)
            self.blackboard.set_status("task_delegated_to_data_acquisition")
        else:
            print(f"{self.name}: Human feedback received but no specific follow-up action identified for: '{feedback}'.")
            self.blackboard.set_status("complete_with_feedback")
        time.sleep(1)
