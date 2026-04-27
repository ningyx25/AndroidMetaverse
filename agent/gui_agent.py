import re
import ast
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.state import GUIState, Action, ActionType, Direction, GoalStatus, UIElementNode
from agent.prompt import GUI_AGENT_SYSTEM_PROMPT, GUI_AGENT_TEMPLATE


class GUIAgent:
    def __init__(
        self, llm: ChatOpenAI, 
        system_prompt: str = GUI_AGENT_SYSTEM_PROMPT,
        template: str = GUI_AGENT_TEMPLATE
    ):
        self.llm = llm
        self.system_prompt = system_prompt
        self.template = template

    @staticmethod
    def parse_reason_action_output(raw: str):
        """Parse model output into (thought, step_goal, action_dict).

        Supports two formats:
        1) JSON object: {"Thought": ..., "Step Goal": ..., "Action": {...}}
        2) Plain text:
            Thought: <one sentence>
            Step Goal: <short imperative>
            Action: <JSON object>

        Returns:
            (thought, step_goal, action_dict) — any field is None if not found.
        """
        raw = raw or ''

        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()

        # Try whole-output JSON first
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj.get('Thought', ""), obj.get('Step Goal', ""), obj.get('Action', {})
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: regex extraction
        thought_match = re.search(r'Thought:\s*(.+?)(?=Step Goal:|Action:|$)', text, re.DOTALL)
        step_goal_match = re.search(r'Step Goal:\s*(.+?)(?=Action:|$)', text, re.DOTALL)
        action_match = re.search(r'Action:\s*(\{.*\})', text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else ""
        step_goal = step_goal_match.group(1).strip() if step_goal_match else ""
        action_dict = {}

        if action_match:
            try:
                action_dict = json.loads(action_match.group(1).strip())
            except json.JSONDecodeError:
                try:
                    action_dict = ast.literal_eval(action_match.group(1).strip())
                except Exception:
                    action_dict = {}

        return thought, step_goal, action_dict


    def plan_action(self, state):
        task_goal: str = state['task_goal']

        step_goal_his: list[str] = state['step_goal_history']
        if len(step_goal_his) > 0:
            step_goal_his = ";".join([
                f"Step {i+1}: {g}" for i, g in enumerate(step_goal_his)
            ])
        else:
            step_goal_his = "You just started, no action has been performed yet."
        
        current_node: UIElementNode = state['ui_elements']
        current_ui_elements = current_node["ui_elements"]

        prompt = self.template.format(
            task_goal=task_goal,
            step_goal_history=step_goal_his,
            current_ui_elements=json.dumps(current_ui_elements, ensure_ascii=False)
        )

        raw = ""
        for chunk in self.llm.stream([
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]):
            print(chunk.content, end="", flush=True)
            raw += chunk.content
        print()

        thought, step_goal, action = self.parse_reason_action_output(raw)
        return {
            **state,
            "last_action": action,
            "thought_history": state["thought_history"] + [thought],
            "step_goal_history": state["step_goal_history"] + [step_goal]
        }
