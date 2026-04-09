#!/usr/bin/env python3
"""
ReDSL — Przykład 02: Własne reguły DSL

Pokazuje jak:
1. Definiować reguły DSL programowo (Python)
2. Ładować reguły z YAML
3. Łączyć z domyślnymi regułami
4. Ewaluować na dowolnych metrykach

Uruchomienie:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.custom_rules import main as run_custom_rules_example


def main():
    run_custom_rules_example(sys.argv[1:])


if __name__ == "__main__":
    main()
