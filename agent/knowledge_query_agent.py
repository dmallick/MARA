import time
import json
from collections import defaultdict

class KnowledgeQueryAgent:
    """
    The Knowledge Query Agent is responsible for interpreting specific user queries
    and extracting answers directly from the structured knowledge graph stored on the blackboard.
    """
    def __init__(self, name: str, blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "query_requested":
            self.execute_query()

    def execute_query(self):
        print(f"\n{self.name}: Query task received. Executing query against knowledge graph.")
        task = self.blackboard.get_data("current_task")
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")

        query_report_text = f"### MARA Research Report - Knowledge Query Result\n\n"
        query_report_text += f"**Original Query:** '{task.get('original_query', 'N/A')}'\n"
        query_report_text += f"**Requested Follow-up:** '{self.blackboard.get_data('human_feedback')}'\n\n"
        
        if not synthesized_data or "extracted_entities" not in synthesized_data or \
           "nodes" not in synthesized_data["extracted_entities"] or \
           "relationships" not in synthesized_data["extracted_entities"]:
            query_report_text += "Error: No structured knowledge graph available to query."
            selfboard.set_data("final_report", query_report_text)
            self.blackboard.set_status("failed")
            print(f"{self.name}: Failed to execute query: No knowledge graph.")
            return

        nodes = synthesized_data["extracted_entities"]["nodes"]
        relationships = synthesized_data["extracted_entities"]["relationships"]
        articles = nodes.get("articles", [])
        authors = nodes.get("authors", [])

        query_type = task.get("type")

        if query_type == "count_articles_by_author":
            author_name_query = task.get("author").lower()
            matching_author_id = next((a['id'] for a in authors if a['properties']['name'].lower() == author_name_query), None)

            if matching_author_id:
                article_count = sum(1 for rel in relationships if rel['target_id'] == matching_author_id and rel['type'] == 'AUTHORED_BY')
                query_report_text += f"**Result:** '{matching_author_id.replace('author_', '').replace('_', ' ').title()}' authored {article_count} article(s).\n"
            else:
                query_report_text += f"**Result:** No author found matching '{author_name_query.title()}' in the knowledge graph.\n"
        
        elif query_type == "find_articles_by_keyword":
            keyword_query = task.get("keyword").lower()
            matching_articles = []
            for article in articles:
                title = article['properties'].get('title', '').lower()
                description_snippet = article['properties'].get('description_snippet', '').lower()
                if keyword_query in title or keyword_query in description_snippet:
                    matching_articles.append(article)
            
            if matching_articles:
                query_report_text += f"**Result:** Found {len(matching_articles)} article(s) containing the keyword '{keyword_query}':\n"
                for article in matching_articles:
                    article_title = article['properties'].get('title', 'N/A')
                    article_snippet = article['properties'].get('description_snippet', 'N/A')
                    
                    # Find author for display
                    author_id = next((rel['target_id'] for rel in relationships if rel['source_id'] == article['id'] and rel['type'] == 'AUTHORED_BY'), None)
                    author_name = next((a['properties']['name'] for a in authors if a['id'] == author_id), "Unknown Author")

                    query_report_text += f"- **Title:** '{article_title}' by {author_name}\n  - **Snippet:** {article_snippet}\n"
            else:
                query_report_text += f"**Result:** No articles found containing the keyword '{keyword_query}'.\n"

        else:
            query_report_text += "Error: Unknown query type."
            self.blackboard.set_data("error_message", "Unknown query type received by Knowledge Query Agent.")

        self.blackboard.set_data("final_report", query_report_text)
        self.blackboard.set_status("complete")
        print(f"{self.name}: Query execution complete. Result posted to blackboard.")
        time.sleep(1)
