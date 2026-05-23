#!/bin/sh
set -eu

NODE_APP_DIR="${NODE_APP_DIR:-/workspace/node-app}"
NODE_PORT="${NODE_PORT:-3000}"
NODE_START_COMMAND="${NODE_START_COMMAND:-npm start}"

if [ -f "$NODE_APP_DIR/package.json" ]; then
    echo "Starting Node service from $NODE_APP_DIR on port $NODE_PORT..."
    (
        cd "$NODE_APP_DIR"
        if [ ! -d node_modules ]; then
            npm install
        fi
        export PORT="$NODE_PORT"
        sh -lc "$NODE_START_COMMAND"
    ) &
    NODE_PID="$!"
else
    echo "No Node app found at $NODE_APP_DIR/package.json; skipping Node service startup."
    NODE_PID=""
fi

jupyter lab \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --ServerApp.root_dir=/workspace \
    --ServerApp.token="${JUPYTER_TOKEN:-bioanalysis}" &
JUPYTER_PID="$!"

stop_services() {
    if [ -n "$NODE_PID" ]; then
        kill "$NODE_PID" 2>/dev/null || true
    fi
    kill "$JUPYTER_PID" 2>/dev/null || true
}

trap stop_services INT TERM
wait "$JUPYTER_PID"
