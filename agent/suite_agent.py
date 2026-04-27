from langchain_openai import ChatOpenAI
from langgraph.graph import END

from agent.state import SuiteState, UIElementNode, ActionType


class SuiteAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def initialize_task(self, state: SuiteState) -> SuiteState:
        root_node: UIElementNode = {
            "ui_elements": [
                {
                    "name": "submit_button",
                    "type": "button",
                    "text": "提交",
                    "description": {"color": "#007AFF", "style": "rounded"},
                    "position": {"x_min": 100, "x_max": 200, "y_min": 300, "y_max": 350},
                    "state": {
                        "is_checked": False, "is_checkable": False, "is_clickable": True,
                        "is_editable": False, "is_enabled": True, "is_focused": False,
                        "is_focusable": True, "is_long_clickable": False, "is_scrollable": False,
                        "is_selected": False, "is_visible": True
                    },
                    "index": 1
                }
            ],
            "parent": None,
            "children": {}
        }
        return {"ui_elements": root_node}

    def get_task_goal(self, state: SuiteState) -> SuiteState:
        return {"task_goal": "提交信息。"}

    def get_task_score(self, state: SuiteState) -> SuiteState:
        return {"is_successful": True}

    def should_continue(self, state: SuiteState) -> str:
        last = state.get("last_action")
        if last and last.get("action_type") in (ActionType.STATUS, ActionType.ANSWER):
            return "get_task_score"
        return "execute_action"
