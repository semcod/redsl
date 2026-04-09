---
title: "regix — Indeks regresji jakości kodu między wersjami git"
slug: regix-indeks-regresji
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Jakość kodu
tags:
  - regression
  - git
  - cyclomatic-complexity
  - code-quality
  - refactoring
excerpt: "regix mierzy degradację jakości kodu między commitami i wersjami git — wykrywa regresje zanim trafią na produkcję."
featured_image: ""
status: publish
path: /home/tom/github/semcod/regix
---

## Czym jest regix?

regix (Regression Index) to narzędzie, które porównuje metryki jakości kodu między dwoma punktami w historii git — np. między ostatnim release'em a bieżącym stanem brancha. Wykrywa pogorszenie złożoności cyklomatycznej, wzrost duplikacji, nowe god modules i inne sygnały regresji.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.11 |
| Język | Python |
| Pliki źródłowe | 46 |
| Linie kodu | 6 538 |
| Pliki testowe | 22 |
| Ocena dojrzałości | A+ |

## Kluczowe funkcje

regix generuje raport delta: metryki przed vs. po, z wyraźnym wskazaniem, które pliki i funkcje pogorszyły się. Działa z sandboxem Docker — klonuje obie wersje, analizuje każdą niezależnie i porównuje wyniki.

Narzędzie integruje się z CI/CD jako quality gate: jeśli regresja przekroczy zdefiniowany próg, pipeline się zatrzymuje.

## Rola w ekosystemie Semcod

regix jest ostatnim krokiem walidacji w pipeline Semcod. Po tym, jak ReDSL wykona refaktoryzację, regix sprawdza, czy nowa wersja kodu jest rzeczywiście lepsza niż oryginał. Jeśli metryki się pogorszyły, zmiana jest odrzucana.

## Jak zacząć

```bash
pip install regix
regix compare HEAD~5..HEAD --output regression-report.json
```

## Repozytorium

- GitHub: [github.com/semcod/regix](https://github.com/semcod/regix)
- Licencja: Apache-2.0
