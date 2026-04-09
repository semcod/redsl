---
title: "weekly — Kompleksowy analizator jakości projektu Python"
slug: weekly-analizator-jakosci
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Jakość kodu
tags:
  - code-quality
  - analysis
  - linter
  - ci-cd
  - reports
excerpt: "weekly automatycznie wykrywa problemy w code style, dokumentacji, CI/CD i zależnościach — generując actionable next steps i szczegółowe raporty."
featured_image: ""
status: publish
path: /home/tom/github/semcod/weekly
---

## Czym jest weekly?

weekly to kompleksowy analizator jakości projektu Python, który skanuje nie tylko kod, ale cały ekosystem projektu: code style, dokumentację, konfigurację CI/CD, zależności i strukturę. Wynik to lista priorytetyzowanych problemów z konkretnymi krokami naprawczymi.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.41 |
| Język | Python |
| Pliki źródłowe | 32 |
| Linie kodu | 3 682 |
| Pliki testowe | 10 |

## Kluczowe funkcje

weekly sprawdza: brakujące pliki konfiguracyjne (pyproject.toml, .gitignore, CI workflows), nieaktualne zależności, brak testów, problemy z dokumentacją i code style. Każdy problem ma przypisany priorytet i sugerowany krok naprawczy — actionable, nie tylko informacyjny.

Narzędzie jest zaprojektowane do cotygodniowego uruchamiania (stąd nazwa) — śledzenie trendów jakości w czasie.

## Rola w ekosystemie Semcod

weekly jest narzędziem do cotygodniowych skanów jakości w ramach usługi Quality Retainer. Generuje raporty trendów, które trafiają do klientów.

## Jak zacząć

```bash
pip install weekly
weekly analyze ./my-project --report weekly-report.md
```

## Repozytorium

- GitHub: [github.com/semcod/weekly](https://github.com/semcod/weekly)
- Licencja: Apache-2.0
