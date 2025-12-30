#!/bin/bash
set -e

# Check if node_modules exists and if package.json is newer
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo "📦 Installing/updating npm dependencies..."
    npm install
else
    echo "✓ Dependencies are up to date"
fi

# Execute the command passed to the entrypoint
exec "$@"
