#!/bin/bash
set -e

export QIANFAN_BASE_URL=https://qianfan.baidubce.com/v2/coding
export QIANFAN_API_KEY=bce-v3/ALTAKSP-noRub5b3WmCkAunt8MaUR/bcacf3431491be645b914c8a6f0a16b2c1faa3d2

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_ROUNDS=10
round=0

while [ $round -lt $MAX_ROUNDS ]; do
    round=$((round + 1))
    echo "===== Round $round ====="
    python3 "$SCRIPT_DIR/describe_all_images.py" "$@" && break
    echo "Some samples failed, retrying..."
done

if [ $round -ge $MAX_ROUNDS ]; then
    echo "Reached max rounds ($MAX_ROUNDS), some samples may still be unprocessed."
    exit 1
fi
