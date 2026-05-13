#!/bin/bash
# run.sh - Script to install dependencies and start the Banking Transactions API

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing dependencies..."
cd "$PROJECT_ROOT"
npm install

echo "Starting Banking Transactions API..."
npm start

