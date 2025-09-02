#!/bin/bash
cd /home/ernest/projects/project1-energy-analysis || exit

# Run pipeline
uv run src/pipeline.py

# Stage changes
git add data/processed/*

# Only commit & push if there are changes
if ! git diff --cached --quiet; then
    git commit -m "Daily data update: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
else
    echo "No changes to commit."
fi
