#!/usr/bin/env python3
"""
ReDSL — Przykład 07: PyQual — analiza jakości kodu

Pokazuje jak:
1. Załadować pliki źródłowe z YAML
2. Uruchomić analizę AST (bez zewnętrznych narzędzi)
3. Wyświetlić znalezione problemy i rekomendacje

Uruchomienie:
    python main.py
    python main.py --scenario advanced
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.pyqual_example import main as run_pyqual_example


def main():
    run_pyqual_example(sys.argv[1:])


if __name__ == "__main__":
    main()
