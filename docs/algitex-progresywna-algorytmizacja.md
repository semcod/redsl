---
title: "algitex — Od LLM do deterministycznego kodu: progresywna algorytmizacja"
slug: algitex-progresywna-algorytmizacja
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Automatyzacja
tags:
  - llm
  - progressive-algorithmization
  - devtools
  - proxy
  - tickets
excerpt: "algitex to toolchain progresywnej algorytmizacji — przekształca rozwiązania prototypowane z LLM w deterministyczny, testowalny kod produkcyjny."
featured_image: ""
status: publish
path: /home/tom/github/semcod/algitex
---

## Czym jest algitex?

algitex (Algorithmic Extraction) to toolchain, który realizuje filozofię progresywnej algorytmizacji: zaczynasz od prototypu z LLM, a algitex stopniowo zastępuje niedeterministyczne fragmenty (wywołania LLM) kodem algorytmicznym. Efekt końcowy to deterministyczny, testowalny, przewidywalny kod — bez zależności od zewnętrznych API.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.59 |
| Język | Python |
| Pliki źródłowe | 94 |
| Linie kodu | 15 178 |
| Pliki testowe | 20 |

## Kluczowe funkcje

algitex analizuje, które fragmenty kodu wciąż wywołują LLM i proponuje algorytmiczne zamienniki. Integruje się z systemami proxy i ticketowymi — każda zamiana jest śledzona jako task z metrykami przed/po.

## Rola w ekosystemie Semcod

algitex reprezentuje długoterminową wizję Semcod — narzędzia pipeline'u same przechodzą progresywną algorytmizację. To co dziś robi LLM, jutro zrobi algorytm.

## Repozytorium

- GitHub: [github.com/semcod/algitex](https://github.com/semcod/algitex)
- Licencja: Apache-2.0
