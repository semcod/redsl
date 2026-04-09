#!/usr/bin/env python3
"""
ReDSL — Przykład 10: Badge Generator

Generator badge'ów jakości kodu A+ do F
z kodem Markdown/HTML do osadzenia.

Uruchomienie:
    python main.py
    python main.py --scenario advanced
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.badge import main as run_badge_example


def main():
    run_badge_example(sys.argv[1:])


if __name__ == "__main__":
    main()
