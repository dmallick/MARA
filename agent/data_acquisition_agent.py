import os
import time
import json
import concurrent.futures
import requests.exceptions
from scrapegraphai.graphs import SmartScraperGraph

class DataAcquisitionAgent:
    """
    The Data Acquisition Agent is responsible for gathering raw data, primarily
    through web scraping, and posting it to the blackboard.
    Includes a timeout for the scraping process to prevent indefinite hangs.
    Now includes a retry mechanism for transient errors.
    """
    def __init__(self, name: str, blackboard, max_retries: int = 3, retry_delay: int = 5):
        self.name = name
        self.blackboard = blackboard
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        print(f"{self.name}: Initialized with max_retries={self.max_retries}, retry_delay={self.retry_delay}s.")
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
        """Executes the data acquisition task when delegated, with retries."""
        print(f"\n{self.name}: Task delegated. Starting web scraping (with retries).")
        
        task = self.blackboard.get_data("current_task")

        if not task or not isinstance(task, dict) or task.get("type") != "web_scrape":
            error_msg = f"Error: No valid web_scrape task found on blackboard or task type mismatch. Current task: {task}"
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", error_msg)
            return

        user_query_for_scraper = self.blackboard.get_data("user_query")
        source_url = task.get("source_url", "https://perinim.github.io/projects")

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            error_msg = "ERROR: OPENAI_API_KEY environment variable not set. Cannot proceed with scraping."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", error_msg)
            return

        graph_config = {
           "llm": {
              "api_key": openai_key,
              "model": "openai/gpt-4o",
           },
        }

        for attempt in range(self.max_retries):
            try:
                print(f"{self.name}: Initializing SmartScraperGraph for source: {source_url} (Attempt {attempt + 1}/{self.max_retries})")
                scraper = SmartScraperGraph(
                    prompt=user_query_for_scraper,
                    source=source_url,
                    config=graph_config
                )
                
                result = self._run_scraper_with_timeout(scraper, timeout=60)
                
                self.blackboard.set_data("raw_scraped_data", result)
                self.blackboard.set_status("raw_data_acquired")
                print(f"{self.name}: Scraping complete. Raw data posted to blackboard.")
                print(f"Raw scraped data (partial view): {json.dumps(result, indent=2)[:500]}...")
                return
            except (TimeoutError, requests.exceptions.RequestException, Exception) as e:
                error_msg = f"ERROR: Scraping attempt {attempt + 1} failed: {e}"
                print(f"{self.name}: {error_msg}")
                if attempt < self.max_retries - 1:
                    print(f"{self.name}: Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"{self.name}: All scraping attempts failed.")
                    self.blackboard.set_data("error_message", error_msg)
                    self.blackboard.set_status("data_acquisition_failed")
                    self.blackboard.set_data("final_report", f"Error: Web scraping failed after {self.max_retries} attempts: {e}")
        time.sleep(1)
