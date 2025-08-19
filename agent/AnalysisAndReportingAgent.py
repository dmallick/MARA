from comm.blackboard import Blackboard
import time


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