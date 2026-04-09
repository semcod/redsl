#!/usr/bin/env python3
"""
ReDSL — Przykład 01: Podstawowa analiza projektu

Pokazuje jak:
1. Wczytać metryki z plików toon.yaml
2. Przepuścić je przez DSL Engine
3. Zobaczyć decyzje refaktoryzacji

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.basic_analysis import main as run_basic_analysis_example


def main():
    run_basic_analysis_example(sys.argv[1:])


if __name__ == "__main__":
    main()
