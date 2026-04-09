#!/usr/bin/env python3
"""
ReDSL — Przykład 09: PR Bot Preview

Realistyczny podgląd komentarza bota w stylu GitHub —
metryki delta, flagi ryzyka, sugestie kodu.

Uruchomienie:
    python main.py
    python main.py --scenario advanced
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.pr_bot import main as run_pr_bot_example


def main():
    run_pr_bot_example(sys.argv[1:])


if __name__ == "__main__":
    main()
