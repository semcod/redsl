# ReDSL

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$3.15-green) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fopenai%2Fgpt-5-mini-lightgrey)

This project uses AI-generated code. Total cost: **$3.1500** with **21** AI commits.

Generated on 2026-04-07 using [openrouter/openai/gpt-5-mini](https://openrouter.ai/models/openrouter/openai/gpt-5-mini)

---



**Re**factor + **DSL** + **S**elf-**L**earning — autonomiczna refaktoryzacja kodu z LLM, pamięcią i DSL.

ReDSL to system refaktoryzacji kodu, który łączy analizę statyczną, reguły DSL i inteligencję LLM do automatycznego poprawiania jakości kodu Python.

## Funkcje

- 🔍 **Analiza statyczna** - Integracja z popularnymi linterami i narzędziami metryk
- 🧠 **LLM z refleksją** - Generowanie propozycji refaktoryzacji z pętlą samorefleksji
- ⚡ **Hybrydowy silnik** - Bezpośrednie refaktoryzacje dla prostych zmian, LLM dla złożonych
- 📊 **DSL Engine** - Definicja reguł refaktoryzacji w czytelnym formacie YAML
- 💾 **System pamięci** - Uczenie się z historii refaktoryzacji
- 🚀 **Skalowalność** - Przetwarzanie wielu projektów jednocześnie

## Instalacja

```bash
pip install -e .
```

## Szybki start

### Podstawowe użycie CLI

```bash
# Refaktoryzacja pojedynczego projektu
redsl refactor ./my-project --max-actions 5 --dry-run

# Refaktoryzacja bez trybu testowego
redsl refactor ./my-project --max-actions 10
```

### Przetwarzanie wsadowe

```bash
# Przetwarzanie projektów semcod z LLM
redsl batch semcod /path/to/semcod --max-actions 10

# Hybrydowa refaktoryzacja (bez LLM) dla projektów semcod
redsl batch hybrid /path/to/semcod --max-changes 30
```

### Debugowanie

```bash
# Sprawdź konfigurację
redsl debug config --show-env

# Zobacz decyzje DSL dla projektu
redsl debug decisions ./my-project --limit 20
```

## Przykłady

| Katalog | Opis |
|---------|------|
| `examples/01-basic-analysis/` | Analiza projektu z plików toon.yaml |
| `examples/02-custom-rules/` | Definiowanie własnych reguł DSL |
| `examples/03-full-pipeline/` | Pełny cykl: analyze → decide → refactor → reflect |
| `examples/04-memory-learning/` | System pamięci: episodic, semantic, procedural |

## Architektura

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR                       │
│   (pętla: analyze → decide → refactor → reflect)    │
├─────────────┬──────────────┬────────────────────────┤
│  ANALYZER   │  DSL ENGINE  │   REFACTOR ENGINE      │
│  ─ toon.yaml│  ─ rules     │   ─ patch generation   │
│  ─ linters  │  ─ scoring   │   ─ validation         │
│  ─ metrics  │  ─ planning  │   ─ application        │
├─────────────┴──────────────┴────────────────────────┤
│            HYBRID REFACTOR ENGINES                  │
│  ─ DirectRefactorEngine (bez LLM)                   │
│  ─ LLM RefactorEngine (z refleksją)                 │
├─────────────────────────────────────────────────────┤
│                  LLM LAYER (LiteLLM)                │
│   ─ code generation  ─ reflection  ─ self-critique  │
├─────────────────────────────────────────────────────┤
│                 MEMORY SYSTEM                       │
│   ─ episodic (historia refaktoryzacji)              │
│   ─ semantic (wzorce, reguły)                       │
│   ─ procedural (strategie, plany)                   │
└─────────────────────────────────────────────────────┘
```

## Dostępne akcje refaktoryzacji

### Proste akcje (bez LLM)
- `REMOVE_UNUSED_IMPORTS` - Usuwanie nieużywanych importów
- `FIX_MODULE_EXECUTION_BLOCK` - Poprawa bloków wykonania modułu
- `EXTRACT_CONSTANTS` - Ekstrakcja magic numbers do stałych
- `ADD_RETURN_TYPES` - Dodawanie adnotacji typów zwracanych

### Złożone akcje (z LLM)
- `EXTRACT_FUNCTIONS` - Ekstrakcja funkcji o wysokiej złożoności
- `SPLIT_MODULE` - Podział dużych modułów
- `REDUCE_COMPLEXITY` - Redukcja złożoności cyklomatycznej
- `SIMPLIFY_CONDITIONALS` - Upraszczanie warunków
- `DEDUPLICATE` - Usuwanie duplikacji kodu

## Konfiguracja

Utwórz plik `.env` w katalogu projektu:

```bash
# Klucz API (wymagany dla LLM)
OPENROUTER_API_KEY=

# Model LLM (opcjonalny)
LLM_MODEL=openrouter/openai/gpt-4o-mini

# Zachowanie refaktoryzacji
REFACTOR_DRY_RUN=true
REFACTOR_AUTO_APPROVE=false
```

## Opcje CLI

```bash
python3 hybrid_llm_refactor.py --help

Options:
  --max-changes N    Maksymalna liczba zmian na projekt (domyślnie: 50)
  --no-llm          Wyłącz LLM (tylko proste refaktoryzacje)
  --no-validation   Wyłącz walidację zmian LLM
```

## Struktura projektu

```
redsl/
├── app/
│   ├── analyzers/      # Analiza kodu i metryki
│   ├── dsl/           # Silnik reguł DSL
│   ├── llm/           # Warstwa LLM z LiteLLM
│   ├── memory/        # System pamięci
│   ├── refactors/     # Silniki refaktoryzacji
│   └── orchestrator.py # Główny koordynator
├── examples/          # Przykłady użycia
├── tests/            # Testy jednostkowe
├── hybrid_llm_refactor.py  # Główny skrypt hybrydowy
└── config/           # Konfiguracja domyślna
```

## License

Licensed under Apache-2.0.
