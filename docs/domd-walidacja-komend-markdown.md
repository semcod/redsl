---
title: "domd — Automatyczne wykrywanie i walidacja komend z plików Markdown"
slug: domd-walidacja-komend-markdown
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Dokumentacja
tags:
  - markdown
  - command-validation
  - documentation
  - testing
  - dashboard
excerpt: "domd (Do Markdown Docs) automatycznie wykrywa komendy w plikach Markdown, uruchamia je i waliduje — generując raporty TODO.md/DONE.md i interaktywny dashboard."
featured_image: ""
status: publish
path: /home/tom/github/semcod/domd
---

## Czym jest domd?

domd (Do Markdown Docs) skanuje pliki Markdown w repozytorium, wykrywa bloki kodu z komendami (bash, Python), uruchamia je i sprawdza, czy działają poprawnie. Wynik to automatycznie generowane pliki TODO.md (komendy do naprawienia) i DONE.md (komendy działające poprawnie), plus interaktywny web dashboard.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 2.2.67 |
| Język | Python |
| Pliki źródłowe | 37 |
| Linie kodu | 3 609 |
| Pliki testowe | 29 |

## Kluczowe funkcje

domd traktuje dokumentację jako kod testowalny. Jeśli README mówi "uruchom `pip install mypackage`", domd sprawdza, czy ta komenda faktycznie działa. To eliminuje problem nieaktualnej dokumentacji — broken examples są natychmiast wykrywane.

## Rola w ekosystemie Semcod

domd waliduje dokumentację wszystkich projektów Semcod. Każdy README z blokami kodu jest automatycznie testowany, co gwarantuje, że instrukcje instalacji i przykłady użycia zawsze działają.

## Jak zacząć

```bash
pip install domd
domd run ./README.md --report
```

## Repozytorium

- GitHub: [github.com/semcod/domd](https://github.com/semcod/domd)
- Licencja: Apache-2.0
