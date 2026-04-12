# ReDSL

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$7.50-yellow) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fopenai%2Fgpt-5-mini-lightgrey)

This project uses AI-generated code. Total cost: **$7.5000** with **65** AI commits.

Generated on 2026-04-12 using [openrouter/openai/gpt-5-mini](https://openrouter.ai/models/openrouter/openai/gpt-5-mini)

---

**Re**factor + **DSL** + **S**elf-**L**earning — Autonomiczny System Refaktoryzacji Kodu

ReDSL to zaawansowany system refaktoryzacji kodu Python, który łączy analizę statyczną, reguły DSL (Domain Specific Language), pamięć agenta i inteligencję LLM do automatycznego poprawiania jakości kodu.

![Version](https://img.shields.io/badge/version-1.2.27-blue) ![Python](https://img.shields.io/badge/python-%3E%3D3.11-blue) ![Tests](https://img.shields.io/badge/tests-571%20passing-green) ![E2E](https://img.shields.io/badge/e2e-18%20tests-green) [![Docs](https://img.shields.io/badge/docs-29%20projektów-green)](./docs/)

---

## Aktualny stan projektu

Na podstawie analizy `code2llm` z 2026-04-09:

- **Pliki**: 114
- **Funkcje**: 781
- **Klasy**: 112
- **Linie kodu**: 19 151
- **Średnia złożoność**: CC̄ = 4.1
- **Hotspoty krytyczne**: 3
- **Duplikacje / cykle**: 0 / 0
- **Największy hotspot**: `redsl/formatters.py` (517 LOC, CC=28)
- **Następny refactor**: rozbić 3 metody o CC > 15:
  - `format_cycle_report_markdown()`
  - `format_batch_report_markdown()`
  - `LLMLayer.call()`

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

Każde uruchomienie `refactor` oraz `batch` zapisuje też raport Markdown obok projektu lub katalogu root:

- `redsl_refactor_plan.md` — wynik `--dry-run`
- `redsl_refactor_report.md` — wykonany cykl refaktoryzacji
- `redsl_batch_semcod_report.md` — raport zbiorczy dla `batch semcod`
- `redsl_batch_hybrid_report.md` — raport zbiorczy dla `batch hybrid`

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

| Katalog | Opis | Link |
|---------|------|------|
| `examples/01-basic-analysis/` | Analiza projektu z plików toon.yaml | [Przejdź](./examples/01-basic-analysis/) |
| `examples/02-custom-rules/` | Definiowanie własnych reguł DSL | [Przejdź](./examples/02-custom-rules/) |
| `examples/03-full-pipeline/` | Pełny cykl: analyze → decide → refactor → reflect | [Przejdź](./examples/03-full-pipeline/) |
| `examples/04-memory-learning/` | System pamięci: episodic, semantic, procedural | [Przejdź](./examples/04-memory-learning/) |
| `examples/05-api-integration/` | Użycie REST API i WebSocket | [Przejdź](./examples/05-api-integration/) |
| `examples/06-awareness/` | Świadomość zmian i adaptacja | [Przejdź](./examples/06-awareness/) |
| `examples/07-pyqual/` | Quality gates i analiza jakości | [Przejdź](./examples/07-pyqual/) |
| `examples/08-audit/` | One-click Audit → ocena A+ do F | [Przejdź](./examples/08-audit/) |
| `examples/09-pr-bot/` | PR Bot z metrykami delta | [Przejdź](./examples/09-pr-bot/) |
| `examples/10-badge/` | Generator badge'i jakości | [Przejdź](./examples/10-badge/) |

### Szybkie uruchomienie przykładu

```bash
# Uruchomienie przykładu przez CLI
redsl example 01-basic-analysis

# Lub bezpośrednio
python examples/01-basic-analysis/main.py
```

## REST API

ReDSL udostępnia REST API (FastAPI) do programatycznego dostępu do wszystkich funkcji:

### Uruchomienie serwera

```bash
# Wbudowany serwer (uvicorn)
redsl server --host 0.0.0.0 --port 8000

# Lub bezpośrednio
python -m redsl.server
```

### Endpointy

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/health` | GET | Health check + wersja + statystyki pamięci |
| `/refactor` | POST | Uruchom refaktoryzację projektu |
| `/analyze` | POST | Analiza projektu — zwraca metryki i alerty |
| `/decide` | POST | Ewaluacja reguł DSL — decyzje bez wykonania |
| `/rules` | POST | Dodaj niestandardowe reguły DSL |
| `/memory/stats` | GET | Statystyki pamięci agenta |
| `/debug/config` | GET | Konfiguracja agenta (z opcjonalnym `?show_env=true`) |
| `/debug/decisions` | GET | Decyzje DSL dla projektu (`?project_path=&limit=`) |
| `/examples` | GET | Lista dostępnych przykładów |
| `/examples/{name}/yaml` | GET | Surowe dane YAML scenariusza |

### Przykłady użycia

```bash
# Health check
curl http://localhost:8000/health

# Analiza projektu
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_dir": "./my-project"}'

# Refaktoryzacja (dry-run)
curl -X POST http://localhost:8000/refactor \
  -H "Content-Type: application/json" \
  -d '{"project_path": "./my-project", "max_actions": 3, "dry_run": true, "format": "yaml"}'

# Dodaj własną regułę DSL
curl -X POST http://localhost:8000/rules \
  -H "Content-Type: application/json" \
  -d '{"rules": [{"name": "my-rule", "condition": {"metric": "cc", "operator": ">", "threshold": 10}, "action": "refactor", "priority": 0.9}]}'
```

Dokumentacja interaktywna (Swagger UI) dostępna pod `http://localhost:8000/docs` po uruchomieniu serwera.

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

## Testy

### Szybki smoke test

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

### Testy automatyczne

```bash
# Wszystkie testy (fast + e2e + integration)
pytest

# Tylko szybkie testy (< 5s każdy)
pytest -m 'not slow'

# Tylko testy e2e (full workflows na realnych projektach)
pytest tests/test_e2e.py -v
```

**Struktura testów:**
- **533 fast tests** — testy jednostkowe i integracyjne (~2 min)
- **18 e2e tests** — pełne przepływy CLI i API na realnych projektach
- **20 integration tests** — integracja z semcod ecosystem (code2llm, regix, pyqual)

**Pokrycie e2e:**
- CLI: `refactor`, `history`, `ecosystem`, `scan`, `batch pyqual-run`
- API: `/health`, `/refactor`, `/analyze`, `/decide`, `/rules`, `/memory/stats`, `/debug/config`, `/debug/decisions`, `/examples`
- Autonomy: quality gate workflow

## Ekosystem Semcod (opcjonalne narzędzia)

ReDSL integruje się z ekosystemem semcod dla wzmocnionej analizy:

| Narzędzie | Bridge | Funkcja |
|-----------|--------|---------|
| `code2llm` | `code2llm_bridge.py` | Generowanie plików toon.yaml z metrykami |
| `regix` | `regix_bridge.py` | Wykrywanie regresji metryk po refaktoryzacji |
| `pyqual` | `pyqual_bridge.py` | Analiza jakości kodu (ruff, mypy, bandit) |
| `planfile` | `planfile_bridge.py` | Tworzenie ticketów dla refactoring tasks |
| `vallm` | `vallm_bridge.py` | Walidacja poprawności kodu przez LLM |
| `redup` | `redup_bridge.py` | Detekcja duplikacji kodu (`redup==0.4.18`) |
| `llx` | `llx_router.py` | Inteligentny routing modeli LLM |

## Konfiguracja

### Plik `.env` (zmienne środowiskowe)

```bash
# Klucz API dla LLM (wymagany dla akcji z LLM)
OPENROUTER_API_KEY (set in your environment)

# Model LLM (domyślnie: openrouter/openai/gpt-5.4-mini)
LLM_MODEL=openrouter/openai/gpt-5.4-mini

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
├── tests/               # 571 testów (533 fast + 18 e2e + 20 integration)
├── examples/            # Przykłady użycia
├── config/              # Domyślna konfiguracja reguł DSL
└── pyproject.toml       # Packaging i zależności
```

## Dokumentacja

Szczegółowa dokumentacja projektów ekosystemu **semcod** dostępna w katalogu [`docs/`](./docs/):

### Narzędzia Core (Pipeline)

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| **ReDSL** | [`docs/README.md`](./docs/README.md) | Autonomiczny system refaktoryzacji (ten projekt) |
| [code2llm](https://github.com/semcod/code2llm) | [`docs/code2llm-analiza-przeplywu-kodu.md`](./docs/code2llm-analiza-przeplywu-kodu.md) | Analiza przepływu kodu, generowanie TOON |
| [code2logic](https://github.com/semcod/code2logic) | [`docs/code2logic-analiza-nlp.md`](./docs/code2logic-analiza-nlp.md) | NLP dla zapytań o kod (polski/angielski) |
| [regix](https://github.com/semcod/regix) | [`docs/regix-indeks-regresji.md`](./docs/regix-indeks-regresji.md) | Wykrywanie regresji metryk między commitami |
| [redup](https://github.com/semcod/redup) | [`docs/redup-detekcja-duplikacji.md`](./docs/redup-detekcja-duplikacji.md) | Detekcja duplikacji na poziomie AST |
| [pyqual](https://github.com/semcod/pyqual) | [`docs/pyqual-quality-gates.md`](./docs/pyqual-quality-gates.md) | Quality gates: ruff + mypy + bandit |
| [vallm](https://github.com/semcod/vallm) | [`docs/vallm-walidacja-kodu-llm.md`](./docs/vallm-walidacja-kodu-llm.md) | Walidacja kodu LLM |

### Automatyzacja i CI/CD

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| [planfile](https://github.com/semcod/planfile) | [`docs/planfile-automatyzacja-sdlc.md`](./docs/planfile-automatyzacja-sdlc.md) | Automatyzacja cyklu SDLC |
| [goal](https://github.com/semcod/goal) | [`docs/goal-automatyczny-git-push.md`](./docs/goal-automatyczny-git-push.md) | Automatyczne commity i release'y |
| [domd](https://github.com/semcod/domd) | [`docs/domd-walidacja-komend-markdown.md`](./docs/domd-walidacja-komend-markdown.md) | Walidacja komend w Markdown |
| [qualbench](https://github.com/semcod/qualbench) | [`docs/qualbench-ci-dla-kodu-ai.md`](./docs/qualbench-ci-dla-kodu-ai.md) | Benchmarki CI dla kodu AI |
| [weekly](https://github.com/semcod/weekly) | [`docs/weekly-analizator-jakosci.md`](./docs/weekly-analizator-jakosci.md) | Analizator jakości projektu |

### Infrastruktura LLM

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| [proxym](https://github.com/semcod/proxym) | [`docs/proxym-proxy-ai.md`](./docs/proxym-proxy-ai.md) | Proxy AI z cache'm semantycznym |
| [llx](https://github.com/semcod/llx) | [`docs/llx-routing-modeli-llm.md`](./docs/llx-routing-modeli-llm.md) | Routing modeli LLM |
| [prellm](https://github.com/semcod/prellm) | [`docs/prellm-preprocessing-llm.md`](./docs/prellm-preprocessing-llm.md) | Preprocessing zapytań LLM |
| [algitex](https://github.com/semcod/algitex) | [`docs/algitex-progresywna-algorytmizacja.md`](./docs/algitex-progresywna-algorytmizacja.md) | Progresywna algorytmizacja |

### Narzędzia Deweloperskie

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| [pfix](https://github.com/semcod/pfix) | [`docs/pfix-self-healing-python.md`](./docs/pfix-self-healing-python.md) | Self-healing Python |
| [prefact](https://github.com/semcod/prefact) | [`docs/prefact-linter-llm-aware.md`](./docs/prefact-linter-llm-aware.md) | Linter świadomy LLM |
| [pactfix](https://github.com/semcod/pactfix) | [`docs/pactfix-bash-analyzer.md`](./docs/pactfix-bash-analyzer.md) | Analizator Bash |
| [clickmd](https://github.com/semcod/clickmd) | [`docs/clickmd-markdown-terminal.md`](./docs/clickmd-markdown-terminal.md) | Markdown w terminalu |
| [toonic](https://github.com/semcod/toonic) | [`docs/toonic-format-toon.md`](./docs/toonic-format-toon.md) | Format TOON |

### Monitoring i Koszty

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| [costs](https://github.com/semcod/costs) | [`docs/cost-kalkulator-kosztow-ai.md`](./docs/cost-kalkulator-kosztow-ai.md) | Kalkulator kosztów AI |
| [nfo](https://github.com/semcod/nfo) | [`docs/nfo-automatyczne-logowanie-funkcji.md`](./docs/nfo-automatyczne-logowanie-funkcji.md) | Auto-logowanie funkcji |
| [metrun](https://github.com/semcod/metrun) | [`docs/metrun-profilowanie-wydajnosci.md`](./docs/metrun-profilowanie-wydajnosci.md) | Profilowanie wydajności |
| [ats-benchmark](https://github.com/semcod/ats-benchmark) | [`docs/ats-benchmark.md`](./docs/ats-benchmark.md) | Benchmarki automatyzacji |

### Ekosystem i Biznes

| Projekt | Dokumentacja | Opis |
|---------|--------------|------|
| [Ekosystem](https://github.com/semcod) | [`docs/ekosystem-semcod-przeglad.md`](./docs/ekosystem-semcod-przeglad.md) | Przegląd ekosystemu (29 narzędzi) |
| [Biznes](https://github.com/semcod) | [`docs/zautomatyzowany-biznes-semcod.md`](./docs/zautomatyzowany-biznes-semcod.md) | Model biznesowy Semcod |
| [code2docs](https://github.com/semcod/code2docs) | [`docs/code2docs-automatyczna-dokumentacja.md`](./docs/code2docs-automatyczna-dokumentacja.md) | Auto-dokumentacja |

### Inne projekty

- [heal](./docs/heal-zdrowie-wellness.md) — Wellness z LLM

---

## License

Licensed under Apache-2.0.
