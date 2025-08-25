import time
import json
import os
from openai import OpenAI # Import the OpenAI client for LLM interaction

class OrchestratorAgent:
    """
    The Orchestrator Agent's role is expanded beyond the MVP to include
    more sophisticated task decomposition and delegation based on user queries.
    It oversees the entire research workflow.
    Enhanced with LLM-based planning for advanced query decomposition.
    """
    def __init__(self, name: str, blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.llm_client = None
        self._initialize_llm()

    def _initialize_llm(self):
        """Initializes the OpenAI LLM client."""
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"{self.name}: WARNING: OPENAI_API_KEY environment variable not set. LLM-based planning will not function.")
            return
        self.llm_client = OpenAI(api_key=openai_key)
        print(f"{self.name}: OpenAI LLM client initialized.")

    def _llm_decompose_query(self, user_query: str) -> dict:
        """
        Uses an LLM to decompose a complex user query into a structured task.
        Returns a dictionary representing the decomposed task.
        """
        if not self.llm_client:
            print(f"{self.name}: LLM client not initialized. Falling back to keyword-based decomposition.")
            return {"task_type": "unsupported_llm_query", "reason": "LLM client not available."}

        prompt = f"""
        You are an intelligent Orchestrator in a Multi-Agent Research & Analysis system.
        Your goal is to decompose a user's complex research query into a structured task
        that can be delegated to specialized agents.

        Your system currently supports the following primary actions:
        - "web_scrape": For gathering raw data from a specific URL. Requires 'source_url', 'target_info'.
            Example: {{"action": "web_scrape", "source_url": "https://perinim.github.io/projects", "target_info": "articles, descriptions, authors"}}
        - "summarize_findings": For summarizing the current synthesized knowledge.
            Example: {{"action": "summarize_findings"}}
        - "filter_by_author": For listing articles by a specific author. Requires 'author_name'.
            Example: {{"action": "filter_by_author", "author_name": "Marco Perini"}}
        - "visualize_author_distribution": For showing an ASCII bar chart of article distribution by author.
            Example: {{"action": "visualize_author_distribution"}}
        - "count_articles_by_author": For counting articles by a specific author. Requires 'author_name'.
            Example: {{"action": "count_articles_by_author", "author_name": "Marco Perini"}}
        - "find_articles_by_keyword": For finding articles containing a specific keyword. Requires 'keyword'.
            Example: {{"action": "find_articles_by_keyword", "keyword": "DQN"}}
        - "identify_prolific_author": For identifying the author with the most articles.
            Example: {{"action": "identify_prolific_author"}}
        - "check_for_changes": For proactively checking the source for new articles or changes.
            Example: {{"action": "check_for_changes"}}
        - "refresh_data": For triggering a full data re-acquisition.
            Example: {{"action": "refresh_data"}}
        - "unsupported_query": If the query cannot be handled by the current agent capabilities. Requires 'reason'.
            Example: {{"action": "unsupported_query", "reason": "The query is too complex or requires capabilities not yet implemented."}}

        User Query: "{user_query}"

        Provide the decomposed task as a JSON object. Ensure the output is *only* the JSON object.
        """

        try:
            print(f"{self.name}: Asking LLM to decompose query: '{user_query}'")
            response = self.llm_client.chat.completions.create(
                model="gpt-4o", # Using a capable model for planning
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0 # Keep it deterministic for task decomposition
            )
            response_content = response.choices[0].message.content
            print(f"{self.name}: LLM Response for query decomposition: {response_content}")
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            print(f"{self.name}: ERROR: LLM returned invalid JSON: {e}")
            return {"action": "unsupported_query", "reason": f"LLM returned invalid JSON: {e}"}
        except Exception as e:
            print(f"{self.name}: ERROR: LLM call failed during query decomposition: {e}")
            return {"action": "unsupported_query", "reason": f"LLM call failed: {e}"}


    def run(self, user_query: str):
        """
        Receives the initial user query, decomposes it, and delegates tasks
        by updating the blackboard.
        Now uses LLM for primary decomposition, with fallback to keyword.
        """
        print(f"{self.name}: Received user query: '{user_query}'")
        self.blackboard.set_data("user_query", user_query)

        decomposed_task = self._llm_decompose_query(user_query)
        action = decomposed_task.get("action")

        if action == "web_scrape":
            task = {"type": "web_scrape", "target": decomposed_task.get("target_info", "articles_info"), "source_url": decomposed_task.get("source_url", "https://perinim.github.io/projects")}
            print(f"{self.name}: Decomposed query (LLM). Delegating 'web_scrape' task. Task object to set: {task}")
            self.blackboard.set_data("current_task", task)
            self.blackboard.set_status("task_delegated_to_data_acquisition")
        elif action == "unsupported_query":
            reason = decomposed_task.get("reason", "Query not recognized for current capabilities.")
            print(f"{self.name}: Query not recognized (LLM). Setting status to 'unsupported_query'. Reason: {reason}")
            self.blackboard.set_status("unsupported_query")
            self.blackboard.set_data("final_report", f"Orchestrator: {reason}")
        else:
            print(f"{self.name}: LLM returned a feedback-like action '{action}' or could not fully decompose. "
                  "Proceeding with potential manual feedback for initial query or refining LLM instruction.")
            if action in ["summarize_findings", "filter_by_author", "visualize_author_distribution", 
                          "count_articles_by_author", "find_articles_by_keyword", "identify_prolific_author", 
                          "check_for_changes", "refresh_data"]: # Added check_for_changes
                 # Create a dummy human feedback to trigger the process_feedback path in the main loop
                 # Store the decomposed task directly in human_feedback as JSON string for process_feedback to parse
                 self.blackboard.set_data("human_feedback", json.dumps(decomposed_task))
                 self.blackboard.set_status("awaiting_re_orchestration")
            else:
                 if "articles" in user_query.lower() and "description" in user_query.lower() and "author" in user_query.lower():
                     task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
                     print(f"{self.name}: Decomposed query (Keyword Fallback). Delegating 'web_scrape' task. Task object to set: {task}")
                     self.blackboard.set_data("current_task", task)
                     self.blackboard.set_status("task_delegated_to_data_acquisition")
                 else:
                     print(f"{self.name}: Query not recognized by LLM or keyword fallback. Setting status to 'unsupported_query'.")
                     self.blackboard.set_status("unsupported_query")
                     self.blackboard.set_data("final_report", "Orchestrator: The initial query could not be automatically decomposed by LLM or keyword fallback. Please refine or use specific feedback.")
        time.sleep(1)

    def process_feedback(self):
        """
        Processes human feedback and potentially delegates new tasks based on it.
        This pathway now handles explicit human feedback OR LLM-generated feedback
        that was routed here from the 'run' method.
        """
        print(f"\n{self.name}: Processing human feedback.")
        feedback_raw = self.blackboard.get_data("human_feedback")
        original_query = self.blackboard.get_data("user_query")

        decomposed_from_feedback = None
        if isinstance(feedback_raw, str) and feedback_raw.strip().startswith('{') and feedback_raw.strip().endswith('}'):
            try:
                # Attempt to parse as JSON if it looks like LLM-generated feedback
                decomposed_from_feedback = json.loads(feedback_raw)
                print(f"{self.name}: Successfully parsed LLM-generated feedback: {decomposed_from_feedback}")
            except json.JSONDecodeError:
                # Not a JSON, treat as plain text feedback
                pass
        
        if decomposed_from_feedback:
            # Handle LLM-generated feedback
            action = decomposed_from_feedback.get("action")
            params = {k: v for k, v in decomposed_from_feedback.items() if k != "action"}

            if action == "summarize_findings":
                print(f"{self.name}: LLM-suggested summary. Delegating task to Analysis & Reporting Agent.")
                summary_task = {"type": "summarize_findings", "from_data_key": "synthesized_knowledge", "original_query": original_query}
                self.blackboard.set_data("current_task", summary_task)
                self.blackboard.set_status("summarize_requested")
            elif action == "filter_by_author":
                author_name = params.get("author_name")
                if author_name:
                    print(f"{self.name}: LLM-suggested filter by author '{author_name}'. Delegating filter task to Analysis & Reporting Agent.")
                    filter_task = {"type": "filter_by_author", "author": author_name, "from_data_key": "raw_scraped_data", "original_query": original_query}
                    self.blackboard.set_data("current_task", filter_task)
                    self.blackboard.set_status("filter_by_author_requested")
                else:
                    print(f"{self.name}: LLM-suggested filter by author, but no author_name parameter found.")
                    self.blackboard.set_status("complete_with_feedback")
            elif action == "visualize_author_distribution":
                print(f"{self.name}: LLM-suggested visualization. Delegating task to Analysis & Reporting Agent.")
                viz_task = {"type": "visualize_author_distribution", "from_data_key": "raw_scraped_data", "original_query": original_query}
                self.blackboard.set_data("current_task", viz_task)
                self.blackboard.set_status("visualize_requested")
            elif action == "refresh_data":
                print(f"{self.name}: LLM-suggested data refresh. Re-delegating data acquisition task.")
                refresh_task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
                self.blackboard.set_data("current_task", refresh_task)
                self.blackboard.set_status("task_delegated_to_data_acquisition")
            elif action == "count_articles_by_author":
                author_name = params.get("author_name")
                if author_name:
                    print(f"{self.name}: LLM-suggested count articles by author '{author_name}'. Delegating query task to Knowledge Query Agent.")
                    query_task = {"type": "count_articles_by_author", "author": author_name, "original_query": original_query}
                    self.blackboard.set_data("current_task", query_task)
                    self.blackboard.set_status("query_requested")
                else:
                    print(f"{self.name}: LLM-suggested count articles by author, but no author_name parameter found.")
                    self.blackboard.set_status("complete_with_feedback")
            elif action == "find_articles_by_keyword":
                keyword = params.get("keyword")
                if keyword:
                    print(f"{self.name}: LLM-suggested find articles by keyword '{keyword}'. Delegating query task to Knowledge Query Agent.")
                    query_task = {"type": "find_articles_by_keyword", "keyword": keyword, "original_query": original_query}
                    self.blackboard.set_data("current_task", query_task)
                    self.blackboard.set_status("query_requested")
                else:
                    print(f"{self.name}: LLM-suggested find articles by keyword, but no keyword parameter found.")
                    self.blackboard.set_status("complete_with_feedback")
            elif action == "identify_prolific_author":
                print(f"{self.name}: LLM-suggested identify prolific author. Delegating task to Analysis & Reporting Agent.")
                prolific_task = {"type": "identify_prolific_author", "original_query": original_query}
                self.blackboard.set_data("current_task", prolific_task)
                self.blackboard.set_status("prolific_author_requested")
            elif action == "check_for_changes": # NEW: Handle LLM-suggested check_for_changes
                print(f"{self.name}: LLM-suggested check for changes. Delegating task to Change Detection Agent.")
                change_task = {"type": "check_for_changes", "original_query": original_query}
                self.blackboard.set_data("current_task", change_task)
                self.blackboard.set_status("check_for_changes_requested")
            else:
                print(f"{self.name}: LLM-generated feedback with unrecognized action: '{action}'.")
                self.blackboard.set_status("complete_with_feedback")
        else:
            # Handle plain text human feedback (existing keyword-based logic)
            lower_feedback = feedback_raw.lower()
            
            author_name = None
            query_task_type = None

            if "how many articles did" in lower_feedback and "publish" in lower_feedback:
                did_idx = lower_feedback.find("did")
                publish_idx = lower_feedback.find("publish", did_idx)
                if did_idx != -1 and publish_idx != -1 and publish_idx > did_idx:
                    author_phrase = feedback_raw[did_idx + len("did"):publish_idx].strip()
                    if author_phrase:
                        author_name = author_phrase
                        query_task_type = "count_articles_by_author"
            
            if query_task_type is None and "how many articles by" in lower_feedback:
                author_keyword_index = lower_feedback.find("how many articles by")
                author_name_start_index = author_keyword_index + len("how many articles by")
                author_name = feedback_raw[author_name_start_index:].strip("?. ").strip()
                if author_name:
                    query_task_type = "count_articles_by_author"

            if query_task_type == "count_articles_by_author" and author_name:
                print(f"{self.name}: Human requested count of articles by author '{author_name}'. Delegating query task to Knowledge Query Agent.")
                query_task = {"type": "count_articles_by_author", "author": author_name, "original_query": original_query}
                self.blackboard.set_data("current_task", query_task)
                self.blackboard.set_status("query_requested")
            
            elif "summarize key findings" in lower_feedback:
                print(f"{self.name}: Human requested summary of key findings. Delegating summary task to Analysis & Reporting Agent.")
                summary_task = {"type": "summarize_findings", "from_data_key": "synthesized_knowledge", "original_query": original_query}
                self.blackboard.set_data("current_task", summary_task)
                self.blackboard.set_status("summarize_requested")
            elif "articles by author" in lower_feedback and "how many" not in lower_feedback:
                author_keyword_index = lower_feedback.find("articles by author")
                author_name_start_index = author_keyword_index + len("articles by author")
                author_name_for_filter = feedback_raw[author_name_start_index:].strip("?. ").strip()
                if author_name_for_filter:
                    print(f"{self.name}: Human requested articles by author '{author_name_for_filter}'. Delegating filter task to Analysis & Reporting Agent.")
                    filter_task = {"type": "filter_by_author", "author": author_name_for_filter, "from_data_key": "raw_scraped_data", "original_query": original_query}
                    self.blackboard.set_data("current_task", filter_task)
                    self.blackboard.set_status("filter_by_author_requested")
                else:
                    print(f"{self.name}: Could not extract author name from feedback: '{feedback_raw}'.")
                    self.blackboard.set_status("complete_with_feedback")
            elif "show article distribution by author" in lower_feedback:
                print(f"{self.name}: Human requested article distribution by author. Delegating visualization task to Analysis & Reporting Agent.")
                viz_task = {"type": "visualize_author_distribution", "from_data_key": "raw_scraped_data", "original_query": original_query}
                self.blackboard.set_data("current_task", viz_task)
                self.blackboard.set_status("visualize_requested")
            elif "refresh data" in lower_feedback:
                print(f"{self.name}: Human requested data refresh. Re-delegating data acquisition task.")
                refresh_task = {"type": "web_scrape", "target": "articles_info", "source_url": "https://perinim.github.io/projects"}
                self.blackboard.set_data("current_task", refresh_task)
                self.blackboard.set_status("task_delegated_to_data_acquisition")
            elif "find articles about" in lower_feedback:
                keyword_index = lower_feedback.find("find articles about")
                keyword_start_index = keyword_index + len("find articles about")
                keyword = feedback_raw[keyword_start_index:].strip("?. ").strip()
                if keyword:
                    print(f"{self.name}: Human requested articles containing keyword '{keyword}'. Delegating query task to Knowledge Query Agent.")
                    query_task = {"type": "find_articles_by_keyword", "keyword": keyword, "original_query": original_query}
                    self.blackboard.set_data("current_task", query_task)
                    self.blackboard.set_status("query_requested")
                else:
                    print(f"{self.name}: Could not extract keyword for query from feedback: '{feedback_raw}'.")
                    self.blackboard.set_status("complete_with_feedback")
            elif "who is the most prolific author" in lower_feedback or "most prolific author" in lower_feedback:
                print(f"{self.name}: Human requested identification of the most prolific author. Delegating task to Analysis & Reporting Agent.")
                prolific_task = {"type": "identify_prolific_author", "original_query": original_query}
                self.blackboard.set_data("current_task", prolific_task)
                self.blackboard.set_status("prolific_author_requested")
            elif "check for new articles" in lower_feedback or "detect changes" in lower_feedback: # NEW: Handle plain text for change detection
                print(f"{self.name}: Human requested check for new articles/changes. Delegating task to Change Detection Agent.")
                change_task = {"type": "check_for_changes", "original_query": original_query}
                self.blackboard.set_data("current_task", change_task)
                self.blackboard.set_status("check_for_changes_requested")
            else:
                print(f"{self.name}: Human feedback received but no specific follow-up action identified for: '{feedback_raw}'.")
                self.blackboard.set_status("complete_with_feedback")
        time.sleep(1)
