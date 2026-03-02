#!/bin/bash
set -e

# Start Ollama server in the background
ollama serve &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for Ollama server to start..."
for i in $(seq 1 60); do
    if ollama list > /dev/null 2>&1; then
        echo "Ollama server is ready."
        break
    fi
    sleep 1
done

# Pull models specified in OLLAMA_MODELS env var (comma-separated)
if [ -n "$OLLAMA_MODELS" ]; then
    IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"
    for model in "${MODELS[@]}"; do
        model=$(echo "$model" | xargs)  # trim whitespace
        echo "Pulling model: $model"
        ollama pull "$model" || echo "Warning: Failed to pull $model"
    done
fi

# Wait for the server process
wait $SERVER_PID
