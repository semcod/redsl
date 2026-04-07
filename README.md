# Conscious Refactor Agent

## AI Cost Tracking

![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.15-brightgreen) ![AI Model](https://img.shields.io/badge/AI%20Model-openrouter%2Fqwen%2Fqwen3-coder-next-lightgrey)

This project uses AI-generated code. Total cost: **$0.1500** with **1** AI commits.

Generated on 2026-04-07 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/models/openrouter/qwen/qwen3-coder-next)

---



Autonomiczny system refaktoryzacji kodu oparty na LLM z pamięcią, refleksją i standaryzowanym językiem DSL do podejmowania decyzji.

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
│                  LLM LAYER (LiteLLM)                │
│   ─ code generation  ─ reflection  ─ self-critique  │
├─────────────────────────────────────────────────────┤
│                 MEMORY SYSTEM                       │
│   ─ episodic (historia refaktoryzacji)              │
│   ─ semantic (wzorce, reguły)                       │
│   ─ procedural (strategie, plany)                   │
└─────────────────────────────────────────────────────┘
```

## Pętla Świadomości (Consciousness Loop)

```
1. PERCEIVE  → analiza kodu (toon.yaml, linters, metryki)
2. DECIDE    → DSL engine wybiera strategię refaktoryzacji
3. PLAN      → LLM generuje plan zmian
4. EXECUTE   → generowanie patchy + walidacja
5. REFLECT   → LLM ocenia własne zmiany (self-critique)
6. REMEMBER  → zapis doświadczenia do pamięci
7. IMPROVE   → korekta na podstawie refleksji
```

## Uruchomienie

```bash
# Docker
docker-compose up --build

# Lokalnie
pip install -r requirements.txt
python -m app.main analyze --project /path/to/project
python -m app.main refactor --project /path/to/project --auto
```

## DSL – Język Decyzji Refaktoryzacji

```yaml
rules:
  - name: split_high_cc
    when:
      cyclomatic_complexity: {gt: 15}
      function_lines: {gt: 50}
    then:
      action: extract_functions
      priority: 0.9
    
  - name: deduplicate_blocks
    when:
      duplicate_similarity: {gte: 0.95}
      duplicate_lines: {gt: 10}
    then:
      action: deduplicate
      priority: 0.8

  - name: split_god_module
    when:
      module_lines: {gt: 400}
      function_count: {gt: 15}
    then:
      action: split_module
      priority: 0.95
```


## License

Licensed under Apache-2.0.
