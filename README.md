# ReDSL

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$4.50-green) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fopenai%2Fgpt-5-mini-lightgrey)

This project uses AI-generated code. Total cost: **$4.5000** with **30** AI commits.

Generated on 2026-04-08 using [openrouter/openai/gpt-5-mini](https://openrouter.ai/models/openrouter/openai/gpt-5-mini)

---



**Re**factor + **DSL** + **S**elf-**L**earning — Autonomiczny System Refaktoryzacji Kodu

ReDSL to zaawansowany system refaktoryzacji kodu Python, który łączy analizę statyczną, reguły DSL (Domain Specific Language), pamięć agenta i inteligencję LLM do automatycznego poprawiania jakości kodu.

![Version](https://img.shields.io/badge/version-1.2.14-blue) ![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![Tests](https://img.shields.io/badge/tests-329%20passing-green)

---

## Kluczowe Funkcje

- 🔍 **Analiza statyczna** - Integracja z code2llm, toon.yaml, linterami (ruff, mypy, bandit)
- 🧠 **LLM z refleksją** - Generowanie propozycji refaktoryzacji z pętlą samorefleksji
- ⚡ **Hybrydowy silnik** - Bezpośrednie refaktoryzacje (bez LLM) dla prostych zmian
- 📊 **DSL Engine** - Definicja reguł refaktoryzacji w czytelnym formacie YAML
- 💾 **System pamięci** - Trzy warstwy: epizodyczna, semantyczna, proceduralna
- 🛡️ **Walidacja regresji** - Automatyczne wykrywanie degradacji metryk przez regix
- 🚀 **Skalowalność** - Przetwarzanie wielu projektów (semcod) jednocześnie
- 🐳 **Sandbox** - Bezpieczne testowanie refaktoryzacji w Docker

## Instalacja

```bash
# Z PyPI (gdy dostępne)
pip install redsl

# Ze źródeł
git clone https://github.com/wronai/redsl
cd redsl
pip install -e .
```

### Wymagania

- Python >= 3.11
- Opcjonalnie: Docker (dla sandbox testing)
- Opcjonalnie: Narzędzia semcod ecosystem (code2llm, regix, pyqual, planfile)

## Szybki start

### Podstawowe użycie CLI

```bash
# Refaktoryzacja pojedynczego projektu (dry-run)
redsl refactor ./my-project --max-actions 5 --dry-run

# Refaktoryzacja z walidacją regresji
redsl refactor ./my-project --max-actions 10 --validate-regix --rollback

# Refaktoryzacja z sandbox testing (Docker)
redsl refactor ./my-project --max-actions 5 --sandbox

# Analiza jakości kodu bez refaktoryzacji
redsl pyqual analyze ./my-project --format yaml

# Automatyczne naprawy jakościowe (bez LLM)
redsl pyqual fix ./my-project
```

### Przetwarzanie wsadowe (semcod ecosystem)

```bash
# Hybrydowa refaktoryzacja (bez LLM) - szybka
redsl batch hybrid /path/to/semcod --max-changes 50

# Pełna refaktoryzacja z LLM i refleksją
redsl batch semcod /path/to/semcod --max-actions 10

# Z wykrywaniem regresji metryk przez regix
redsl batch semcod /path/to/semcod --max-actions 5 --validate-regix
```

### Debugowanie i diagnostyka

```bash
# Sprawdź konfigurację i zmienne środowiskowe
redsl debug config --show-env

# Zobacz decyzje DSL dla projektu
redsl debug decisions ./my-project --limit 20

# Profiluj wydajność cyklu refaktoryzacji
redsl perf ./my-project

# Szacuj koszt LLM przed uruchomieniem
redsl cost ./my-project --max-actions 10
```

## Przykłady

| Katalog | Opis |
|---------|------|
| `examples/01-basic-analysis/` | Analiza projektu z plików toon.yaml |
| `examples/02-custom-rules/` | Definiowanie własnych reguł DSL |
| `examples/03-full-pipeline/` | Pełny cykl: analyze → decide → refactor → reflect |
| `examples/04-memory-learning/` | System pamięci: episodic, semantic, procedural |
| `examples/05-api-integration/` | Użycie REST API i WebSocket |

## Architektura

```
┌─────────────────────────────────────────────────────────────────┐
│                     REFACTOR ORCHESTRATOR                       │
│         PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT            │
│                    ↓                    ↓                       │
│              REMEMBER → IMPROVE (auto-learning)                 │
├─────────────────┬───────────────────┬───────────────────────────┤
│    ANALYZER     │    DSL ENGINE     │     REFACTOR ENGINES      │
│  ─ toon.yaml    │  ─ rule scoring   │  ┌─────────────────────┐  │
│  ─ code2llm     │  ─ decisions      │  │ DirectRefactorEngine│  │
│  ─ linters      │  ─ auto-learning  │  │ (bez LLM)           │  │
│  ─ redup        │                   │  ├─────────────────────┤  │
│                 │                   │  │ LLM RefactorEngine  │  │
│                 │                   │  │ (z refleksją)       │  │
│                 │                   │  └─────────────────────┘  │
├─────────────────┴───────────────────┴───────────────────────────┤
│                     VALIDATION LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ regix       │  │ vallm       │  │ sandbox (Docker)        │  │
│  │ (regression)│  │ (pactfix)   │  │ (bezpieczne testowanie) │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     ECOSYSTEM BRIDGES                           │
│  code2llm │ regix │ pyqual │ planfile │ vallm │ redup │ llx     │
├─────────────────────────────────────────────────────────────────┤
│                     LLM LAYER (LiteLLM)                         │
│  ─ model routing (llx_router)  ─ cost estimation  ─ reflection  │
├─────────────────────────────────────────────────────────────────┤
│                     MEMORY SYSTEM                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐      │
│  │ episodic    │  │ semantic    │  │ procedural          │      │
│  │ (historia)  │  │ (wzorce)    │  │ (strategie)         │      │
│  └─────────────┘  └─────────────┘  └─────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Dostępne akcje refaktoryzacji

### Proste akcje (bez LLM)
- `REMOVE_UNUSED_IMPORTS` - Usuwanie nieużywanych importów
- `FIX_MODULE_EXECUTION_BLOCK` - Poprawa bloków wykonania modułu
- `EXTRACT_CONSTANTS` - Ekstrakcja magic numbers do stałych
- `ADD_RETURN_TYPES` - Dodawanie adnotacji typów zwracanych

> **Uwaga implementacyjna:** deterministyczne helpery AST znajdują się teraz w `redsl/refactors/ast_transformers.py`, a `redsl.refactors` oraz `redsl.refactors.direct` re-exportują je dla zachowania kompatybilności.

### Złożone akcje (z LLM)
- `EXTRACT_FUNCTIONS` - Ekstrakcja funkcji o wysokiej złożoności
- `SPLIT_MODULE` - Podział dużych modułów
- `REDUCE_COMPLEXITY` - Redukcja złożoności cyklomatycznej
- `SIMPLIFY_CONDITIONALS` - Upraszczanie warunków
- `DEDUPLICATE` - Usuwanie duplikacji kodu

## Smoke test na świeżym projekcie

Jeśli chcesz szybko sprawdzić, czy ReDSL uruchamia się poprawnie w nowym projekcie, użyj minimalnego projektu z jednym plikiem:

```bash
mkdir -p /tmp/redsl-smoke
cat > /tmp/redsl-smoke/main.py <<'PY'
import os


def main() -> None:
    return None


main()
PY

python3 -m redsl analyze /tmp/redsl-smoke
python3 -m redsl refactor /tmp/redsl-smoke --dry-run --max-actions 5
```

## Ekosystem Semcod (opcjonalne narzędzia)

ReDSL integruje się z ekosystemem semcod dla wzmocnionej analizy:

| Narzędzie | Bridge | Funkcja |
|-----------|--------|---------|
| `code2llm` | `code2llm_bridge.py` | Generowanie plików toon.yaml z metrykami |
| `regix` | `regix_bridge.py` | Wykrywanie regresji metryk po refaktoryzacji |
| `pyqual` | `pyqual_bridge.py` | Analiza jakości kodu (ruff, mypy, bandit) |
| `planfile` | `planfile_bridge.py` | Tworzenie ticketów dla refactoring tasks |
| `vallm` | `vallm_bridge.py` | Walidacja poprawności kodu przez LLM |
| `redup` | `redup_bridge.py` | Detekcja duplikacji kodu |
| `llx` | `llx_router.py` | Inteligentny routing modeli LLM |

## Konfiguracja

### Plik `.env` (zmienne środowiskowe)

```bash
# Klucz API dla LLM (wymagany dla akcji z LLM)
OPENROUTER_API_KEY (set in your environment)

# Model LLM (domyślnie: openrouter/openai/gpt-4o-mini)
LLM_MODEL=openrouter/openai/gpt-4o-mini

# Zachowanie refaktoryzacji
REFACTOR_DRY_RUN=false
REFACTOR_AUTO_APPROVE=false
REFACTOR_MAX_REFLECTION_ROUNDS=1

# Pamięć agenta
MEMORY_PERSIST_DIR=.redsl_memory

# Lokalne modele (Ollama) - wymagają ollama serve
OLLAMA_HOST=http://localhost:11434

# Timeout dla narzędzi zewnętrznych
REDSL_REGIX_TIMEOUT=300
```

### Plik `redsl.yaml` (reguły DSL)

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

# Reguły refaktoryzacji
rules:
  - name: high_complexity
    condition: cyclomatic_complexity > 15
    action: EXTRACT_FUNCTIONS
    priority: 0.9
  
  - name: unused_imports
    condition: unused_import_count > 5
    action: REMOVE_UNUSED_IMPORTS
    priority: 0.8

# Wykluczenia z analizy
exclude:
  - .venv/
  - venv/
  - node_modules/
  - .git/
  - tests/
```

## Opcje CLI

```bash
redsl refactor --help

Options:
  -n, --max-actions INTEGER      Maksymalna liczba akcji
  --dry-run                      Pokaż plan bez aplikowania zmian
  -f, --format [text|yaml|json]  Format wyjścia
  --use-code2llm                 Użyj code2llm do percepcji
  --validate-regix               Walidacja regresji po wykonaniu
  --rollback                     Auto-rollback przy regresji
  --sandbox                      Testuj w Docker sandbox
```

## Struktura projektu

```
redsl/
├── redsl/
│   ├── analyzers/       # Analiza kodu, metryki, code2llm/redup bridge
│   ├── commands/        # Komendy CLI: batch, pyqual, planfile bridge
│   ├── dsl/             # Silnik reguł DSL i scoring
│   ├── llm/             # Warstwa LLM (LiteLLM) + llx router
│   ├── memory/          # System pamięci (3 warstwy)
│   ├── refactors/       # Silniki: Direct + LLM + body_restorer
│   ├── validation/      # regix, vallm, test_runner, sandbox
│   ├── diagnostics/     # Profilowanie: perf_bridge (metrun)
│   ├── orchestrator.py  # Główny koordynator pipeline
│   ├── cli.py           # Punkt wejścia CLI
│   └── config.py        # AgentConfig, LLMConfig
├── tests/               # 329 testów jednostkowych
├── examples/            # Przykłady użycia
├── config/              # Domyślna konfiguracja reguł DSL
└── pyproject.toml       # Packaging i zależności
```

## License

Licensed under Apache-2.0.
