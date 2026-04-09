---
title: "code2logic — Analiza przepływu kodu z przetwarzaniem zapytań NLP"
slug: code2logic-analiza-nlp
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Analiza kodu
tags:
  - static-analysis
  - NLP
  - control-flow
  - data-flow
  - call-graph
excerpt: "code2logic rozszerza code2llm o przetwarzanie zapytań w języku naturalnym — pytasz po polsku lub angielsku, a narzędzie odpowiada danymi z analizy kodu."
featured_image: ""
status: publish
path: /home/tom/github/semcod/code2logic
---

## Czym jest code2logic?

code2logic to rozszerzenie code2llm o warstwę NLP (Natural Language Processing). Zamiast pisać zapytania w formacie technicznym, możesz zadać pytanie w języku naturalnym — np. "które funkcje mają złożoność cyklomatyczną powyżej 10?" — a code2logic przetłumaczy je na zapytanie do grafu kodu i zwróci wynik.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.2.1 |
| Język | Python |
| Pliki źródłowe | 173 |
| Linie kodu | 48 133 |
| Pliki testowe | 49 |

## Kluczowe funkcje

code2logic buduje na fundamencie code2llm (CFG, DFG, call graphs) i dodaje query engine obsługujący język naturalny. Największy projekt w ekosystemie Semcod pod względem linii kodu (48k), co odzwierciedla złożoność parsowania zapytań NLP i mapowania ich na operacje grafowe.

## Rola w ekosystemie Semcod

code2logic jest narzędziem interaktywnym — pozwala developerom eksplorować metryki kodu w trybie konwersacyjnym, bez konieczności znajomości API code2llm.

## Jak zacząć

```bash
pip install code2logic
code2logic query ./src "pokaż god modules z CC > 20"
```

## Repozytorium

- GitHub: [github.com/semcod/code2logic](https://github.com/semcod/code2logic)
- Licencja: Apache-2.0
