#!/usr/bin/env python3
"""
ReDSL — Przykład 04: System pamięci i uczenia

Pokazuje 3 warstwy pamięci:
1. EPISODIC  — „co zrobiłem" (historia akcji)
2. SEMANTIC  — „co wiem" (wzorce, lekcje)
3. PROCEDURAL — „jak to robić" (strategie)

Agent uczy się z doświadczeń i wykorzystuje wiedzę
w kolejnych cyklach refaktoryzacji.

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.memory_learning import main as run_memory_learning_example


def main():
    run_memory_learning_example(sys.argv[1:])


if __name__ == "__main__":
    main()
