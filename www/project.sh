#!/usr/bin/env bash
set -e
clear

VENV="venv"
PIP="$VENV/bin/pip"

if [ ! -f "$PIP" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
elif ! head -1 "$PIP" | grep -q "$(pwd)"; then
    echo "Virtual environment has broken paths (moved from another location). Recreating..."
    rm -rf "$VENV"
    python3 -m venv "$VENV"
fi

#$PIP install -e . --quiet
#$PIP install regix --upgrade --quiet
#$PIP install pyqual --upgrade --quiet
#$PIP install prefact --upgrade --quiet
#$PIP install vallm --upgrade --quiet
#$PIP install redup==0.4.18 --upgrade --quiet
#$PIP install glon --upgrade --quiet
#$PIP install goal --upgrade --quiet
#$PIP install code2logic --upgrade --quiet
$PIP install code2llm --upgrade --quiet
#$PIP install --force-reinstall -e . --quiet  # Re-apply editable install after PyPI upgrades
$VENV/bin/code2llm ./ -f all -o ./project --no-chunk
$PIP install code2docs --upgrade --quiet
$VENV/bin/code2docs ./ --readme-only
#$VENV/bin/redup scan . --format toon --output ./project
#$VENV/bin/vallm batch . --recursive --format toon --output ./project
#$VENV/bin/prefact -a -e "examples/**"
$PIP install sumd --upgrade --quiet
sumd .
sumr .
