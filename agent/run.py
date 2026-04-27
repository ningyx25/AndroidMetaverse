from agent.config import llm
from agent.graph import build_graph
from agent.suite_agent import SuiteAgent
from agent.gui_agent import GUIAgent
from agent.android_agent import AndroidAgent
from agent.state import SuiteState

suite_agent = SuiteAgent(llm)
gui_agent = GUIAgent(llm)
android_agent = AndroidAgent(llm)

suite_graph = build_graph(suite_agent, gui_agent, android_agent)

test_state: SuiteState = {
    "task_id": 1,
    "task_type": "test",
    "task_goal": "",
    "ui_elements": {"ui_elements": [], "parent": None, "children": {}},
    "last_action": None,
    "thought_history": [],
    "step_goal_history": [],
    "action_history": [],
    "ui_elements_history": {"root": {"ui_elements": [], "parent": None, "children": {}}},
    "is_successful": False,
}

result = suite_graph.invoke(test_state)
print("is_successful:", result["is_successful"])
print("action_history:")
for action in result["action_history"]:
    print(" ", action)
