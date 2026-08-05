#!/bin/sh
set -e

echo "=== [Startup] Ensuring required backend data and log directories exist ==="
mkdir -p data/raw data/extracted data/processed data/chunks data/embeddings data/faiss data/metadata data/evaluation logs

export FLASK_APP=run.py
PORT="${PORT:-5000}"

echo "=== [Startup] Environment: FLASK_APP=${FLASK_APP}, PORT=${PORT} ==="

echo "=== [Startup] Checking Database Migration Configuration ==="
if [ -d "migrations" ]; then
    echo "=== [Startup] Executing Database Migrations via Flask-Migrate ==="
    if flask db upgrade; then
        echo "=== [Startup] Flask-Migrate DB upgrade completed successfully ==="
    elif [ -f "alembic.ini" ]; then
        echo "=== [Startup] Flask CLI migration failed, falling back to Alembic ==="
        alembic upgrade head || echo "=== [Startup Warning] Alembic migration returned non-zero status ==="
    else
        echo "=== [Startup Warning] Database migration skipped or database connection unavailable ==="
    fi
elif [ -f "alembic.ini" ]; then
    echo "=== [Startup] Executing Database Migrations via Alembic ==="
    alembic upgrade head || echo "=== [Startup Warning] Alembic migration skipped or completed ==="
else
    echo "=== [Startup Info] No migrations directory or alembic.ini found. Skipping database migration ==="
fi

echo "=== [Startup] Verification: Testing FAISS and NumPy imports ==="
python -c "import numpy; import faiss; print(f'NumPy version: {numpy.__version__}, FAISS loaded successfully')" || echo "=== [Warning] FAISS import verification check failed ==="

echo "=== [Startup] Launching production Gunicorn server on 0.0.0.0:${PORT} ==="
exec gunicorn --bind "0.0.0.0:${PORT}" "run:app" --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile -
