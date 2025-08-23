import time

class DataRefreshAgent:
    """
    The Data Refresh Agent monitors the freshness of the synthesized knowledge
    and can trigger a data re-acquisition if data is deemed stale.
    """
    def __init__(self, name: str, blackboard, stale_threshold: int = 2):
        self.name = name
        self.blackboard = blackboard
        self.stale_threshold = stale_threshold
        print(f"{self.name}: Initialized with stale threshold: {self.stale_threshold} cycles.")
        self.blackboard.register_observer("status", self.on_blackboard_change)
        self.blackboard.register_observer("synthesized_knowledge", self.on_blackboard_change)

    def on_blackboard_change(self, key, value):
        if key == "status" and value == "complete":
            self._check_for_staleness()
        elif key == "synthesized_knowledge" and value is not None:
            self._check_for_staleness()

    def _check_for_staleness(self):
        synthesized_data = self.blackboard.get_data("synthesized_knowledge")
        if synthesized_data and "extracted_entities" in synthesized_data and \
           "data_age" in synthesized_data["extracted_entities"]:
            current_age = synthesized_data["extracted_entities"]["data_age"]
            if current_age >= self.stale_threshold:
                print(f"\n{self.name}: DETECTED STALE DATA! Synthesized knowledge is {current_age} cycles old (threshold: {self.stale_threshold}).")
                print(f"{self.name}: Requesting data refresh from Orchestrator.")
                self.blackboard.set_data("human_feedback", "refresh data")
                self.blackboard.set_status("awaiting_re_orchestration")
            else:
                print(f"{self.name}: Synthesized knowledge is fresh ({current_age} cycles). No refresh needed.")
        else:
            if self.blackboard.get_status() == "complete" or self.blackboard.get_status() == "synthesized_knowledge":
                print(f"{self.name}: No synthesized knowledge or age info found to check staleness.")
