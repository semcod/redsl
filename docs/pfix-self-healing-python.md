---
title: "pfix — Self-healing Python: automatyczna naprawa błędów runtime z LLM"
slug: pfix-self-healing-python
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Debugging
tags:
  - self-healing
  - debugging
  - llm
  - mcp
  - auto-fix
excerpt: "pfix przechwytuje błędy runtime Pythona, analizuje je i automatycznie naprawia kod oraz zależności za pomocą LLM i MCP — self-healing Python."
featured_image: ""
status: publish
path: /home/tom/github/semcod/pfix
---

## Czym jest pfix?

pfix to narzędzie self-healing dla Pythona — przechwytuje błędy runtime (exceptions, import errors, dependency conflicts), analizuje kontekst błędu i automatycznie generuje poprawkę za pomocą LLM. Obsługuje również naprawę zależności (brakujące pakiety, niekompatybilne wersje) i integruje się z MCP (Model Context Protocol).

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.72 |
| Język | Python |
| Pliki źródłowe | 88 |
| Linie kodu | 9 160 |
| Pliki testowe | 16 |

## Kluczowe funkcje

pfix oferuje trzy tryby: `pfix explain last` (wyjaśnia ostatni błąd z logów), `pfix explain TypeError` (generuje edukacyjny content o typie wyjątku) i automatyczny fix z fallback chain (próbuje kolejnych modeli LLM, aż znajdzie działającą poprawkę).

Unikalną funkcją jest `pfix-python` — wrapper, który uruchamia skrypt Pythona i automatycznie naprawia błędy w locie.

## Rola w ekosystemie Semcod

pfix jest używany w pętli CI/CD planfile — kiedy testy failują, pfix analizuje błąd i generuje propozycję poprawki, którą planfile może automatycznie zastosować i przetestować ponownie.

## Jak zacząć

```bash
pip install pfix
pfix explain last
pfix-python my_script.py
```

## Repozytorium

- GitHub: [github.com/semcod/pfix](https://github.com/semcod/pfix)
- Licencja: Apache-2.0
