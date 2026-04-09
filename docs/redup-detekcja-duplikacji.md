---
title: "redup — Detekcja duplikacji kodu z planowaniem refaktoryzacji"
slug: redup-detekcja-duplikacji
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Refaktoryzacja
tags:
  - duplication
  - refactoring
  - AST
  - LLM
  - code-analysis
excerpt: "redup wykrywa duplikacje kodu na poziomie semantycznym i strukturalnym (AST), a następnie generuje plan refaktoryzacji gotowy do wykonania przez LLM."
featured_image: ""
status: publish
path: /home/tom/github/semcod/redup
---

## Czym jest redup?

redup to analizator duplikacji kodu, który działa na poziomie AST (Abstract Syntax Tree), a nie tokenów. Oznacza to, że wykrywa nie tylko dosłowne kopie kodu, ale też fragmenty semantycznie podobne — np. funkcje robiące to samo, ale z innymi nazwami zmiennych. Po wykryciu duplikacji generuje gotowy plan refaktoryzacji, który może być wykonany ręcznie lub przez LLM.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.4.15 |
| Język | Python |
| Pliki źródłowe | 21 |
| Linie kodu | 2 128 |
| Pliki testowe | 13 |
| Ocena dojrzałości | A |

## Kluczowe funkcje

redup grupuje zduplikowany kod w klastry i oblicza, ile linii można odzyskać przez ekstrakcję wspólnych funkcji lub modułów. W typowym projekcie 20k LOC redup znajduje 15-20 grup duplikacji z potencjałem redukcji 200+ linii.

Plan refaktoryzacji jest generowany w formacie zrozumiałym dla LLM — z kontekstem, sugerowaną strategią (extract function, extract module, template method) i priorytetem.

## Rola w ekosystemie Semcod

redup dostarcza dane o duplikacjach do ReDSL, który następnie planuje i wykonuje refaktoryzację. Wynik jest walidowany przez regix, który sprawdza, czy metryki jakości nie pogorszyły się.

## Jak zacząć

```bash
pip install redup
redup scan ./src --output duplicates.json
```

## Repozytorium

- GitHub: [github.com/semcod/redup](https://github.com/semcod/redup)
- Licencja: Apache-2.0
