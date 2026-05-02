import json

with open("data/metadata_with_all_desc_pure.json") as f:
    data = json.load(f)


VALID_TYPES = {
    "button", "text_input", "label", "icon", "checkbox", "dropdown", "image",
    "container", "navigation_bar", "status_bar", "radio", "slider",
    "progress_bar", "webview", "tab", "badge", "other"
}

VALID_STATES = {
    "is_checked", "is_checkable", "is_clickable", "is_editable", "is_enabled",
    "is_focused", "is_focusable", "is_long_clickable", "is_scrollable",
    "is_selected", "is_visible"
}


def parse_element(raw):
    """Parse a pipe-delimited UI element string into a structured dict.
    Format: <name> | <type> | <text> | <index> | <state_keys_if_any_true>
    """
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 4:
        raise ValueError(f"Invalid element format: {raw!r}")

    name, type_, text, index_str = parts[0], parts[1], parts[2], parts[3]

    if type_ not in VALID_TYPES:
        raise ValueError(f"Invalid type {type_!r} in: {raw!r}")

    index = int(index_str)

    states = set(parts[4].split(",")) if len(parts) >= 5 and parts[4] else set()
    if invalid := states - VALID_STATES:
        raise ValueError(f"Invalid states {invalid} in: {raw!r}")

    return {"name": name, "type": type_, "text": text, "index": index, "states": states, "raw": raw}


def parse_elements(ui_elements):
    """Build a dict keyed by '<name>|<index>' to avoid collisions on blank-text elements."""
    result = {}
    for raw in ui_elements:
        elem = parse_element(raw)
        key = f"{elem['name']}|{elem['index']}"
        result[key] = elem
    return result


def diff_pages(page_before, page_after):
    p1 = parse_elements(page_before["ui_elements"])
    p2 = parse_elements(page_after["ui_elements"])
    k1, k2 = set(p1), set(p2)

    added   = {k: p2[k] for k in k2 - k1}
    removed = {k: p1[k] for k in k1 - k2}
    changed = {
        k: {"before": p1[k], "after": p2[k]}
        for k in k1 & k2
        if p1[k]["raw"] != p2[k]["raw"]
    }
    return added, removed, changed


TYPE_EN = {
    "button": "button", "text_input": "text input", "label": "label", "icon": "icon",
    "checkbox": "checkbox", "dropdown": "dropdown", "image": "image", "container": "container",
    "navigation_bar": "navigation bar", "status_bar": "status bar", "radio": "radio button",
    "slider": "slider", "progress_bar": "progress bar", "webview": "web view",
    "tab": "tab", "badge": "badge", "other": "element"
}

STATE_EN = {
    "is_checked": "checked", "is_checkable": "checkable", "is_clickable": "clickable",
    "is_editable": "editable", "is_enabled": "enabled", "is_focused": "focused",
    "is_focusable": "focusable", "is_long_clickable": "long-clickable",
    "is_scrollable": "scrollable", "is_selected": "selected", "is_visible": "visible"
}


def fmt(elem):
    type_en = TYPE_EN.get(elem["type"], "element")
    text_part = f' displaying "{elem["text"]}"' if elem["text"] else ""
    state_part = ", ".join(STATE_EN[s] for s in elem["states"] if s in STATE_EN and s != "is_visible")
    desc = f"A {type_en}{text_part} ({elem['name']})"
    if state_part:
        desc += f", currently {state_part}"
    return desc + "."


PROMPT_TEMPLATE = (
    "The given image is a GUI page on a mobile device.\n"
    "Please delete the following UI elements to the given GUI page: {reduced_elements}\n"
    "Please add the following UI elements to the given GUI page: {added_elements}"
)


def build_prompt(added, removed):
    added_elements   = ";".join(f"{i+1}.{fmt(v)}" for i, v in enumerate(sorted(added.values(),   key=lambda e: e["index"])))
    reduced_elements = ";".join(f"{i+1}.{fmt(v)}" for i, v in enumerate(sorted(removed.values(), key=lambda e: e["index"])))
    return PROMPT_TEMPLATE.format(added_elements=added_elements or "none",
                                  reduced_elements=reduced_elements or "none")


pages = data[0]["description"]["pages"]
added, removed, changed = diff_pages(pages[0], pages[1])
print(build_prompt(added, removed))
