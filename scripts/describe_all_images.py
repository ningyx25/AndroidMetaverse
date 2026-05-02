import argparse
import asyncio
import json
import os
import sys
from openai import AsyncOpenAI
from prompt import (
    PAGES_JSON_SCHEMA, 
    DESCRIBE_ALL_IMAGES_SYSTEM_PROMPT, 
    DESCRIBE_ALL_IMAGES_TEMPLATE
)

MAX_CONCURRENCY = 5

save_lock = asyncio.Lock()


async def process_sample(sem: asyncio.Semaphore, client: AsyncOpenAI, model: str, idx: int, sample: dict) -> tuple:
    async with sem:
        prompt = DESCRIBE_ALL_IMAGES_TEMPLATE.format(
            task=sample["task_objective"],
            sub_objectives=sample["sub_objectives"],
            init_ui_elements=sample["init_ui_elements"],
        )
        try:
            print(f"[{idx+1}] {sample.get('id', idx)}")
            print("-" * 60)
            stream = await client.chat.completions.create(
                model=model,
                stream=True,
                messages=[
                    {"role": "system", "content": DESCRIBE_ALL_IMAGES_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=98304,  # 131072
                temperature=0.2,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "pages_response",
                        "schema": PAGES_JSON_SCHEMA
                    }
                }
            )
            text = ""
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta_obj = chunk.choices[0].delta
                reasoning = getattr(delta_obj, "reasoning_content", None) or ""
                content = delta_obj.content or ""
                if content:
                    print(content, end="", flush=True)
                    text += content
            print()
            desc = text
            desc = desc.strip()
            if desc.startswith("```"):
                desc = desc.split("```")[1]
                if desc.startswith("json"):
                    desc = desc[4:].strip()
            description = json.loads(desc)
        except Exception as e:
            description = None
            print(f"[ERROR] [{idx}] {sample.get('id', idx)}: {e}", file=sys.stderr)
        return idx, description


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="kimi-k2.5")
    parser.add_argument("--input", default="/fs1/private/user/ningyongxin/workplace/proj/AndroidMetaverse/data/metadata_with_desc_pure_v3.json")
    parser.add_argument("--output", default="/fs1/private/user/ningyongxin/workplace/proj/AndroidMetaverse/data/metadata_with_all_desc_pure_kimi2_5.json")
    args = parser.parse_args()

    # from dotenv import load_dotenv
    # load_dotenv()
    client = AsyncOpenAI(
        # api_key=os.getenv("QIANFAN_API_KEY"),
        # base_url=os.getenv("QIANFAN_BASE_URL"),
        api_key=os.environ.get("QIANFAN_API_KEY"),
        base_url=os.environ.get("QIANFAN_BASE_URL", "https://qianfan.baidubce.com/v2/coding"),
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = list(data.values())

    output_path = args.output
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            results = json.load(f)
        print(f"Loaded {len(results)} existing results, resuming...")
    else:
        results = [None] * len(data)

    pending = [
        i for i, r in enumerate(results)
        if r is None or (isinstance(r, dict) and r.get("description") is None)
    ]
    print(f"Total: {len(data)}, Pending: {len(pending)}\n")

    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    tasks = [process_sample(sem, client, args.model, i, data[i]) for i in pending]

    for coro in asyncio.as_completed(tasks):
        idx, description = await coro
        sample = data[idx]

        print(f"[{idx+1}/{len(data)}] done")

        results[idx] = {**sample, "description": description}
        async with save_lock:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    remaining = sum(1 for r in results if r is None or (isinstance(r, dict) and r.get("description") is None))
    print(f"Done. {len(data) - remaining}/{len(data)} samples processed. Output: {args.output}")
    sys.exit(1 if remaining > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
