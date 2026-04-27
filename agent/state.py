from enum import Enum
from typing_extensions import TypedDict


class UIElementType(str, Enum):
    BUTTON = "button"
    TEXT_INPUT = "text_input"
    LABEL = "label"
    ICON = "icon"
    CHECKBOX = "checkbox"
    DROPDOWN = "dropdown"
    IMAGE = "image"
    CONTAINER = "container"
    NAVIGATION_BAR = "navigation_bar"
    STATUS_BAR = "status_bar"
    RADIO = "radio"
    SLIDER = "slider"
    PROGRESS_BAR = "progress_bar"
    WEBVIEW = "webview"
    TAB = "tab"
    BADGE = "badge"
    OTHER = "other"


class UIElementDesc(TypedDict):
    color: str
    style: str


class UIElementPos(TypedDict):
    x_min: int
    x_max: int
    y_min: int
    y_max: int


class UIElementState(TypedDict):
    is_checked: bool
    is_checkable: bool
    is_clickable: bool
    is_editable: bool
    is_enabled: bool
    is_focused: bool
    is_focusable: bool
    is_long_clickable: bool
    is_scrollable: bool
    is_selected: bool
    is_visible: bool


class UIElement(TypedDict):
    name: str
    type: UIElementType
    text: str
    state: UIElementState
    index: int


class UIElementNode(TypedDict):
    ui_elements: list[UIElement]
    parent: "UIElementNode"
    children: dict[str, "UIElementNode"]  # action -> child node


class UIElementTree(TypedDict):
    root: UIElementNode


class ActionType(str, Enum):
    ANSWER = 'answer'
    CLICK = 'click'
    DOUBLE_TAP = 'double_tap'
    INPUT_TEXT = 'input_text'
    KEYBOARD_ENTER = 'keyboard_enter'
    LONG_PRESS = 'long_press'
    NAVIGATE_BACK = 'navigate_back'
    NAVIGATE_HOME = 'navigate_home'
    OPEN_APP = 'open_app'
    SCROLL = 'scroll'
    STATUS = 'status'
    SWIPE = 'swipe'
    UNKNOWN = 'unknown'
    WAIT = 'wait'


class Direction(str, Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class GoalStatus(str, Enum):
    COMPLETE = 'complete'
    INFEASIBLE = 'infeasible'


class Action(TypedDict):
    action_type: ActionType
    index: str | int
    text: str
    direction: Direction
    goal_status: GoalStatus
    app_name: str


class AndroidState(TypedDict):
    ui_elements: UIElementNode  # 维持一个最新的ui_elements
    last_action: Action

    action_history: list[Action]  # 记录历史action
    ui_elements_history: UIElementTree  # 记录历史ui_elements


class GUIState(TypedDict):
    task_goal: str  # 任务目标
    thought_history: list[str]
    step_goal_history: list[str]
    action_history: list[Action]  # 执行动作历史

    ui_elements: UIElementNode  # 当前画面
    last_action: Action


class SuiteState(TypedDict):
    task_id: int
    task_type: str
    task_goal: str

    ui_elements: UIElementNode  # 当前画面
    last_action: Action

    thought_history: list[str]
    step_goal_history: list[str]
    action_history: list[Action]  # 执行动作历史
    ui_elements_history: UIElementTree

    is_successful: bool


if __name__ == "__main__":
    root: UIElementNode = {"ui_elements": [], "parent": None, "children": {}}
    child: UIElementNode = {"ui_elements": [], "parent": root, "children": {}}
    root["children"]["click_button"] = child

    tree: UIElementTree = {"root": root}

    assert tree["root"] is root
    assert root["children"]["click_button"] is child
    assert child["parent"] is root
    print("OK: root -[click_button]-> child")
