---
title: "preLLM — Preprocessing małym LLM przed wykonaniem dużym modelem"
slug: prellm-preprocessing-llm
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - LLM
tags:
  - llm
  - prompt-engineering
  - prompt-decomposition
  - small-llm
  - optimization
excerpt: "preLLM to jedna funkcja do preprocessingu zapytań małym, tanim modelem LLM zanim zostaną wykonane przez duży, drogi model — dekompozycja promptów, klasyfikacja i wzbogacanie kontekstu."
featured_image: ""
status: publish
path: /home/tom/github/semcod/prellm
---

## Czym jest preLLM?

preLLM implementuje wzorzec small-then-large: zapytanie najpierw trafia do małego, taniego modelu (np. Qwen 3B przez Ollama), który je klasyfikuje, dekompozuje na podzadania i wzbogaca kontekstem — a dopiero potem przetworzone zapytanie trafia do dużego modelu (GPT-4, Claude). Efekt to niższe koszty i wyższa jakość odpowiedzi.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.4.25 |
| Język | Python |
| Pliki źródłowe | 108 |
| Linie kodu | 16 828 |
| Pliki testowe | 32 |

## Kluczowe funkcje

API jest maksymalnie proste — jedna funkcja `preprocess_and_execute()` z konfigurowalnymi strategiami (classify, structure, enrich). preLLM wspiera reguły domenowe (np. wykrywanie destruktywnych operacji na bazie danych), konfigurację per-domena (DevOps, coding, business, embedded) i fallback chain dla modeli.

Typowe oszczędności to 40-60% kosztów LLM przy zachowaniu lub poprawie jakości odpowiedzi.

## Rola w ekosystemie Semcod

preLLM jest poprzednikiem llx i działa na wyższym poziomie abstrakcji — preprocessuje zapytania niezwiązane z kodem. W ekosystemie Semcod jest używany w planfile (generowanie strategii) i pfix (auto-fix błędów).

## Jak zacząć

```bash
pip install prellm
```

```python
from prellm import preprocess_and_execute

result = await preprocess_and_execute(
    query="Popraw mój projekt z hardcode'em",
    small_llm="ollama/qwen2.5:3b",
    large_llm="anthropic/claude-sonnet-4-20250514",
    strategy="structure",
)
```

## Repozytorium

- GitHub: [github.com/semcod/prellm](https://github.com/semcod/prellm)
- Licencja: Apache-2.0
