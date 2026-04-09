---
title: "pyqual — Deklaratywne quality gates dla AI-assisted development"
slug: pyqual-quality-gates
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Jakość kodu
tags:
  - quality-gates
  - CI/CD
  - LLM
  - pipeline
  - ruff
excerpt: "pyqual łączy ruff, mypy i bandit w jeden deklaratywny pipeline z automatycznymi poprawkami — quality gates zaprojektowane pod AI-assisted development."
featured_image: ""
status: publish
path: /home/tom/github/semcod/pyqual
---

## Czym jest pyqual?

pyqual to deklaratywny system quality gates stworzony z myślą o projektach, w których kod jest generowany lub wspomagany przez modele LLM. Zamiast konfigurować osobno ruff, mypy i bandit, definiujesz reguły w jednym pliku YAML, a pyqual uruchamia pętle walidacji z automatycznymi poprawkami.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.140 |
| Język | Python |
| Pliki źródłowe | 118 |
| Linie kodu | 18 887 |
| Pliki testowe | 33 |
| Ocena dojrzałości | A+ |

## Kluczowe funkcje

Deklaratywna konfiguracja quality gates pozwala zdefiniować progi akceptacji (np. pokrycie testami ≥80%, zero błędów bandit o severity critical) i uruchomić pętlę: analiza → poprawka → walidacja → powtórz. Proste błędy są naprawiane deterministycznie, a złożone mogą być delegowane do LLM.

pyqual integruje się z CI/CD — działa zarówno jako komenda CLI, jak i jako krok w GitHub Actions czy GitLab CI.

## Rola w ekosystemie Semcod

pyqual jest głównym narzędziem do egzekwowania jakości w pipeline Semcod. Działa w tandemie z vallm (walidacja kodu z LLM) i regix (detekcja regresji). Kiedy ReDSL wykonuje refaktoryzację, pyqual weryfikuje, czy wynik spełnia zdefiniowane quality gates.

## Jak zacząć

```bash
pip install pyqual
pyqual run ./src --config quality.yaml
```

## Repozytorium

- GitHub: [github.com/semcod/pyqual](https://github.com/semcod/pyqual)
- Licencja: Apache-2.0
