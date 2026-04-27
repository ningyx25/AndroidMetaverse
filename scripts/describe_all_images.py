import argparse
import asyncio
import json
import os
import sys
from openai import AsyncOpenAI
from prompt import DESCRIBE_ALL_IMAGES_SYSTEM_PROMPT, DESCRIBE_ALL_IMAGES_TEMPLATE

MAX_CONCURRENCY = 1

save_lock = asyncio.Lock()


async def call_model_stream(client: AsyncOpenAI, model: str, prompt: str) -> str:
    stream = await client.chat.completions.create(
        model=model,
        stream=True,
        messages=[
            {"role": "system", "content": DESCRIBE_ALL_IMAGES_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    chunks = []
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            chunks.append(delta)
    return "".join(chunks)


async def process_sample(sem: asyncio.Semaphore, client: AsyncOpenAI, model: str, idx: int, sample: dict) -> tuple:
    async with sem:
        prompt = DESCRIBE_ALL_IMAGES_TEMPLATE.format(
            task=sample["task_objective"],
            sub_objectives=sample["sub_objectives"],
            init_ui_elements=sample["init_ui_elements"],
        )
        try:
            description = await call_model_stream(client, model, prompt)
        except Exception as e:
            description = None
            print(f"[ERROR] [{idx}] {sample.get('id', idx)}: {e}", file=sys.stderr)
        return idx, description


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    client = AsyncOpenAI(
        api_key=os.environ.get("MODELSCOPE_API_KEY"),
        base_url=os.environ.get("MODELSCOPE_BASE_URL"),
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(base_dir, args.input), "r", encoding="utf-8") as f:
        data = json.load(f)

    output_path = os.path.join(base_dir, args.output)
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

        print(f"[{idx+1}/{len(data)}] {sample.get('id', idx)}")
        print("-" * 60)
        print(description)
        print()

        results[idx] = {**sample, "description": description}
        async with save_lock:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    done = sum(1 for r in results if r is not None)
    print(f"Done. {done}/{len(data)} samples processed. Output: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
