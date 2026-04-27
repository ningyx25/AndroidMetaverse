import asyncio
import json
import base64
import os
import sys
from collections import defaultdict
from openai import AsyncOpenAI
from prompt import UI_ELEMENT_DESC, ELEMENT_JSON_SCHEMA

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


def ui_to_natural_language(ui_str: str) -> str:
    parts = [p.strip() for p in ui_str.split("|")]
    name, ui_type, text = parts[0], parts[1], parts[2]
    states = [s.strip() for s in parts[4].split(",")] if len(parts) > 4 and parts[4].strip() else []
    type_en = TYPE_EN.get(ui_type, "element")
    text_part = f" displaying \"{text}\"" if text else ""
    state_part = ", ".join(STATE_EN[s] for s in states if s in STATE_EN and s != "is_visible")
    desc = f"A {type_en}{text_part} ({name})"
    if state_part:
        desc += f", currently {state_part}"
    return desc + "."


def build_init_ui_elements(first_image_description: str, sub_objective: str = "") -> str | None:
    if not first_image_description:
        return None
    try:
        parsed = json.loads(first_image_description)
        elements = parsed.get("ui_elements", [])
        if not elements:
            return None
        page = {"sub_objective": sub_objective, "ui_elements": elements, "description": "", "index": 1}
        return json.dumps({"pages": [page]}, ensure_ascii=False)
    except Exception:
        return None


def build_nld(first_image_description: str) -> str | None:
    if not first_image_description:
        return None
    try:
        parsed = json.loads(first_image_description)
        elements = parsed.get("ui_elements", [])
        descs = [ui_to_natural_language(e) for e in elements]
        if not descs:
            return None
        numbered = "; ".join(f"{i+1}. {d}" for i, d in enumerate(descs))
        return f"- **UI Elements**: {numbered}"
    except Exception:
        return None


BASE_URL = "http://api.dreamxz.cn:9999/v1"
API_KEY = os.environ.get("TIONCICO_API_KEY", "your_api_key_here")
MODEL = "qwen3.6-plus"
INPUT_FILE = "../data/metadata_with_prompt_pure.json"
OUTPUT_FILE = "../data/metadata_with_desc_pure.json"
MAX_CONCURRENCY = 1

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
save_lock = asyncio.Lock()


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def describe_image_stream(image_path: str) -> str:
    b64 = encode_image(image_path)
    ext = os.path.splitext(image_path)[-1].lstrip(".").lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    stream = await client.chat.completions.create(
        model=MODEL,
        stream=True,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": UI_ELEM_DESC},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        temperature=0.0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ui_elements_response",  # 必须有 name
                "schema": JSON_SCHEMA            # schema 放在这里
            }
        }
    )

    chunks = []
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            delta = chunk.choices[0].delta.content
            print(delta, end="", flush=True)
            chunks.append(delta)
    print()
    return "".join(chunks)


async def process_episode(sem: asyncio.Semaphore, episode_id: str, steps: list, base_dir: str) -> tuple:
    async with sem:
        first_image = steps[0]["image"]
        image_path = os.path.join(base_dir, first_image)
        try:
            description = await describe_image_stream(image_path)
        except Exception as e:
            description = None
            print(f"[ERROR] episode {episode_id} {first_image}: {e}", file=sys.stderr)
        return episode_id, description


async def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(base_dir, INPUT_FILE), "r", encoding="utf-8") as f:
        data = json.load(f)

    # 按 episode_id 分组，保持原始顺序
    groups = defaultdict(list)
    for item in data:
        groups[item["episode_id"]].append(item)

    output_path = os.path.join(base_dir, OUTPUT_FILE)
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"Loaded {len(results)} existing results, resuming...")
    else:
        results = {}

    # Migrate old format (list) to new format (dict with steps)
    for ep_id, val in list(results.items()):
        if isinstance(val, list):
            desc = val[0].get("first_image_description")
            steps = [{k: v for k, v in s.items() if k not in ("first_image_description", "first_image_nld")} for s in val]
            results[ep_id] = {"first_image_description": desc, "first_image_nld": None, "steps": steps}

    # Force regenerate first_image_nld / episode-level fields for all episodes that have first_image_description
    nld_filled = 0
    for ep_id, val in results.items():
        if val.get("first_image_description"):
            results[ep_id]["first_image_nld"] = build_nld(val["first_image_description"])
            ep_steps = groups.get(ep_id, [])
            ep_first_sub = ep_steps[0].get("step_instruction", "") if ep_steps else ""
            results[ep_id]["init_ui_elements"] = build_init_ui_elements(val["first_image_description"], ep_first_sub)
            nld_filled += 1
        ep_steps = groups.get(ep_id, [])
        if ep_steps:
            results[ep_id]["task_objective"] = ep_steps[0].get("goal_info", "")
            results[ep_id]["sub_objectives"] = "; ".join(
                f"Step {i+1}: {s['step_instruction']}" for i, s in enumerate(ep_steps)
            )
    if nld_filled:
        print(f"Filled first_image_nld for {nld_filled} existing episodes.")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    pending = [
        ep_id for ep_id in groups
        if ep_id not in results or results[ep_id].get("first_image_description") is None
    ]
    print(f"Total episodes: {len(groups)}, Pending: {len(pending)}\n")

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [process_episode(sem, ep_id, groups[ep_id], base_dir) for ep_id in pending]

    for coro in asyncio.as_completed(tasks):
        episode_id, description = await coro
        steps = groups[episode_id]

        print(f"episode {episode_id} -> {steps[0]['image']}")
        print("-" * 60)

        nld = build_nld(description)
        init_ui = build_init_ui_elements(description, steps[0].get("step_instruction", ""))
        task_objective = steps[0].get("goal_info", "")
        sub_objectives = "; ".join(f"Step {i+1}: {s['step_instruction']}" for i, s in enumerate(steps))
        clean_steps = [{k: v for k, v in s.items() if k not in ("first_image_description", "first_image_nld")} for s in steps]
        results[episode_id] = {
            "first_image_description": description,
            "first_image_nld": nld,
            "init_ui_elements": init_ui,
            "task_objective": task_objective,
            "sub_objectives": sub_objectives,
            "steps": clean_steps,
        }

        async with save_lock:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Done. {len(results)}/{len(groups)} episodes processed. Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
