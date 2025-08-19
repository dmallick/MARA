
from comm.blackboard import Blackboard
import time
import os
import json
from dotenv import load_dotenv
from scrapegraphai.graphs import SmartScraperGraph
load_dotenv()

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
                prompt=user_query_for_scraper, # type: ignore
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