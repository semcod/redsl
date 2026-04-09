#!/usr/bin/env python3
"""
ReDSL — Przykład 05: Integracja przez REST API

Pokazuje jak korzystać z ReDSL jako mikroserwisu:
1. Analiza projektu (POST /analyze)
2. Decyzje DSL (POST /decide)
3. Refaktoryzacja (POST /refactor)
4. Dodawanie reguł (POST /rules)
5. Statystyki pamięci (GET /memory/stats)

Uruchomienie serwera:
    cd redsl/
    uvicorn app.api:app --port 8000

Uruchomienie klienta:
    python main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from redsl.examples.api_integration import main as run_api_integration_example


def main():
    run_api_integration_example(sys.argv[1:])


if __name__ == "__main__":
    main()
