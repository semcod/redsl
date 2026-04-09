---
title: "qualbench — CI dla kodu AI: mierzy gotowość produkcyjną, nie tylko poprawność"
slug: qualbench-ci-dla-kodu-ai
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Benchmarking
tags:
  - benchmark
  - ai
  - code-quality
  - ci
  - quality-gates
excerpt: "qualbench to system CI dla kodu generowanego przez AI — mierzy production readiness zamiast samej poprawności składniowej."
featured_image: ""
status: publish
path: /home/tom/github/semcod/qualbench
---

## Czym jest qualbench?

qualbench zmienia sposób oceny kodu generowanego przez AI. Standardowe benchmarki (HumanEval, MBPP) sprawdzają, czy kod działa. qualbench idzie dalej — mierzy, czy kod jest gotowy do produkcji: czy ma testy, czy jest czytelny, czy spełnia quality gates, czy nie wprowadza regresji.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.3.0 |
| Język | Python |
| Pliki źródłowe | 25 |
| Linie kodu | 4 276 |
| Pliki testowe | 3 |

## Kluczowe funkcje

qualbench ocenia kod w wielu wymiarach: poprawność (czy działa?), jakość (CC, duplikacje, code smells), testowalność (czy ma testy? jaki coverage?), dokumentacja (docstringi, komentarze) i bezpieczeństwo (bandit scan). Wynik to score produkcyjnej gotowości — od 0% do 100%.

## Rola w ekosystemie Semcod

qualbench jest używany do benchmarkowania jakości kodu generowanego przez pipeline ReDSL. Pozwala porównywać wydajność różnych modeli LLM w kontekście production readiness, a nie tylko poprawności.

## Jak zacząć

```bash
pip install qualbench
qualbench evaluate ./generated_code/ --report benchmark.json
```

## Repozytorium

- GitHub: [github.com/semcod/qualbench](https://github.com/semcod/qualbench)
- Licencja: Apache-2.0
