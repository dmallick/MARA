import time
import json
from collections import defaultdict # Used for visualizations and counting
from datetime import datetime # Used for timestamps

class AnalysisAndReportingAgent:
    """
    The Analysis & Reporting Agent monitors the blackboard for 'data_validated' status.
    Once data is available, it processes it, generates insights, and compiles the final report.
    It can also generate a summary of key findings upon request or visualize data.
    Updated to handle the new knowledge graph structure.
    Now includes functionality to identify the most prolific author.
    Now includes functionality to report change detection results.
    """
    def __init__(self, name: str, blackboard):
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
        elif key == "status" and value == "visualize_requested":
            self.execute_visualization_task()
        elif key == "status" and value == "prolific_author_requested":
            self.execute_prolific_author_task()
        elif key == "status" and value in ["changes_detected", "no_changes_detected"]: # NEW: Listen for change detection results
            self.execute_change_detection_report()
        elif key == "status" and (value in ["data_acquisition_failed", "unsupported_query", "knowledge_synthesis_failed", "data_validation_failed", "failed"]):
            self.execute_failure_report()

    def execute_task(self):
        print(f"\n{self.name}: Data validated. Generating final report and insights.")
        raw_data = self.blackboard.get_data("raw_scraped_data") 
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        validation_result = self.blackboard.get_data("validation_result")
        
        report_text = "### MARA Research Report\n\n"
        report_text += f"**Overall Process Status:** {self.blackboard.get_status()}\n\n"
        
        if synthesized_data and "extracted_entities" in synthesized_data:
            extracted_entities_meta = synthesized_data["extracted_entities"]
            if "timestamp" in extracted_entities_meta:
                 report_text += f"**Report Generated At:** {extracted_entities_meta['timestamp']}\n"
                 report_text += f"**Synthesized Data Age:** {extracted_entities_meta.get('data_age', 'N/A')} cycles\n\n"


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

        if synthesized_data and "extracted_entities" in synthesized_data and \
           "nodes" in synthesized_data["extracted_entities"] and \
           "relationships" in synthesized_data["extracted_entities"]:
            
            report_text += f"#### Knowledge Synthesis Summary (Structured Graph):\n{synthesized_data.get('summary', 'N/A')}\n\n"
            
            nodes = synthesized_data["extracted_entities"]["nodes"]
            relationships = synthesized_data["extracted_entities"]["relationships"]

            report_text += "**Entities:**\n"
            if nodes.get("articles"):
                report_text += "  - Articles:\n"
                for article in nodes["articles"]:
                    report_text += f"    - ID: {article['id']}, Title: '{article['properties']['title']}'\n"
            if nodes.get("authors"):
                report_text += "  - Authors:\n"
                for author in nodes["authors"]:
                    report_text += f"    - ID: {author['id']}, Name: '{author['properties']['name']}'\n"
            
            report_text += "\n**Relationships:**\n"
            if relationships:
                for rel in relationships:
                    source_article = next((a for a in nodes["articles"] if a["id"] == rel["source_id"]), None)
                    target_author = next((a for a in nodes["authors"] if a["id"] == rel["target_id"]), None)
                    
                    source_title = source_article['properties']['title'] if source_article else rel['source_id']
                    target_name = target_author['properties']['name'] if target_author else rel['target_id']

                    report_text += f"  - '{source_title}' {rel['type']} '{target_name}'\n"
            else:
                report_text += "  - No relationships found.\n"
            
            report_text += "\n"
        else:
            report_text += "No structured knowledge graph available for reporting.\n\n"

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
            error_msg = "ERROR: 'current_task' is None. Cannot execute summary task."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("failed")
            self.blackboard.set_data("final_report", "Error: Cannot generate summary, no valid task found.")
            return

        synthesized_data = self.blackboard.get_data(task.get("from_data_key", "synthesized_knowledge"))

        summary_report_text = f"### MARA Research Report - Key Findings Summary\n\n"
        if synthesized_data and "extracted_entities" in synthesized_data:
            extracted_entities_meta = synthesized_data["extracted_entities"]
            if "timestamp" in extracted_entities_meta:
                 summary_report_text += f"**Summary Generated At:** {extracted_entities_meta['timestamp']}\n"
                 summary_report_text += f"**Synthesized Data Age:** {extracted_entities_meta.get('data_age', 'N/A')} cycles\n\n"

        if synthesized_data and "extracted_entities" in synthesized_data and \
           "nodes" in synthesized_data["extracted_entities"] and \
           "relationships" in synthesized_data["extracted_entities"]:
            
            nodes = synthesized_data["extracted_entities"]["nodes"]
            relationships = synthesized_data["extracted_entities"]["relationships"]

            summary_report_text += "Here are the key findings based on the knowledge graph:\n"
            if nodes.get("articles"):
                for article in nodes["articles"]:
                    article_title = article['properties']['title']
                    author_id = next((rel['target_id'] for rel in relationships if rel['source_id'] == article['id'] and rel['type'] == 'AUTHORED_BY'), None)
                    author_name = next((a['properties']['name'] for a in nodes["authors"] if a['id'] == author_id), "Unknown Author")
                    summary_report_text += f"- **Article:** '{article_title}' by {author_name}. Snippet: '{article['properties']['description_snippet']}'\n"
            else:
                summary_report_text += "- No articles found in the knowledge graph to summarize.\n"

            summary_report_text += f"\nOriginal request: '{task.get('original_query', 'N/A')}'\n"
            summary_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"
            
            self.blackboard.set_data("final_report", summary_report_text)
            self.blackboard.set_status("complete")
            print(f"{self.name}: Key findings summary generated and posted.")
        else:
            error_msg = "No structured knowledge graph available to summarize."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("failed")
            self.blackboard.set_data("final_report", error_msg)
        time.sleep(1)

    def execute_filter_by_author_task(self):
        """Filters raw scraped data to show articles by a specific author.
           Now filters based on the knowledge graph structure."""
        print(f"\n{self.name}: Filter by author task received. Filtering articles from knowledge graph.")
        task = self.blackboard.get_data("current_task")

        if task is None:
            error_msg = "ERROR: 'current_task' is None. Cannot execute filter by author task."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("failed")
            self.blackboard.set_data("final_report", error_msg)
            return

        author_to_filter = task.get("author").lower()
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")

        filter_report_text = f"### MARA Research Report - Articles by Author: '{author_to_filter.title()}' (from Knowledge Graph)\n\n"
        if synthesized_data and "extracted_entities" in synthesized_data:
            extracted_entities_meta = synthesized_data["extracted_entities"]
            if "timestamp" in extracted_entities_meta:
                 filter_report_text += f"**Generated At:** {extracted_entities_meta['timestamp']}\n"
                 filter_report_text += f"**Synthesized Data Age:** {extracted_entities_meta.get('data_age', 'N/A')} cycles\n\n"
        
        found_articles = []

        if synthesized_data and "extracted_entities" in synthesized_data and \
           "nodes" in synthesized_data["extracted_entities"] and \
           "relationships" in synthesized_data["extracted_entities"]:
            
            nodes = synthesized_data["extracted_entities"]["nodes"]
            relationships = synthesized_data["extracted_entities"]["relationships"]

            target_author_id = next((a['id'] for a in nodes["authors"] if a['properties']['name'].lower() == author_to_filter), None)

            if target_author_id:
                article_ids_by_author = [rel['source_id'] for rel in relationships if rel['target_id'] == target_author_id and rel['type'] == 'AUTHORED_BY']
                
                for article_id in article_ids_by_author:
                    article = next((a for a in nodes["articles"] if a['id'] == article_id), None)
                    if article:
                        found_articles.append(article)
            
            if found_articles:
                filter_report_text += f"Found {len(found_articles)} article(s) by '{author_to_filter.title()}':\n\n"
                for article in found_articles:
                    title = article['properties'].get("title", "N/A")
                    description_snippet = article['properties'].get("description_snippet", "N/A")
                    filter_report_text += f"- **Title:** {title}\n  - **Snippet:** {description_snippet}\n\n"
            else:
                filter_report_text += f"No articles found by author '{author_to_filter.title()}' in the knowledge graph.\n\n"
        else:
            filter_report_text += "No structured knowledge graph available to filter.\n\n"
        
        filter_report_text += f"Original request: '{task.get('original_query', 'N/A')}'\n"
        filter_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"

        self.blackboard.set_data("final_report", filter_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Articles filtered by author from knowledge graph and report posted.")
        time.sleep(1)


    def execute_visualization_task(self):
        """Generates a simple ASCII bar chart of article distribution by author
           from the knowledge graph structure."""
        print(f"\n{self.name}: Visualization task received. Generating article distribution by author from knowledge graph.")
        task = self.blackboard.get_data("current_task")

        if task is None:
            error_msg = "ERROR: 'current_task' is None. Cannot execute visualization task."
            print(f"{self.name}: {error_msg}")
            self.blackboard.set_data("error_message", error_msg)
            self.blackboard.set_status("failed")
            self.blackboard.set_data("final_report", error_msg)
            return

        synthesized_data = self.blackboard.get_data("synthesized_knowledge")

        viz_report_text = f"### MARA Research Report - Article Distribution by Author (ASCII Bar Chart from Knowledge Graph)\n\n"
        if synthesized_data and "extracted_entities" in synthesized_data:
            extracted_entities_meta = synthesized_data["extracted_entities"]
            if "timestamp" in extracted_entities_meta:
                 viz_report_text += f"**Generated At:** {extracted_entities_meta['timestamp']}\n"
                 viz_report_text += f"**Synthesized Data Age:** {extracted_entities_meta.get('data_age', 'N/A')} cycles\n\n"
        
        if synthesized_data and "extracted_entities" in synthesized_data and \
           "nodes" in synthesized_data["extracted_entities"] and \
           "relationships" in synthesized_data["extracted_entities"]:
            
            nodes = synthesized_data["extracted_entities"]["nodes"]
            relationships = synthesized_data["extracted_entities"]["relationships"]

            author_counts = defaultdict(int)
            for rel in relationships:
                if rel['type'] == 'AUTHORED_BY':
                    author_id = rel['target_id']
                    author_name = next((a['properties']['name'] for a in nodes["authors"] if a['id'] == author_id), "Unknown Author")
                    author_counts[author_name] += 1
            
            if author_counts:
                max_articles = max(author_counts.values())
                if max_articles == 0:
                    viz_report_text += "No articles found in the knowledge graph to visualize author distribution.\n"
                    self.blackboard.set_data("final_report", viz_report_text)
                    self.blackboard.set_status("complete")
                    print(f"{self.name}: No articles found for visualization.")
                    return

                viz_report_text += "```\n"
                viz_report_text += "Article Distribution by Author (from Knowledge Graph):\n"
                viz_report_text += "-----------------------------------------------------\n"
                
                sorted_authors = sorted(author_counts.keys())

                for author_name in sorted_authors:
                    count = author_counts[author_name]
                    bar_length = int((count / max_articles) * 30)
                    bar = '#' * bar_length
                    viz_report_text += f"{author_name.ljust(20)} | {bar} ({count})\n"
                viz_report_text += "```\n"
            else:
                viz_report_text += "No authors or articles found in the knowledge graph to generate distribution.\n"
        else:
            viz_report_text += "No structured knowledge graph available for visualization.\n\n"
        
        viz_report_text += f"Original request: '{task.get('original_query', 'N/A')}'\n"
        viz_report_text += f"Requested follow-up: '{self.blackboard.get_data('human_feedback')}'\n"

        self.blackboard.set_data("final_report", viz_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Article distribution by author generated from knowledge graph and posted.")
        time.sleep(1)

    def execute_prolific_author_task(self):
        """
        Identifies and reports the most prolific author from the knowledge graph.
        """
        print(f"\n{self.name}: Task received: Identify most prolific author. Analyzing knowledge graph.")
        task = self.blackboard.get_data("current_task")
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")

        prolific_report_text = f"### MARA Research Report - Most Prolific Author\n\n"
        prolific_report_text += f"**Original Query:** '{task.get('original_query', 'N/A')}'\n"
        prolific_report_text += f"**Requested Follow-up:** '{self.blackboard.get_data('human_feedback')}'\n\n"

        if not synthesized_data or "extracted_entities" not in synthesized_data or \
           "nodes" not in synthesized_data["extracted_entities"] or \
           "relationships" not in synthesized_data["extracted_entities"]:
            prolific_report_text += "Error: No structured knowledge graph available to identify prolific author."
            self.blackboard.set_data("final_report", prolific_report_text)
            self.blackboard.set_status("failed")
            print(f"{self.name}: Failed to identify prolific author: No knowledge graph.")
            return

        nodes = synthesized_data["extracted_entities"]["nodes"]
        relationships = synthesized_data["extracted_entities"]["relationships"]
        authors = nodes.get("authors", [])

        author_article_counts = defaultdict(int)
        for rel in relationships:
            if rel['type'] == 'AUTHORED_BY':
                author_id = rel['target_id']
                author_name = next((a['properties']['name'] for a in authors if a['id'] == author_id), "Unknown Author")
                author_article_counts[author_name] += 1
        
        if author_article_counts:
            most_prolific_author = max(author_article_counts, key=author_article_counts.get)
            max_articles = author_article_counts[most_prolific_author]
            prolific_report_text += f"**Insight:** The most prolific author identified is **'{most_prolific_author}'** with {max_articles} article(s).\n"
        else:
            prolific_report_text += "No authors or articles found in the knowledge graph to identify the most prolific author.\n"

        self.blackboard.set_data("final_report", prolific_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Most prolific author identified and report posted.")
        time.sleep(1)

    def execute_change_detection_report(self): # NEW: Method to report change detection results
        """
        Reports the findings from the Change Detection Agent.
        """
        print(f"\n{self.name}: Task received: Report change detection results.")
        change_report = self.blackboard.get_data("change_detection_report")
        current_status = self.blackboard.get_status() # Will be "changes_detected" or "no_changes_detected"

        report_text = f"### MARA Change Monitoring Update\n\n"
        report_text += f"**Overall Status of Change Detection:** {current_status.replace('_', ' ').title()}\n\n"
        
        if change_report:
            report_text += change_report # Directly embed the report from ChangeDetectionAgent
        else:
            report_text += "No specific change detection report found on the blackboard."

        self.blackboard.set_data("final_report", report_text)
        # Status is already set by ChangeDetectionAgent, just ensuring report is complete
        self.blackboard.set_status("complete") 
        print(f"{self.name}: Change detection report compiled and posted.")
        time.sleep(1)


    def execute_failure_report(self):
        """Generates a simple report if a previous step failed."""
        print(f"\n{self.name}: Executing failure report.")
        failure_message = self.blackboard.get_data("final_report")
        error_details = self.blackboard.get_data("error_message")

        report_text = f"### MARA Research Report - Process Failed\n\n"
        report_text += f"**Overall Process Status:** {self.blackboard.get_status()}\n\n"
        report_text += f"Reason for failure: {failure_message if failure_message else 'An unspecified error occurred.'}\n"
        if error_details:
            report_text += f"Error Details: {error_details}\n\n"
        report_text += "Please review the process logs for more details."
        
        self.blackboard.set_data("final_report", report_text)
        print(f"{self.name}: Failure report generated and posted to blackboard.")
        time.sleep(1)
