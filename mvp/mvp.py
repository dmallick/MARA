import os
from dotenv import load_dotenv
import time
import json
from scrapegraphai.graphs import SmartScraperGraph
import logging
logging.basicConfig(level=logging.INFO)
load_dotenv()
# Define the central shared repository, the Blackboard
# In this MVP, a simple dictionary will represent the blackboard,
# serving as the communication and data-sharing medium for the agents.
blackboard = {
    "user_query": "",
    "data_to_analyze": None,
    "final_report": None,
    "status": "idle"
}


# --- AGENT DEFINITIONS ---

def OrchestratorAgent(query: str):
    """
    The Orchestrator Agent's role in the MVP is to receive the user query,
    decompose it, and delegate the task to the appropriate agent.
    
    In a real system, this would involve complex planning and delegation.[1, 2]
    For the MVP, it's a direct task hand-off to the Data Acquisition Agent.
    """
    print("Orchestrator: Received user query.")
    blackboard["user_query"] = query
    blackboard["status"] = "task_delegated"
    print(f"Orchestrator: Delegating task '{query}' to Data Acquisition Agent.")
    time.sleep(1) # Simulate processing time

def DataAcquisitionAgent():
    """
    The Data Acquisition Agent is responsible for web scraping and data extraction.
    It operates by reading the blackboard and, when the status is 'task_delegated',
    it executes its task.
    """
    if blackboard["status"] == "task_delegated":
        print("\nData Acquisition Agent: Task delegated. Starting web scraping.")
        
        # We use a tool like ScrapeGraphAI to perform the scraping. This library
        # uses LLMs to intelligently scrape and structure data.
        # The API key would be loaded from an environment variable for security.
        openai_api_key = os.getenv("OPENAI_API_KEY")
        #logging.info("Using OpenAI API key for web scraping.", openai_api_key)
        
        # Define the web scraping pipeline using ScrapeGraphAI
        """ graph_config = {
            "api_key": openai_api_key,
            "model": "gpt-3.5-turbo",
        } """
        graph_config = {
        "llm": {
            "api_key": openai_api_key,
            "model": "openai/gpt-4o",
            },
        }
        
        # The source URL and prompt are hardcoded for this MVP to match the scope.[3]
        scraper = SmartScraperGraph(
            prompt=blackboard["user_query"],
            source="https://perinim.github.io/projects",
            config=graph_config
        )
        
        # Execute the scraping task
        try:
            result = scraper.run()
            
            # Post the scraped data to the blackboard for other agents to access.[4]
            # The blackboard acts as a central space for knowledge sharing.[4]
            blackboard["data_to_analyze"] = result
            blackboard["status"] = "data_ready"
            print("Data Acquisition Agent: Scraping complete. Data posted to blackboard.")
            print(f"Scraped data: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Data Acquisition Agent: An error occurred during scraping - {e}")
            blackboard["status"] = "failed"
            blackboard["final_report"] = f"Error: Web scraping failed with error: {e}"
        
        time.sleep(1) # Simulate processing time

def AnalysisAndReportingAgent():
    """
    The Analysis & Reporting Agent monitors the blackboard for 'data_ready' status.
    Once data is available, it processes it and generates the final report.
    """
    if blackboard["status"] == "data_ready":
        print("\nAnalysis & Reporting Agent: Data found on blackboard. Generating report.")
        
        raw_data = blackboard["data_to_analyze"]
        report_text = "### Final Research Report\n\n"
        
        # In a real system, this would be a complex analysis.[5, 6]
        # For the MVP, we simply format the structured JSON data into a readable report.
        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                report_text += f"- **{key.title()}:**\n"
                if isinstance(value, list):
                    for item in value:
                        report_text += f"  - {item}\n"
                else:
                    report_text += f"  - {value}\n"
        else:
            report_text += str(raw_data)
            
        # Post the final report to the blackboard
        blackboard["final_report"] = report_text
        blackboard["status"] = "complete"
        print("Analysis & Reporting Agent: Report generated and posted to blackboard.")
        time.sleep(1) # Simulate processing time

# --- MAIN WORKFLOW EXECUTION ---

if __name__ == "__main__":
    print("Starting MARA MVP Workflow...")
    
    # Step 1: Query Submission (user submits a predefined query)
    user_query = "List me all the articles on the page with their description and the author."
    OrchestratorAgent(user_query)
    
    # Step 2: Task Delegation & Data Retrieval
    DataAcquisitionAgent()
    
    # Step 3: Information Synthesis & Final Output
    AnalysisAndReportingAgent()

    # Step 4: Check and print final result
    print("\n--- Final Output ---")
    if blackboard["status"] == "complete":
        print(blackboard["final_report"])
    else:
        print(f"Workflow finished with status: {blackboard['status']}. No final report was generated.")
