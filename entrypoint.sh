#!/bin/bash

set -e

# Export data dir to environment
export LOCALAPPDATA=/data
export APPDATA=/data

# Create data dirs
mkdir -p /data/Stampa_SaaS

# Mode selection
MODE=${1:-gui}

case $MODE in
  gui)
    echo "→ Launching GUI mode..."
    python /app/main.py
    ;;
  cli)
    echo "→ Launching CLI mode..."
    python /app/setup_app.py
    ;;
  db)
    echo "→ Syncing database..."
    python /app/create_db_from_csv.py
    ;;
  cleanup)
    echo "→ Running cleanup..."
    python /app/cleanup.py
    ;;
  shell)
    echo "→ Bash shell..."
    /bin/bash
    ;;
  test)
    echo "→ Running tests..."
    python /app/test_db_sync.py
    ;;
  *)
    echo "Usage: $0 {gui|cli|db|cleanup|shell|test}"
    echo "  gui      - Launch GUI (default)"
    echo "  cli      - Run setup wizard"
    echo "  db       - Sync CSV to SQLite"
    echo "  cleanup  - Cleanup temp files"
    echo "  shell    - Interactive bash"
    echo "  test     - Run tests"
    exit 1
    ;;
esac
