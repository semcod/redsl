#!/usr/bin/env python3
"""
ReDSL — Przykład 03: Pełny pipeline refaktoryzacji

Pokazuje kompletny cykl:
    PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER

⚠️  Wymaga OPENAI_API_KEY (lub innego providera LLM)

Uruchomienie:
    Set OPENAI_API_KEY in your environment before running
    python main.py

    # Z lokalnym modelem (Ollama):
    python main.py --model ollama/llama3
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.full_pipeline import main as run_full_pipeline_example


def main():
    run_full_pipeline_example(sys.argv[1:])


if __name__ == "__main__":
    main()
