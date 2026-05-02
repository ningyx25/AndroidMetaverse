#!/bin/bash
set -e

export TIONCICO_BASE_URL=http://api.dreamxz.cn:9999/v1
export TIONCICO_API_KEY=sk-DiGei1wc2eE9n75RezrITtXOQqoRFfosh4W7agL1hbLzMq66

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MAX_ROUNDS=${1:-10}
round=0

while [ $round -lt $MAX_ROUNDS ]; do
    round=$((round + 1))
    echo "===== Round $round ====="
    python3 "$SCRIPT_DIR/describe_first_images.py" && break
    echo "Some episodes failed, retrying..."
done

if [ $round -ge $MAX_ROUNDS ]; then
    echo "Reached max rounds ($MAX_ROUNDS), some episodes may still be unprocessed."
    exit 1
fi
