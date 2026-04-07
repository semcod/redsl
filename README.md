# ReDSL

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$1.65-green) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

This project uses AI-generated code. Total cost: **$1.6500** with **11** AI commits.

Generated on 2026-04-07 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/models/openrouter/qwen/qwen3-coder-next)

---



**Re**factor + **DSL** + **S**elf-**L**earning — autonomiczna refaktoryzacja kodu z LLM, pamięcią i DSL.

![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.45-brightgreen) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

```bash
pip install redsl
```

## Szybki start

```bash
redsl analyze  --project ./my-project           # Analiza metryk
redsl explain  --project ./my-project           # Wyjaśnij decyzje
redsl refactor --project ./my-project           # Dry-run
redsl refactor --project ./my-project --live    # Aplikuj zmiany
```

## Docker

```bash
docker-compose up --build                        # API na :8000
docker-compose --profile autonomous up           # Agent autonomiczny
```

## DSL — język decyzji

```yaml
rules:
  - name: split_high_cc
    when:
      cyclomatic_complexity: {gt: 15}
    then:
      action: extract_functions
      priority: 0.85
```

## Przykłady

| Katalog | Opis |
|---------|------|
| `examples/01-basic-analysis/` | Analiza projektu z plików toon.yaml |
| `examples/02-custom-rules/` | Definiowanie własnych reguł DSL |
| `examples/03-full-pipeline/` | Pełny cykl: analyze → decide → refactor → reflect |
| `examples/04-memory-learning/` | System pamięci: episodic, semantic, procedural |
| `examples/05-api-integration/` | REST API + curl/httpx examples |

## Architektura

```
PERCEIVE → DECIDE → PLAN → EXECUTE → REFLECT → REMEMBER
   ↑                                              │
   └──────────── continuous learning ──────────────┘
```

## Szczegóły techniczne

### Warstwy systemu

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
│                  LLM LAYER (LiteLLM)                │
│   ─ code generation  ─ reflection  ─ self-critique  │
├─────────────────────────────────────────────────────┤
│                 MEMORY SYSTEM                       │
│   ─ episodic (historia refaktoryzacji)              │
│   ─ semantic (wzorce, reguły)                       │
│   ─ procedural (strategie, plany)                   │
└─────────────────────────────────────────────────────┘
```

### Pętla Świadomości (Consciousness Loop)

```
1. PERCEIVE  → analiza kodu (toon.yaml, linters, metryki)
2. DECIDE    → DSL engine wybiera strategię refaktoryzacji
3. PLAN      → LLM generuje plan zmian
4. EXECUTE   → generowanie patchy + walidacja
5. REFLECT   → LLM ocenia własne zmiany (self-critique)
6. REMEMBER  → zapis doświadczenia do pamięci
7. IMPROVE   → korekta na podstawie refleksji
```

## Konfiguracja

Zmienne środowiskowe:
- `OPENAI_API_KEY` lub `OPENROUTER_API_KEY` — klucz API
- `REFACTOR_LLM_MODEL` — model LLM (np. `openrouter/openai/gpt-4o-mini`)
- `REFACTOR_DRY_RUN` — tryb testowy (`true`/`false`)

## License

Licensed under Apache-2.0.
