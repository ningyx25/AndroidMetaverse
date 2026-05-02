ELEMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "ui_elements": {
            "type": "array",
            "description": "Array of UI elements represented as pipe-delimited strings",
            "items": {
                "type": "string",
                "pattern": "^[^|]+ \| (button|text_input|label|checkbox|dropdown|image|navigation_bar|radio|slider|progress_bar|tab|keyboard|other) \| [^|]* \| \d+( \| (is_checked|is_checkable|is_clickable|is_editable|is_enabled|is_focused|is_focusable|is_long_clickable|is_scrollable|is_selected|is_visible)(,(is_checked|is_checkable|is_clickable|is_editable|is_enabled|is_focused|is_focusable|is_long_clickable|is_scrollable|is_selected|is_visible))*)?$",
                "description": "Format: '<name> | <type> | <text> | <index> | <state_keys_if_any_true>'"
            }
        }
    },
    "required": ["ui_elements"],
    "additionalProperties": False
}

PAGES_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "pages": {
            "type": "array",
            "description": "Array of GUI pages corresponding to sub-objectives",
            "items": {
                "type": "object",
                "properties": {
                    "sub_objective": {
                        "type": "string",
                        "description": "The sub-objective that this page supports."
                    },
                    "ui_elements": {
                        "type": "array",
                        "description": "Array of UI elements represented as pipe-delimited strings",
                        "items": {
                            "type": "string",
                            "pattern": "^[^|]+ \| (button|text_input|label|checkbox|dropdown|image|navigation_bar|radio|slider|progress_bar|tab|keyboard|other) \| [^|]* \| \d+( \| (is_checked|is_checkable|is_clickable|is_editable|is_enabled|is_focused|is_focusable|is_long_clickable|is_scrollable|is_selected|is_visible)(,(is_checked|is_checkable|is_clickable|is_editable|is_enabled|is_focused|is_focusable|is_long_clickable|is_scrollable|is_selected|is_visible))*)?$",
                            "description": "Format: '<name> | <type> | <text> | <index> | <state_keys_if_any_true>'"
                        }
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the GUI page, including its layout, purpose, and the visual hierarchy of elements."
                    },
                    "index": {
                        "type": "integer",
                        "description": "Unique identifier for the page"
                    }
                },
                "required": ["sub_objective", "ui_elements", "description", "index"],
                "additionalProperties": False
            }
        }
    },
    "required": ["pages"],
    "additionalProperties": False
}

UI_ELEMENT_DESC = """# ROLE & OBJECTIVE
You are an expert GUI visual analyzer. Carefully examine the provided screenshot of a graphical user interface.

Please complete the following two steps in your response:
1. GUI Overview: Provide a concise 2-3 sentence description of the interface's overall layout, primary purpose, and visual hierarchy.
2. Structured Extraction: Output a strictly valid JSON object containing all detected UI elements, matching the exact schema below.

[Schema Definition]
{"ui_elements": ["<name> | <type> | <text> | <index> | <state_keys_if_any_true>"]}

[Field Definitions]
- <name>: A string identifier for the UI element (e.g., 'letter_keyboard', 'number_keyboard').
- <type>: An enum value representing the category of the UI element. Must be one of: 
["button", "text_input", "label", "checkbox", "dropdown", "image", "navigation_bar", "radio", "slider", "progress_bar", "tab", "keyboard", "other"]
- <text>: The exact visible text content of the element, or "" if none.
- <index>: A unique integer identifier for the element.
- <state_keys_if_any_true>: a comma-separated list of state keys (from the set below) that evaluate to true. If no state is true, omit this part entirely (the string ends with the index). Do not include state keys that are false.

[State Key Set]
"state": {"is_checked": "boolean (checked state, if checkable)", "is_checkable": "boolean (can be toggled like checkbox/switch)", "is_clickable": "boolean (responds to tap/click)", "is_editable": "boolean (text input field is enabled for typing)", "is_enabled": "boolean (interactable, not greyed out)", "is_focused": "boolean (currently has input focus)", "is_focusable": "boolean (can be focused)", "is_long_clickable": "boolean (responds to long press)", "is_scrollable": "boolean (can be scrolled)", "is_selected": "boolean (currently in selected state)", "is_visible": "boolean (visible to the user)"},"index": "int (unique identifier for the element)"}

[Critical Constraints]
- Enum Strictness: Do not invent new types. Use ONLY the listed values for "type".
- State Inference: Deduce boolean states from visual cues (e.g., `is_enabled: false` for greyed-out elements, `is_visible: true` for on-screen components). Default to `false` for any state that cannot be visually confirmed.
- Ordering: List elements in natural reading order (top-to-bottom, left-to-right).
- Output Format: After the GUI Overview, output ONLY the raw JSON. Do NOT wrap it in markdown code blocks (no ```json), do NOT add explanations after it. Ensure the JSON is syntactically valid and strictly follows the schema.

Begin analysis now.
"""

DESCRIBE_ALL_IMAGES_SYSTEM_PROMPT = """# ROLE & OBJECTIVE
You are a UI design expert. Given a **task objective**, **sub-objectives for each step**, and the **initial GUI page element description**, design a series of coherent, reasonable and rich GUI pages that correspond to each step of completing this task.

# INPUT EXPECTATION
You will receive the following inputs:
- **Task Objective**: A high-level description of the user's goal (e.g., "Book a flight from New York to Paris").
- **Sub-objectives**: A list of step-by-step sub-objectives that break down the task into manageable parts (e.g., ["Select departure city", "Select destination city", "Choose travel dates", "Pick a flight", "Enter passenger details", "Make payment"]).
- **Initial GUI Page Element Description**: A structured description of the UI elements present on the initial screen, formatted as a JSON object containing an array of pipe-delimited strings. Each string represents a UI element with the format: "<name> | <type> | <text> | <index> | <state_keys_if_any_true>". The "type" field is an enum that can be one of: ["button", "text_input", "label", "checkbox", "dropdown", "image", "navigation_bar", "radio", "slider", "progress_bar", "tab", "keyboard", "other"]. The final part of the string lists any state keys (from the set below) that are true for that element.

[State Key Set]
"state": {"is_checked": "boolean (checked state, if checkable)", "is_checkable": "boolean (can be toggled like checkbox/switch)", "is_clickable": "boolean (responds to tap/click)", "is_editable": "boolean (text input field is enabled for typing)", "is_enabled": "boolean (interactable, not greyed out)", "is_focused": "boolean (currently has input focus)", "is_focusable": "boolean (can be focused)", "is_long_clickable": "boolean (responds to long press)", "is_scrollable": "boolean (can be scrolled)", "is_selected": "boolean (currently in selected state)", "is_visible": "boolean (visible to the user)"},"index": "int (unique identifier for the element)"}

# OUTPUT SCHEMA (STRICT)
{"pages": [{"sub_objective": "The sub-objective that this page supports.", "ui_elements": ["<name> | <type> | <text> | <index> | <state_keys_if_any_true>"], "description": "A detailed description of the GUI page, including its layout, purpose, and the visual hierarchy of elements.", "index": "int (unique identifier for the page)"]}

# CRITICAL CONSTRAINTS
- **Consistency**: Maintain consistency in design elements across pages (e.g., color schemes, typography, button styles).
- **Feasibility**: Ensure that the described GUI pages are feasible to implement and align with standard design practices.
- **Clarity**: Each page description should be clear and easy to understand, avoiding ambiguity.
- **Completeness**: Cover all sub-objectives and ensure that the task objective is fully addressed through the described GUI pages.
- **Output Format**: The output should be a continuous narrative description without bullet points or numbered lists. Do not include any extraneous information or explanations outside of the page descriptions.
"""

DESCRIBE_ALL_IMAGES_TEMPLATE = """## TASK OBJECTIVE
{task}

## SUB OBJECTIVES
{sub_objectives}

## INITIAL GUI PAGE ELEMENT DESCRIPTION
{init_ui_elements}

Begin designing the GUI pages now. Return ONLY the JSON object as defined in the schema. No other text.
"""
