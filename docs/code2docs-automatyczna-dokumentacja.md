---
title: "code2docs — Automatyczna dokumentacja z analizy kodu źródłowego"
slug: code2docs-automatyczna-dokumentacja
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Dokumentacja
tags:
  - documentation
  - auto-docs
  - readme-generator
  - api-reference
  - code-analysis
excerpt: "code2docs generuje i synchronizuje dokumentację projektu bezpośrednio z kodu źródłowego — README, CONTRIBUTING, API reference i organization overview."
featured_image: ""
status: publish
path: /home/tom/github/semcod/code2docs
---

## Czym jest code2docs?

code2docs automatyzuje generowanie dokumentacji projektu na podstawie analizy kodu źródłowego. Zamiast ręcznie pisać README i aktualizować je przy każdej zmianie, code2docs skanuje repozytorium i generuje aktualną dokumentację — w tym README projektu, CONTRIBUTING.md, API reference i overview całej organizacji.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 3.0.25 |
| Język | Python |
| Pliki źródłowe | 64 |
| Linie kodu | 8 220 |
| Pliki testowe | 10 |

## Kluczowe funkcje

code2docs zawiera specjalizowane generatory: ContributingGenerator (wykrywa narzędzia dev i generuje instrukcje), OrgReadmeGenerator (skanuje wiele projektów i tworzy overview organizacji), a także generatory dla testów, code style i pull requestów.

Narzędzie integruje się z code2llm — wykorzystuje metryki kodu do wzbogacania dokumentacji o informacje o złożoności, pokryciu testami i architekturze.

## Rola w ekosystemie Semcod

code2docs jest odpowiedzialny za dokumentację wszystkich 29 projektów w organizacji Semcod. OrgReadmeGenerator automatycznie generuje overview ekosystemu z opisami, wersjami i linkami.

## Jak zacząć

```bash
pip install code2docs
code2docs generate ./my-project --output docs/
```

## Repozytorium

- GitHub: [github.com/semcod/code2docs](https://github.com/semcod/code2docs)
- Licencja: Apache-2.0
