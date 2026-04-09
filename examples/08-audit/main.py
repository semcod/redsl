#!/usr/bin/env python3
"""
ReDSL — Przykład 08: One-click Audit

Pełny flow: Connect GitHub → skan → raport z grade circle,
metrykami, rekomendacjami i badge.

Uruchomienie:
    python main.py
    python main.py --scenario advanced
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.audit import main as run_audit_example


def main():
    run_audit_example(sys.argv[1:])


if __name__ == "__main__":
    main()
