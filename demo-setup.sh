#!/usr/bin/env bash
# Setup for demo.tape — meant to be *sourced* (not executed) so the exports
# persist in the recording shell. This keeps every long command out of the
# recording: the tape only ever types `source demo-setup.sh`.
export PATH="$PWD/.venv/bin:$PATH"
export AGENTBENCH_DATA_DIR="/tmp/ab-demo-lb"
rm -rf "$AGENTBENCH_DATA_DIR"
for f in claude-haiku-4-5 gemini-2.5-flash; do
  agentbench leaderboard submit \
    --results "benchmarks/v0.1.0/${f}.json" \
    --name "$f" --author agentbench --model "$f" >/dev/null 2>&1
done
