---
title: "nfo — Automatyczny system logowania funkcji z dekoratorami i analizą LLM"
slug: nfo-automatyczne-logowanie-funkcji
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Observability
tags:
  - logging
  - decorator
  - sqlite
  - prometheus
  - observability
excerpt: "nfo to system automatycznego logowania funkcji Python za pomocą dekoratorów — wspiera wiele sinków (SQLite, CSV, Markdown, Prometheus) i analizę LLM dla DevOps."
featured_image: ""
status: publish
path: /home/tom/github/semcod/nfo
---

## Czym jest nfo?

nfo to automatyczny system logowania, który dodaje observability do funkcji Python za pomocą dekoratorów. Zamiast ręcznie dodawać `logger.info()` do każdej funkcji, nfo automatycznie śledzi wywołania, argumenty, czas wykonania i wyniki — zapisując dane do wybranego sinku.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.2.20 |
| Język | Python |
| Pliki źródłowe | 84 |
| Linie kodu | 13 453 |
| Pliki testowe | 25 |

## Kluczowe funkcje

nfo wspiera wiele formatów wyjścia: SQLite (do analizy), CSV (do eksportu), Markdown (do dokumentacji), Prometheus (do monitoringu). Unikalna funkcja to LLM-powered analysis — nfo może przeanalizować zebrane logi i wygenerować raport z anomaliami, wąskimi gardłami i sugestiami optymalizacji.

Dekorator `@nfo` jest minimalnie inwazyjny — dodajesz jedną linię nad funkcją i masz pełną observability.

## Rola w ekosystemie Semcod

nfo dostarcza dane runtime dla metrun (profilowanie wydajności) i jest używany wewnętrznie w narzędziach Semcod do śledzenia wydajności poszczególnych kroków pipeline'u.

## Jak zacząć

```bash
pip install nfo
```

```python
from nfo import nfo

@nfo(sink="sqlite")
def process_data(items):
    return [transform(item) for item in items]
```

## Repozytorium

- GitHub: [github.com/semcod/nfo](https://github.com/semcod/nfo)
- Licencja: Apache-2.0
