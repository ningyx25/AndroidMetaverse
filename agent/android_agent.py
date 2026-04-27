import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.state import AndroidState, UIElementNode, UIElement, Action
from agent.prompt import (
    ANDROID_AGENT_SYSTEM_PROMPT,
    ANDROID_AGENT_TEMPLATE,
    JSON_UI_ElEM_SCHEMA
)


class AndroidAgent:
    def __init__(
        self, llm: ChatOpenAI, 
        system_prompt: str = ANDROID_AGENT_SYSTEM_PROMPT,
        template: str = ANDROID_AGENT_TEMPLATE,
    ):
        self.llm = llm
        self.system_prompt = system_prompt
        self.template = template

    @staticmethod
    def format_action(action: dict) -> str:
        t = action.get("action_type", "unknown").upper()
        idx = action.get("index")
        match t:
            case "CLICK" | "DOUBLE_TAP" | "LONG_PRESS":
                return f"{t} INDEX {idx}"
            case "INPUT_TEXT":
                return f"INPUT_TEXT INDEX {idx} TEXT {action.get('text', '')}"
            case "SCROLL" | "SWIPE":
                return f"{t} INDEX {idx} DIRECTION {action.get('direction', '').upper()}"
            case "OPEN_APP":
                return f"OPEN_APP {action.get('app_name', '')}"
            case "STATUS" | "ANSWER":
                return f"{t} {action.get('goal_status', '').upper()}"
            case "KEYBOARD_ENTER" | "NAVIGATE_BACK" | "NAVIGATE_HOME" | "WAIT":
                return t
            case _:
                return "UNKNOWN"

    def execute_action(self, state):
        current_node: UIElementNode = state['ui_elements']
        last_action: Action = state["last_action"]

        prompt = self.template.format(
            ui_elements=json.dumps(current_node['ui_elements'], ensure_ascii=False),
            action=self.format_action(last_action)
        )

        content = ""
        for chunk in self.llm.stream([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]):
            print(chunk.content, end="", flush=True)
            content += chunk.content
        print()

        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        ui_data = json.loads(content)

        new_node: UIElementNode = {
            "ui_elements": ui_data["ui_elements"],
            "parent": current_node,
            "children": {}
        }
        current_node["children"][self.format_action(last_action)] = new_node

        return {
            **state,
            "ui_elements": new_node,
            "action_history": state["action_history"] + [last_action],
        }
