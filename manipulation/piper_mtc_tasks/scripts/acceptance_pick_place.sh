#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ROOT_DIR="${VENOM_WS:-$(cd "$REPO_DIR/../.." && pwd)}"
SETUP_SCRIPT="$ROOT_DIR/install/setup.bash"
LOG_DIR="/tmp/piper_mtc_acceptance"
RUNS="${1:-5}"

mkdir -p "$LOG_DIR"

successes=0
failures=0

for run in $(seq 1 "$RUNS"); do
  run_dir="$LOG_DIR/run_$run"
  mkdir -p "$run_dir"
  launch_log="$run_dir/launch.log"
  action_log="$run_dir/action.log"

  echo "=== Run $run/$RUNS ==="

  bash -lc "source '$SETUP_SCRIPT' && ros2 launch piper_mtc_tasks sim_pick_task.launch.py use_gazebo_gui:=false" \
    >"$launch_log" 2>&1 &
  launch_pid=$!

  cleanup() {
    if kill -0 "$launch_pid" 2>/dev/null; then
      kill -INT "$launch_pid" 2>/dev/null || true
      wait "$launch_pid" 2>/dev/null || true
    fi
  }

  ready=0
  for _ in $(seq 1 90); do
    if bash -lc "source '$SETUP_SCRIPT' && ros2 action list" 2>/dev/null | grep -q '^/manipulation/execute_task$'; then
      ready=1
      break
    fi
    sleep 1
  done

  if [[ "$ready" -ne 1 ]]; then
    echo "Run $run: action server did not become ready"
    cleanup
    failures=$((failures + 1))
    continue
  fi

  set +e
  timeout 180 bash -lc \
    "source '$SETUP_SCRIPT' && ros2 action send_goal /manipulation/execute_task venom_manipulation_interfaces/action/ExecuteTask '{task_type: 1}' --feedback" \
    >"$action_log" 2>&1
  action_status=$?
  set -e

  if grep -q "Goal finished with status: SUCCEEDED" "$action_log" && \
     grep -q "success: true" "$action_log"; then
    echo "Run $run: SUCCESS"
    successes=$((successes + 1))
  else
    echo "Run $run: FAILURE"
    failures=$((failures + 1))
  fi

  cleanup
  sleep 3
done

echo
echo "Acceptance summary: successes=$successes failures=$failures total=$RUNS"
echo "Logs: $LOG_DIR"

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi
