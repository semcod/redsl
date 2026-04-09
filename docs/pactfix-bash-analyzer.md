---
title: "pactfix — Analizator i auto-fixer skryptów Bash z ShellCheck"
slug: pactfix-bash-analyzer
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - DevOps
tags:
  - bash
  - shellcheck
  - auto-fix
  - scripting
  - linting
excerpt: "pactfix analizuje skrypty Bash w czasie rzeczywistym z integracją ShellCheck i automatycznie naprawia wykryte problemy."
featured_image: ""
status: publish
path: /home/tom/github/semcod/pactfix
---

## Czym jest pactfix?

pactfix to analizator skryptów Bash, który integruje ShellCheck z automatycznym naprawianiem błędów. Zamiast ręcznie poprawiać każde ostrzeżenie ShellCheck, pactfix aplikuje poprawki automatycznie — od brakujących cudzysłowów po niebezpieczne wzorce (np. `eval`, unquoted variables).

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 1.0.5 |
| Język | Python |
| Pliki źródłowe | 33 |
| Linie kodu | 4 280 |
| Pliki testowe | 8 |

## Kluczowe funkcje

pactfix działa w trybie real-time — monitoruje zmiany w skryptach i natychmiast zgłasza problemy. Auto-fix obsługuje najpopularniejsze kategorie błędów ShellCheck (quoting, variable expansion, deprecated syntax). Narzędzie generuje diff z naniesionymi poprawkami do review.

## Rola w ekosystemie Semcod

pactfix jest odpowiedzialny za jakość skryptów Bash w projektach Semcod — scripts/, hooks/, CI/CD workflows i Makefile. Uzupełnia pfix (Python) o wsparcie dla Shell.

## Jak zacząć

```bash
pip install pactfix
pactfix analyze ./scripts/ --auto-fix
```

## Repozytorium

- GitHub: [github.com/semcod/pactfix](https://github.com/semcod/pactfix)
- Licencja: Apache-2.0
