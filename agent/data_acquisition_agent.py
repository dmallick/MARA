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
    Exposes _perform_acquisition for other agents to use directly.
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
                # print(f"{self.name}: Starting scraper.run() with a {timeout} second timeout.")
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                # print(f"{self.name}: Scraper timed out after {timeout} seconds.")
                raise TimeoutError(f"Scraping operation timed out after {timeout} seconds.")
            except Exception as e:
                # print(f"{self.name}: An error occurred within the scraper.run() call: {e}")
                raise e

    def _perform_acquisition(self, user_query_for_scraper: str, source_url: str) -> dict:
        """
        Internal method to execute the web scraping task.
        Designed to be called by this agent or other agents (e.g., ChangeDetectionAgent)
        without directly modifying the blackboard status for the calling agent.
        Returns the raw scraped data or None on failure.
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"{self.name}: ERROR: OPENAI_API_KEY environment variable not set. Cannot proceed with scraping.")
            return None

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
                return result # Success
            except (TimeoutError, requests.exceptions.RequestException, Exception) as e:
                print(f"{self.name}: ERROR: Scraping attempt {attempt + 1} failed for {source_url}: {e}")
                if attempt < self.max_retries - 1:
                    print(f"{self.name}: Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    print(f"{self.name}: All scraping attempts failed for {source_url}.")
                    return None # All retries exhausted
        return None # Should not be reached if loop completes or returns

    def execute_task(self):
        """
        Executes the data acquisition task when delegated via blackboard status, with retries.
        Posts results and status to the blackboard.
        """
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

        raw_data = self._perform_acquisition(user_query_for_scraper, source_url)

        if raw_data:
            self.blackboard.set_data("raw_scraped_data", raw_data)
            self.blackboard.set_status("raw_data_acquired")
            print(f"{self.name}: Scraping complete. Raw data posted to blackboard.")
            print(f"Raw scraped data (partial view): {json.dumps(raw_data, indent=2)[:500]}...")
        else:
            error_msg = f"Data Acquisition Agent failed to acquire raw data from {source_url} after {self.max_retries} attempts."
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("data_acquisition_failed")
            self.blackboard.set_data("final_report", error_msg)
        time.sleep(1)

