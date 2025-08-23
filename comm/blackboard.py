import os
import time
import json
import threading
from collections import defaultdict
from scrapegraphai.graphs import SmartScraperGraph
import concurrent.futures # Import for timeout mechanism
import requests.exceptions # For potential network-related exceptions
from datetime import datetime # Import datetime for timestamping

# --- 1. Blackboard Implementation (Central Shared Repository) ---
class Blackboard:
    def __init__(self):
        self._data = {}
        self._status = "idle"
        self._observers = defaultdict(list)
        self._lock = threading.RLock() # Changed to RLock to allow re-entrant locking

    def set_data(self, key: str, value):
        """Posts data to the blackboard under a specific key."""
        with self._lock:
            self._data[key] = value
            print(f"Blackboard: Data '{key}' posted. Value: {value}") # Added debug print for value
            self._notify_observers(key)

    def get_data(self, key: str):
        """Retrieves data from the blackboard."""
        print(f"Blackboard - get_data: Attempting to acquire lock for key: '{key}'") # Added debug print
        with self._lock:
            retrieved_value = self._data.get(key)
            print(f"Blackboard - get_data: Lock acquired for key: '{key}'. Value: {retrieved_value}") # Added debug print
            return retrieved_value
        # The lock is automatically released here when exiting the 'with' block.
        # This print statement would technically execute *after* the lock is released.
        # print(f"Blackboard - get_data: Lock released for key: '{key}'") # This line is unreachable due to the return statement.

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
                callbacks_to_run = list(self._observers[key]) # Make a copy to avoid issues if list changes during iteration

        for callback in callbacks_to_run:
            try:
                # Pass the latest value from the blackboard (re-acquiring the lock if necessary inside callback)
                # or pass a copy of the value at the time of notification
                # For simplicity, we directly call it, understanding it may implicitly re-acquire RLock
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
                print(f"Blackboard: Data '{key}' aged to {self._data[key]['extracted_entities']['data_age']}.")


# Instantiate the central blackboard
shared_blackboard = Blackboard()


# --- 2. Agent Definitions (Modular Python Classes) ---

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
        
        if "articles" in user_query.lower() and "description" in user_query.lower() and "author" in user_query.lower():
            task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
            print(f"{self.name}: Decomposed query. Delegating 'web_scrape' task. Task object to set: {task}") # Added debug
            
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
        original_query = self.blackboard.get_data("user_query") # Get the original query for context

        # --- DEBUG START ---
        print(f"{self.name}: Debug: Feedback retrieved by Orchestrator: '{feedback}' (Type: {type(feedback)})")
        if feedback:
            print(f"{self.name}: Debug: Lowercased feedback: '{feedback.lower()}'")
            print(f"{self.name}: Debug: Check for 'summarize key findings' in feedback: {'summarize key findings' in feedback.lower()}")
            print(f"{self.name}: Debug: Check for 'articles by author' in feedback: {'articles by author' in feedback.lower()}")
            print(f"{self.name}: Debug: Check for 'show article distribution' in feedback: {'show article distribution' in feedback.lower()}") # New debug
        # --- DEBUG END ---

        if feedback and "summarize key findings" in feedback.lower():
            print(f"{self.name}: Human requested summary of key findings. Delegating summary task to Analysis & Reporting Agent.")
            summary_task = {"type": "summarize_findings", "from_data_key": "synthesized_knowledge", "original_query": original_query}
            self.blackboard.set_data("current_task", summary_task)
            self.blackboard.set_status("summarize_requested") # New status to trigger summary in Analysis agent
        elif feedback and "articles by author" in feedback.lower():
            # Extract author name from feedback - a simplified approach for now
            author_keyword_index = feedback.lower().find("articles by author")
            author_name_start_index = author_keyword_index + len("articles by author")
            # This is a very basic parsing; a real system would use NLP
            author_name = feedback[author_name_start_index:].strip("?. ").strip()
            if author_name:
                print(f"{self.name}: Human requested articles by author '{author_name}'. Delegating filter task to Analysis & Reporting Agent.")
                filter_task = {"type": "filter_by_author", "author": author_name, "from_data_key": "raw_scraped_data", "original_query": original_query}
                self.blackboard.set_data("current_task", filter_task)
                self.blackboard.set_status("filter_by_author_requested")
            else:
                print(f"{self.name}: Could not extract author name from feedback: '{feedback}'.")
                self.blackboard.set_status("complete_with_feedback")
        elif feedback and "show article distribution by author" in feedback.lower(): # New condition for visualization
            print(f"{self.name}: Human requested article distribution by author. Delegating visualization task to Analysis & Reporting Agent.")
            viz_task = {"type": "visualize_author_distribution", "from_data_key": "raw_scraped_data", "original_query": original_query}
            self.blackboard.set_data("current_task", viz_task)
            self.blackboard.set_status("visualize_requested")
        else:
            print(f"{self.name}: Human feedback received but no specific follow-up action identified for: '{feedback}'.")
            self.blackboard.set_status("complete_with_feedback") # New status for graceful exit after feedback
        time.sleep(1)


class DataAcquisitionAgent:
    """
    The Data Acquisition Agent is responsible for gathering raw data, primarily
    through web scraping, and posting it to the blackboard.
    Includes a timeout for the scraping process to prevent indefinite hangs.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        """Callback triggered when observed blackboard data changes."""
        if key == "status" and value == "task_delegated_to_data_acquisition":
            self.execute_task()

    def _run_scraper_with_timeout(self, scraper_instance, timeout=60):
        """Helper function to run scraper.run() with a timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(scraper_instance.run)
            try:
                print(f"{self.name}: Starting scraper.run() with a {timeout} second timeout.")
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                print(f"{self.name}: Scraper timed out after {timeout} seconds.")
                raise TimeoutError(f"Scraping operation timed out after {timeout} seconds.")
            except Exception as e:
                print(f"{self.name}: An error occurred within the scraper.run() call: {e}")
                raise e

    def execute_task(self):
        """Executes the data acquisition task when delegated."""
        print(f"\n{self.name}: Task delegated. Starting web scraping.")
        
        # --- DEBUG START ---
        print(f"{self.name}: Debug: Raw blackboard _data before get_data('current_task'): {self.blackboard._data}")
        # --- DEBUG END ---

        task = self.blackboard.get_data("current_task")
        
        # --- DEBUG START ---
        print(f"{self.name}: Debug: Value retrieved for 'current_task': {task}")
        # --- DEBUG END ---

        if not task or not isinstance(task, dict) or task.get("type") != "web_scrape": # More robust check
            error_msg = f"Error: No valid web_scrape task found on blackboard or task type mismatch. Current task: {task}"
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", error_msg)
            return

        user_query_for_scraper = self.blackboard.get_data("user_query")
        source_url = task.get("source_url", "https://example.com")

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"{self.name}: ERROR: OPENAI_API_KEY environment variable not set. Cannot proceed with scraping.")
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
            print(f"{self.name}: Initializing SmartScraperGraph for source: {source_url}")
            scraper = SmartScraperGraph(
                prompt=user_query_for_scraper,
                source=source_url,
                config=graph_config
            )
            
            result = self._run_scraper_with_timeout(scraper, timeout=60)
            
            self.blackboard.set_data("raw_scraped_data", result)
            self.blackboard.set_status("raw_data_acquired")
            print(f"{self.name}: Scraping complete. Raw data posted to blackboard.")
            # Print a controlled amount of data, as full JSON can be very long
            print(f"Raw scraped data (partial view): {json.dumps(result, indent=2)[:500]}...")
        except TimeoutError as e:
            print(f"{self.name}: ERROR: Scraping operation failed due to timeout - {e}")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", f"Error: Web scraping timed out: {e}")
        except requests.exceptions.RequestException as e:
            print(f"{self.name}: ERROR: Network request failed during scraping - {e}")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", f"Error: Network issue during web scraping: {e}")
        except Exception as e:
            print(f"{self.name}: ERROR: An unexpected error occurred during scraping - {e}")
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", f"Error: Web scraping failed with unexpected error: {e}")
        time.sleep(1)


class KnowledgeSynthesisAgent:
    """
    The Knowledge Synthesis Agent processes raw data and extracts structured
    information, simulating the construction of a knowledge base.
    Now includes timestamping and data aging to lay the foundation for a temporal knowledge graph.
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
        print(f"\n{self.name}: Raw data acquired. Starting knowledge synthesis.")
        raw_data = self.blackboard.get_data("raw_scraped_data")

        if raw_data:
            # Added data_age initialization here
            synthesized_output = {"articles_summary": [], "authors": set(), "timestamp": datetime.now().isoformat(), "data_age": 0} 
            if isinstance(raw_data, dict) and "content" in raw_data and isinstance(raw_data["content"], list):
                for article in raw_data["content"]:
                    title = article.get("title", "N/A")
                    description = article.get("description", "N/A")
                    author = article.get("author", "NA") # Default to "NA" if author is missing
                    
                    if author != "NA":
                        synthesized_output["authors"].add(author)

                    summary_point = {
                        "title": title,
                        "author": author,
                        "description_snippet": description[:50] + '...' if len(description) > 50 else description
                    }
                    synthesized_output["articles_summary"].append(summary_point)
            
            synthesized_output["authors"] = list(synthesized_output["authors"]) # Convert set to list for JSON serialization

            synthesized_data = {
                "summary": "Synthesized key information from acquired raw data.",
                "extracted_entities": synthesized_output
            }
            self.blackboard.set_data("synthesized_knowledge", synthesized_data)
            self.blackboard.set_status("knowledge_synthesized")
            print(f"{self.name}: Knowledge synthesis complete. Synthesized data posted (with timestamp and age).")
            print(f"Synthesized knowledge (partial view): {json.dumps(synthesized_data, indent=2)[:500]}...")
        else:
            print(f"{self.name}: No raw data found for synthesis. Setting status to 'knowledge_synthesis_failed'.")
            self.blackboard.set_status("knowledge_synthesis_failed")
            self.blackboard.set_data("final_report", "Error: Knowledge Synthesis Agent failed due to missing raw data.")
        time.sleep(1)


class DataValidationAgent:
    """
    The Data Validation Agent performs quality checks on the synthesized data.
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
        print(f"\n{self.name}: Knowledge synthesized. Starting data validation.")
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        
        validation_result = {"is_valid": False, "notes": "No data for validation."}

        if synthesized_data and "extracted_entities" in synthesized_data and synthesized_data["extracted_entities"].get("articles_summary"):
            if len(synthesized_data["extracted_entities"]["articles_summary"]) > 0:
                is_valid = True
                notes = "Articles summary data is present."
            else:
                is_valid = False
                notes = "No article summaries extracted, potential issue."
            
            validation_result = {"is_valid": is_valid, "notes": notes}
            self.blackboard.set_data("validation_result", validation_result)
            self.blackboard.set_status("data_validated")
            print(f"{self.name}: Data validation complete. Result posted: {validation_result}")
        else:
            print(f"{self.name}: No synthesized data found for validation. Setting status to 'data_validation_failed'.")
            self.blackboard.set_status("data_validation_failed")
            self.blackboard.set_data("final_report", "Error: Data Validation Agent failed due to missing synthesized knowledge.")
        time.sleep(1)


class AnalysisAndReportingAgent:
    """
    The Analysis & Reporting Agent monitors the blackboard for 'data_validated' status.
    Once data is available, it processes it, generates insights, and compiles the final report.
    It can also generate a summary of key findings upon request or visualize data.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "data_validated":
            self.execute_task()
        elif key == "status" and value == "summarize_requested":
            self.execute_summary_task()
        elif key == "status" and value == "filter_by_author_requested":
            self.execute_filter_by_author_task()
        elif key == "status" and value == "visualize_requested": # New condition for visualization task
            self.execute_visualization_task()
        elif key == "status" and (value in ["data_acquisition_failed", "unsupported_query", "knowledge_synthesis_failed", "data_validation_failed"]):
            self.execute_failure_report()

    def execute_task(self):
        print(f"\n{self.name}: Data validated. Generating final report and insights.")
        raw_data = self.blackboard.get_data("raw_scraped_data") 
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        validation_result = self.blackboard.get_data("validation_result")
        
        report_text = "### MARA Research Report\n\n"
        report_text += f"**Overall Process Status:** {self.blackboard.get_status()}\n\n"
        if synthesized_data and "timestamp" in synthesized_data["extracted_entities"]: # Display timestamp
             report_text += f"**Report Generated At:** {synthesized_data['extracted_entities']['timestamp']}\n"
             # Display data age
             report_text += f"**Synthesized Data Age:** {synthesized_data['extracted_entities'].get('data_age', 'N/A')} cycles\n\n"


        if raw_data:
            report_text += "#### Scraped Articles Overview (Raw Data):\n\n"
            if isinstance(raw_data, dict) and "content" in raw_data and isinstance(raw_data["content"], list):
                num_articles = len(raw_data["content"])
                report_text += f"**Total Articles Found:** {num_articles}\n\n"
                for article in raw_data["content"]:
                    title = article.get("title", "N/A")
                    description = article.get("description", "N/A")
                    author = article.get("author", "NA")
                    report_text += f"- **Title:** {title}\n  - **Description:** {description}\n  - **Author:** {author}\n\n"
            else:
                report_text += f"Raw data structure not as expected: {raw_data}\n\n"
        else:
            report_text += "No raw scraped data available for reporting.\n\n"

        if synthesized_data:
            report_text += f"#### Knowledge Synthesis Summary:\n{synthesized_data.get('summary', 'N/A')}\n"
            if synthesized_data.get("extracted_entities", {}).get("articles_summary"):
                report_text += "Extracted Entities (Articles):\n"
                for item in synthesized_data["extracted_entities"]["articles_summary"]:
                    report_text += f"- **Title:** {item.get('title', 'N/A')}\n  - **Author:** {item.get('author', 'N/A')}\n  - **Snippet:** {item.get('description_snippet', 'N/A')}\n\n"
            
            # New Analytical Insight: Unique Authors
            unique_authors = synthesized_data["extracted_entities"].get("authors", [])
            if unique_authors:
                report_text += f"\n**Unique Authors Identified:** {', '.join(unique_authors)}\n"
            else:
                report_text += "\n**No Unique Authors Identified.**\n"
            
            report_text += "\n"
        else:
            report_text += "No synthesized knowledge available for reporting.\n\n"

        if validation_result:
            report_text += f"#### Data Validation Status:\nIs Valid: {validation_result.get('is_valid', 'N/A')}\nNotes: {validation_result.get('notes', 'N/A')}\n\n"
        else:
            report_text += "No data validation result available.\n\n"

        self.blackboard.set_data("final_report", report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Report generated and posted to blackboard.")
        time.sleep(1)

    def execute_summary_task(self):
        """Generates a summary of key findings based on synthesized knowledge."""
        print(f"\n{self.name}: Summary task received. Generating key findings summary.")
        task = self.blackboard.get_data("current_task")

        if task is None:
            print(f"{self.name}: ERROR: 'current_task' is None. Cannot execute summary task.")
            self.blackboard.set_data("final_report", "Error: Cannot generate summary, no valid task found.")
            self.blackboard.set_status("failed")
            return

        synthesized_data = self.blackboard.get_data(task.get("from_data_key", "synthesized_knowledge"))

        summary_report_text = f"### MARA Research Report - Key Findings Summary\n\n"
        if synthesized_data and "timestamp" in synthesized_data["extracted_entities"]:
             summary_report_text += f"**Summary Generated At:** {synthesized_data['extracted_entities']['timestamp']}\n"
             # Display data age
             summary_report_text += f"**Synthesized Data Age:** {synthesized_data['extracted_entities'].get('data_age', 'N/A')} cycles\n\n"

        if synthesized_data and synthesized_data.get("extracted_entities", {}).get("articles_summary"):
            all_summaries = synthesized_data["extracted_entities"]["articles_summary"]
            summary_report_text += "Here are the key findings:\n"
            for s in all_summaries:
                summary_report_text += f"- **Title:** {s.get('title', 'N/A')}\n  - **Author:** {s.get('author', 'N/A')}\n  - **Snippet:** {s.get('description_snippet', 'N/A')}\n\n"

            summary_report_text += f"\nOriginal request: '{task.get('original_query', 'N/A')}'\n"
            summary_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"
            
            self.blackboard.set_data("final_report", summary_report_text)
            self.blackboard.set_status("complete") # Mark as complete after summary
            print(f"{self.name}: Key findings summary generated and posted.")
        else:
            summary_report_text += "No synthesized data available to summarize."
            self.blackboard.set_data("final_report", summary_report_text)
            self.blackboard.set_status("failed")
            print(f"{self.name}: Failed to generate summary: No data.")
        time.sleep(1)

    def execute_filter_by_author_task(self):
        """Filters raw scraped data to show articles by a specific author."""
        print(f"\n{self.name}: Filter by author task received. Filtering articles.")
        task = self.blackboard.get_data("current_task")

        if task is None:
            print(f"{self.name}: ERROR: 'current_task' is None. Cannot execute filter by author task.")
            self.blackboard.set_data("final_report", "Error: Cannot filter by author, no valid task found.")
            self.blackboard.set_status("failed")
            return

        author_to_filter = task.get("author")
        raw_data = self.blackboard.get_data(task.get("from_data_key", "raw_scraped_data"))
        synthesized_data = self.blackboard.get_data("synthesized_knowledge") # Get synthesized data for timestamp

        filter_report_text = f"### MARA Research Report - Articles by Author: '{author_to_filter}'\n\n"
        if synthesized_data and "timestamp" in synthesized_data["extracted_entities"]:
             filter_report_text += f"**Generated At:** {synthesized_data['extracted_entities']['timestamp']}\n"
             # Display data age
             filter_report_text += f"**Synthesized Data Age:** {synthesized_data['extracted_entities'].get('data_age', 'N/A')} cycles\n\n"
        
        found_articles = []

        if raw_data and isinstance(raw_data, dict) and "content" in raw_data and isinstance(raw_data["content"], list):
            for article in raw_data["content"]:
                if article.get("author", "").lower() == author_to_filter.lower():
                    found_articles.append(article)
            
            if found_articles:
                filter_report_text += f"Found {len(found_articles)} article(s) by '{author_to_filter}':\n\n"
                for article in found_articles:
                    title = article.get("title", "N/A")
                    description = article.get("description", "N/A")
                    filter_report_text += f"- **Title:** {title}\n  - **Description:** {description}\n\n"
            else:
                filter_report_text += f"No articles found by author '{author_to_filter}'.\n\n"
        else:
            filter_report_text += "No raw scraped data available to filter.\n\n"
        
        filter_report_text += f"Original request: '{task.get('original_query', 'N/A')}'\n"
        filter_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"

        self.blackboard.set_data("final_report", filter_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Articles filtered by author and report posted.")
        time.sleep(1)

    def execute_visualization_task(self):
        """Generates a simple ASCII bar chart of article distribution by author."""
        print(f"\n{self.name}: Visualization task received. Generating article distribution by author.")
        task = self.blackboard.get_data("current_task")

        if task is None:
            print(f"{self.name}: ERROR: 'current_task' is None. Cannot execute visualization task.")
            self.blackboard.set_data("final_report", "Error: Cannot generate visualization, no valid task found.")
            self.blackboard.set_status("failed")
            return

        raw_data = self.blackboard.get_data(task.get("from_data_key", "raw_scraped_data"))
        synthesized_data = self.blackboard.get_data("synthesized_knowledge") # Get synthesized data for timestamp

        viz_report_text = f"### MARA Research Report - Article Distribution by Author (ASCII Bar Chart)\n\n"
        if synthesized_data and "timestamp" in synthesized_data["extracted_entities"]:
             viz_report_text += f"**Generated At:** {synthesized_data['extracted_entities']['timestamp']}\n"
             # Display data age
             viz_report_text += f"**Synthesized Data Age:** {synthesized_data['extracted_entities'].get('data_age', 'N/A')} cycles\n\n"
        
        if raw_data and isinstance(raw_data, dict) and "content" in raw_data and isinstance(raw_data["content"], list):
            author_counts = defaultdict(int)
            for article in raw_data["content"]:
                author = article.get("author", "Unknown Author")
                author_counts[author] += 1
            
            if author_counts:
                max_articles = max(author_counts.values())
                if max_articles == 0: # Avoid division by zero if no articles are found
                    viz_report_text += "No articles found to visualize author distribution.\n"
                    self.blackboard.set_data("final_report", viz_report_text)
                    self.blackboard.set_status("complete")
                    print(f"{self.name}: No articles found for visualization.")
                    return

                viz_report_text += "```\n" # Start of code block for monospace text
                viz_report_text += "Article Distribution by Author:\n"
                viz_report_text += "--------------------------------\n"
                
                # Sort authors for consistent output
                sorted_authors = sorted(author_counts.keys())

                for author in sorted_authors:
                    count = author_counts[author]
                    # Scale bar length for better visibility in console
                    bar_length = int((count / max_articles) * 30) # Max bar length 30 characters
                    bar = '#' * bar_length
                    viz_report_text += f"{author.ljust(20)} | {bar} ({count})\n"
                viz_report_text += "```\n" # End of code block
            else:
                viz_report_text += "No authors or articles found to generate distribution.\n"
        else:
            viz_report_text += "No raw scraped data available for visualization.\n\n"
        
        viz_report_text += f"Original request: '{task.get('original_query', 'N/A')}'\n"
        viz_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"

        self.blackboard.set_data("final_report", viz_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Article distribution by author generated and posted.")
        time.sleep(1)


    def execute_failure_report(self):
        """Generates a simple report if a previous step failed."""
        failure_message = self.blackboard.get_data("final_report")
        if not failure_message:
            current_status = self.blackboard.get_status()
            if current_status == "data_acquisition_failed":
                failure_message = "Data Acquisition Agent failed to retrieve data."
            elif current_status == "knowledge_synthesis_failed":
                failure_message = "Knowledge Synthesis Agent failed to process data."
            elif current_status == "data_validation_failed":
                failure_message = "Data Validation Agent failed to validate data."
            elif current_status == "unsupported_query":
                failure_message = "Orchestrator did not recognize the query as supported."
            else:
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
    The Human-in-the-Loop Agent facilitates user feedback and can potentially
    trigger refinement loops based on human input.
    """
    def __init__(self, name: str, blackboard: Blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and (value == "complete" or value == "failed"):
            self.execute_feedback_prompt()

    def execute_feedback_prompt(self):
        print(f"\n{self.name}: Workflow complete/failed. Engaging human for feedback.")
        
        print("\n--- HUMAN INTERVENTION REQUIRED ---")
        user_feedback = input(
            "Human-in-the-Loop: Please review the MARA report above. "
            "Do you have any feedback or a follow-up request? "
            "(e.g., 'summarize key findings', 'articles by author Marco Perini', 'show article distribution by author', 'age data', or 'exit' to finish): "
        )
        print("--- END HUMAN INTERVENTION ---")

        if user_feedback.lower() == "exit":
            print(f"{self.name}: Received 'exit'. Ending human feedback loop.")
            self.blackboard.set_data("human_feedback", "User chose to exit.")
        elif user_feedback.lower() == "age data": # New feedback to trigger data aging
            print(f"{self.name}: Received 'age data' request. Setting status for data aging.")
            self.blackboard.set_data("human_feedback", user_feedback)
            self.blackboard.set_status("age_data_requested")
        else:
            print(f"{self.name}: Received human feedback: '{user_feedback}'. Posting to blackboard.")
            self.blackboard.set_data("human_feedback", user_feedback)
            self.blackboard.set_status("awaiting_re_orchestration")


# --- MAIN WORKFLOW EXECUTION ---

if __name__ == "__main__":
    print("Starting MARA Phase II Development Workflow...")

    orchestrator = OrchestratorAgent("Orchestrator", shared_blackboard)
    data_acquisition = DataAcquisitionAgent("DataAcquisitionAgent", shared_blackboard)
    knowledge_synthesis = KnowledgeSynthesisAgent("KnowledgeSynthesisAgent", shared_blackboard)
    data_validation = DataValidationAgent("DataValidationAgent", shared_blackboard)
    analysis_reporting = AnalysisAndReportingAgent("AnalysisAndReportingAgent", shared_blackboard)
    human_in_loop = HumanInTheLoopAgent("HumanInTheLoopAgent", shared_blackboard)

    print("\n--- Initiating Research Process ---")
    user_initial_query = "List me all the articles on the page with their description and the author."
    orchestrator.run(user_initial_query)

    max_wait_time = 360 # Increased wait time for full workflow including human input and re-orchestration
    start_time = time.time()
    
    while True:
        current_status = shared_blackboard.get_status()
        print(f"Main: Current status: {current_status}...")

        if current_status == "awaiting_re_orchestration":
            orchestrator.process_feedback() 
        elif current_status == "age_data_requested": # New condition for aging data
            shared_blackboard.age_data("synthesized_knowledge")
            # After aging, we should let the user re-request a report to see the change
            # or automatically regenerate the report. For now, we'll revert to 'complete'
            # and rely on the user to request a report.
            shared_blackboard.set_status("complete") 
            print("Main: Data aging complete. Please request a new report to see updated age.")

        elif current_status in ["complete", "failed", "unsupported_query", "complete_with_feedback"]:
            break 
        
        if (time.time() - start_time) > max_wait_time:
            print("Main: Workflow timed out.")
            shared_blackboard.set_status("timed_out") 
            break
        
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
