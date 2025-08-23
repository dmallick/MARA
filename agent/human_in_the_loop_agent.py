import time

class HumanInTheLoopAgent:
    """
    The Human-in-the-Loop Agent facilitates user feedback and can potentially
    trigger refinement loops based on human input.
    """
    def __init__(self, name: str, blackboard):
        self.name = name
        self.blackboard = blackboard
        print(f"{self.name}: Initialized.")
        self.blackboard.register_observer("status", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and (value == "complete" or value == "failed" or value == "timed_out" or value == "unsupported_query"):
            self.execute_feedback_prompt()
        elif key == "status" and value == "complete_with_feedback":
            self.execute_feedback_prompt()


    def execute_feedback_prompt(self):
        print(f"\n{self.name}: Workflow complete/failed. Engaging human for feedback.")
        
        print("\n--- HUMAN INTERVENTION REQUIRED ---")
        user_feedback = input(
            "Human-in-the-Loop: Please review the MARA report above. "
            "Do you have any feedback or a follow-up request? "
            "(e.g., 'summarize key findings', 'articles by author Marco Perini', "
            "'show article distribution by author', 'age data', 'refresh data', or 'exit' to finish): "
        )
        print("--- END HUMAN INTERVENTION ---")

        if user_feedback.lower() == "exit":
            print(f"{self.name}: Received 'exit'. Ending human feedback loop.")
            self.blackboard.set_data("human_feedback", "User chose to exit.")
        else:
            print(f"{self.name}: Received human feedback: '{user_feedback}'. Posting to blackboard.")
            self.blackboard.set_data("human_feedback", user_feedback)
            self.blackboard.set_status("awaiting_re_orchestration")
