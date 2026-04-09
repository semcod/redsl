#!/usr/bin/env python3
"""
ReDSL — Przykład 06: Awareness — wykrywanie wzorców zmian

Pokazuje jak:
1. Zbudować timeline z metryk projektu
2. Wykryć wzorce zmian (degradacja / poprawa)
3. Przeszukać wzorce po sygnałach

Uruchomienie:
    python main.py
    python main.py --scenario advanced
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.awareness import main as run_awareness_example


def main():
    run_awareness_example(sys.argv[1:])


if __name__ == "__main__":
    main()
