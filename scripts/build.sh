#!/bin/bash
set -e
npm install
npx tailwindcss -i ./app/static/css/input.css -o ./app/static/css/output.css --minify
uv sync
echo "Build complete"