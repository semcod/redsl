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

import json

# ──────────────────────────────────────────────────────────
# Klient API — przykłady requestów
# ──────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"


def example_curl_commands():
    """Wydrukuj przykładowe komendy curl."""

    print("=" * 60)
    print("  ReDSL API — przykłady curl")
    print("=" * 60)

    # Health check
    print("""
  # 1. Health check
  curl -s {base}/health | python -m json.tool
""".format(base=BASE_URL))

    # Analiza z toon.yaml
    print("""
  # 2. Analiza projektu (z contentem toon.yaml)
  curl -s -X POST {base}/analyze \\
    -H "Content-Type: application/json" \\
    -d '{{
      "project_dir": ".",
      "project_toon": "ALERTS[1]:\\n  !!! cc_exceeded  process_order = 25 (limit:15)\\nMODULES[1]:\\n  M[service.py] 200L C:0 F:5 CC↑25 D:0 (python)"
    }}' | python -m json.tool
""".format(base=BASE_URL))

    # Refaktoryzacja
    print("""
  # 3. Refaktoryzacja (dry-run)
  curl -s -X POST {base}/refactor \\
    -H "Content-Type: application/json" \\
    -d '{{
      "project_dir": "/path/to/project",
      "max_actions": 3,
      "dry_run": true,
      "project_toon": "ALERTS[1]:\\n  !!! cc_exceeded  func = 30 (limit:15)\\nMODULES[1]:\\n  M[app.py] 400L C:0 F:12 CC↑30 D:0 (python)",
      "source_files": {{
        "app.py": "def func():\\n    pass"
      }}
    }}' | python -m json.tool
""".format(base=BASE_URL))

    # Dodaj reguły
    print("""
  # 4. Dodaj niestandardowe reguły DSL
  curl -s -X POST {base}/rules \\
    -H "Content-Type: application/json" \\
    -d '{{
      "rules": [
        {{
          "name": "team_max_lines",
          "when": {{"module_lines": {{"gt": 300}}}},
          "then": {{"action": "split_module", "priority": 0.85}}
        }}
      ]
    }}' | python -m json.tool
""".format(base=BASE_URL))

    # Pamięć
    print("""
  # 5. Statystyki pamięci
  curl -s {base}/memory/stats | python -m json.tool
""".format(base=BASE_URL))


def example_python_client():
    """Przykład klienta Python z httpx."""

    print("\n" + "=" * 60)
    print("  ReDSL API — klient Python (httpx)")
    print("=" * 60)

    code = '''
import httpx

BASE = "http://localhost:8000"

# Analiza
resp = httpx.post(f"{BASE}/analyze", json={
    "project_dir": ".",
    "project_toon": """
ALERTS[2]:
  !!! cc_exceeded      process_order = 25 (limit:15)
  !!  high_fan_out     process_order = 10 (limit:10)

MODULES[1]:
  M[service.py] 200L C:0 F:5 CC↑25 D:0 (python)
""",
})
analysis = resp.json()
print(f"Pliki: {analysis['total_files']}")
print(f"Alerty: {len(analysis['alerts'])}")

# Refaktoryzacja
resp = httpx.post(f"{BASE}/refactor", json={
    "project_dir": ".",
    "max_actions": 2,
    "dry_run": True,
    "project_toon": "...",
    "source_files": {"service.py": "def process_order(): ..."},
})
result = resp.json()
print(f"Decyzje: {result['decisions_count']}")
print(f"Propozycje: {result['proposals_generated']}")

# Dodaj reguły zespołowe
httpx.post(f"{BASE}/rules", json={
    "rules": [
        {
            "name": "strict_cc",
            "when": {"cyclomatic_complexity": {"gt": 10}},
            "then": {"action": "extract_functions", "priority": 0.90},
        }
    ]
})
'''
    print(code)


def example_websocket():
    """Przykład klienta WebSocket."""

    print("\n" + "=" * 60)
    print("  ReDSL API — WebSocket (real-time)")
    print("=" * 60)

    code = '''
import asyncio
import websockets
import json

async def realtime_refactor():
    async with websockets.connect("ws://localhost:8000/ws/refactor") as ws:
        # Wyślij request
        await ws.send(json.dumps({
            "project_dir": "/path/to/project",
            "max_actions": 3,
        }))

        # Odbieraj status w czasie rzeczywistym
        while True:
            msg = json.loads(await ws.recv())
            print(f"[{msg['phase']}] {msg.get('status', msg.get('summary', ''))}")

            if msg["phase"] == "complete":
                print(f"Zastosowano: {msg['applied']} zmian")
                break

asyncio.run(realtime_refactor())
'''
    print(code)


def main():
    example_curl_commands()
    example_python_client()
    example_websocket()

    print("\n" + "=" * 60)
    print("  Uruchom serwer:")
    print("    uvicorn app.api:app --port 8000")
    print("  Potem użyj powyższych komend.")
    print("=" * 60)


if __name__ == "__main__":
    main()
