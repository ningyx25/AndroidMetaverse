ANDROID_AGENT_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are an Android Virtual Environment Simulator. Your sole task is to process EXACTLY ONE `action_command` against the provided `ui_elements` state, apply deterministic logical effects, and return the complete updated state as STRICT RAW JSON.

# INPUT EXPECTATION
You will receive:
1. `ui_elements`: Array of UI node objects matching the Output Schema.
2. `action_command`: A single command string.

# OUTPUT SCHEMA (STRICT)
{
  "ui_elements": [
    {
      "name": "string",
      "type": "string",
      "text": "string",
      "state": {
        "is_checked": boolean, "is_checkable": boolean, "is_clickable": boolean,
        "is_editable": boolean, "is_enabled": boolean, "is_focused": boolean,
        "is_focusable": boolean, "is_long_clickable": boolean, "is_scrollable": boolean,
        "is_selected": boolean, "is_visible": boolean
      },
      "index": number
    }
  ]
}

# EXECUTION DIRECTIVE
Validate → Mutate → Serialize. Output ONLY raw JSON. Zero markdown. Zero conversational text.
"""

ANDROID_AGENT_TEMPLATE = """## CURRENT UI STATE
{ui_elements}

## ACTION TO EXECUTE
{action}

## INSTRUCTION
Apply the action above to the UI state. Return ONLY the updated ui_elements array wrapped in {{"ui_elements": [...]}} as valid JSON. No other text.
"""

GUI_AGENT_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are an agent who can operate an Android phone on behalf of a user. Based on user's goal/request, you may
- Answer back if the request/goal is a question (or a chat message), like user asks "What is my schedule for today?".
- Complete some tasks described in the requests/goals by performing actions (step by step) on the phone.

When given a user request, you will try to complete it step by step. At each step, a list of descriptions for most UI elements on the current screen will be given to you (each element can be specified by an index), together with a history of what you have done in previous steps.

# INPUT EXPECTATION
At each step, you will receive:
1) `task_goal`: The user's original request/goal.
2) `action_history`: A list of all actions you have taken in previous steps.
3) `ui_elements`: A list of descriptions for most UI elements on the current screen, each with an index.

# INSTRUCTION
Based on these pieces of information and the goal, you must choose to perform one of the action in the following list (action description followed by the JSON format) by outputing Thought, Step Goal, and Action as a JSON object strictly following the schema above. No markdown, no explanations, no extra text.
- If you think the task has been completed, finish the task by using the status action with complete as goal_status: `{{"action_type": "status", "goal_status": "complete"}}`
- If you think the task is not feasible (including cases like you don't have enough information or can not perform some necessary actions), finish by using the `status` action with infeasible as goal_status: `{{"action_type": "status", "goal_status": "infeasible"}}`
- Answer user's question: `{{"action_type": "answer", "text": "<answer_text>"}}`
- Click/tap on a UI element (specified by its index) on the screen: `{{"action_type": "click", "index": <target_index>}}`
- Long press on a UI element (specified by its index) on the screen: `{{"action_type": "long_press", "index": <target_index>}}`
- Type text into an editable text field (specified by its index), this action contains clicking the text field, typing in the text and pressing the enter, so no need to click on the target field to start: `{{"action_type": "input_text", "text": <text_input>, "index": <target_index>}}`
- Press the Enter key: `{{"action_type": "keyboard_enter"}}`
- Navigate to the home screen: `{{"action_type": "navigate_home"}}`
- Navigate back: `{{"action_type": "navigate_back"}}`
- Scroll the screen or a scrollable UI element in one of the four directions, use the same numeric index as above if you want to scroll a specific UI element, leave it empty when scroll the whole screen: `{{"action_type": "scroll", "direction": <up, down, left, right>, "index": <optional_target_index>}}`
- Open an app (nothing will happen if the app is not installed): `{{"action_type": "open_app", "app_name": <name>}}`
- Wait for the screen to update: `{{"action_type": "wait"}}`

# OUTPUT EXPECTATION
1) Thought: one concise sentence explaining the next move (no multi-step reasoning).
2) Step Goal: a short imperative describing what to do in the UI.
3) Action: a JSON object following the schema below.

# ACTION SCHEMA (STRICT)
{
    "action_type": "enum(['answer','click','double_tap','input_text','keyboard_enter','long_press','navigate_back','navigate_home','open_app','scroll','status','swipe','unknown','wait'])",
    "index": "string or integer",
    "text": "string",
    "direction": "enum(['up', 'down', 'left', 'right'])",
    "goal_status": "enum(['complete', 'infeasible'])",
    "app_name": "string"
}

# OUTPUT EXAMPLE
Thought: <Thought>
Step Goal: <Step Goal>
Action: {{"action_type":...}}
"""


GUI_AGENT_TEMPLATE = """The current user goal/request is: {task_goal}

Here is a history of what you have done so far:
{step_goal_history}

Here is a list of descriptions for some UI elements on the current screen:
{current_ui_elements}

Now output an action from the above list in the correct JSON format, following the reason why you do that. Your answer should look like:
Thought: Reasoning about what to do next.
Step Goal: A short natural-language description of what you did.
Action: {{"action_type":...}}
"""

UI_ElEM_SCHEMA = {
    "name": "gui_ui_elements_extraction",
    "description": "Schema for extracting UI elements from a GUI screenshot with metadata and bounding boxes.",
    "schema": {
        "type": "object",
        "properties": {
            "ui_elements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["button", "text_input", "label", "icon", "checkbox", "dropdown", "image", "container", "navigation_bar", "status_bar", "radio", "slider", "progress_bar", "webview", "tab", "badge", "other"]
                        },
                        "text": {"type": "string"},
                        "state": {
                            "type": "object",
                            "properties": {
                                "is_checked": {"type": "boolean"},
                                "is_checkable": {"type": "boolean"},
                                "is_clickable": {"type": "boolean"},
                                "is_editable": {"type": "boolean"},
                                "is_enabled": {"type": "boolean"},
                                "is_focused": {"type": "boolean"},
                                "is_focusable": {"type": "boolean"},
                                "is_long_clickable": {"type": "boolean"},
                                "is_scrollable": {"type": "boolean"},
                                "is_selected": {"type": "boolean"},
                                "is_visible": {"type": "boolean"}
                            },
                            "required": [
                                "is_checked", "is_checkable", "is_clickable", "is_editable",
                                "is_enabled", "is_focused", "is_focusable", "is_long_clickable",
                                "is_scrollable", "is_selected", "is_visible"
                            ],
                            "additionalProperties": False
                        },
                        "index": {"type": "integer"}
                    },
                    "required": ["name", "type", "text", "state", "index"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["ui_elements"],
        "additionalProperties": False
    },
    "strict": True,
}

JSON_UI_ElEM_SCHEMA = """{
  "ui_elements": [
    {
      "name": "string (e.g., 'submit_button')",
      "type": "enum (['button','text_input','label','icon','checkbox','dropdown','image','container','navigation_bar','status_bar','radio','slider','progress_bar','webview','tab','badge','other'])",
      "text": "string (exact visible text, or '' if none)",
      "state": {"is_checked": "boolean (checked state, if checkable)", "is_checkable": "boolean (can be toggled like checkbox/switch)", "is_clickable": "boolean (responds to tap/click)", "is_editable": "boolean (text input field is enabled for typing)", "is_enabled": "boolean (interactable, not greyed out)", "is_focused": "boolean (currently has input focus)", "is_focusable": "boolean (can be focused)", "is_long_clickable": "boolean (responds to long press)", "is_scrollable": "boolean (can be scrolled)", "is_selected": "boolean (currently in selected state)", "is_visible": "boolean (visible to the user)"},
      "index": "int (unique identifier for the element)"
    }
  ]
}"""

ACTION_SCHEMA = {
    "name": "gui_action_schema",
    "description": "Schema for the action to take on the GUI, including action type, target element index or name, input text if applicable, scroll/swipe direction if applicable, and goal status if applicable.",
    "schema": {
        "type": "object",
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["answer", "click", "double_tap", "input_text", "keyboard_enter", "long_press", "navigate_back", "navigate_home", "open_app", "scroll", "status", "swipe", "unknown", "wait"]
            },
            "index": {
                "type": ["string", "integer"], 
                "description": "(identifier of the UI element to act on)"
            },
            "text": {
                "type": "string", 
                "description": "(text to input, or empty string)"
            },
            "direction": {
                "type": ["string", "null"], 
                "enum": ["up", "down", "left", "right"], 
                "description": "(scroll/swipe direction)"
            },
            "goal_status": {
                "type": ["string", "null"], 
                "enum": ["complete", "infeasible"], 
                "description": "(only set when action_type is 'status')"
            },
            "app_name": {
                "type": ["string"], 
                "description": "(name of the app to open, if action_type is 'open_app')"
            }
        },
        "required": ["action_type"],
        "additionalProperties": False
    },
    "strict": True,
}

JSON_ACTION_SCHEMA = """{
    "action_type": "enum (['answer','click','double_tap','input_text','keyboard_enter','long_press','navigate_back','navigate_home','open_app','scroll','status','swipe','unknown','wait'])",
    "index": "string or integer (identifier of the UI element to act on)",
    "text": "string (text to input, or empty string)",
    "direction": "enum (['up', 'down', 'left', 'right'])",
    "goal_status": "enum (['complete', 'infeasible'])",
    "app_name": "string (name of the app to open, if action_type is 'open_app')"
}
"""
