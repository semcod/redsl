---
title: "code2llm — Analiza przepływu kodu w formacie zoptymalizowanym dla LLM"
slug: code2llm-analiza-przeplywu-kodu
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Analiza kodu
tags:
  - static-analysis
  - control-flow
  - data-flow
  - call-graph
  - TOON
excerpt: "code2llm to silnik analizy przepływu kodu Python, który generuje grafy CFG, DFG i call graphs w zoptymalizowanym formacie TOON — gotowym do przetworzenia przez modele LLM."
featured_image: ""
status: publish
path: /home/tom/github/semcod/code2llm
---

## Czym jest code2llm?

code2llm to wysokowydajny silnik analizy statycznej kodu Python, który ekstrahuje strukturę programu — grafy przepływu sterowania (CFG), grafy przepływu danych (DFG) i grafy wywołań (call graphs) — i zapisuje je w zoptymalizowanym formacie TOON. Ten format jest zaprojektowany tak, aby modele językowe mogły efektywnie przetwarzać metryki kodu bez konieczności parsowania surowych plików źródłowych.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.5.103 |
| Język | Python |
| Pliki źródłowe | 137 |
| Linie kodu | 25 223 |
| Pliki testowe | 33 |
| Ocena dojrzałości | A |

## Kluczowe funkcje

code2llm analizuje repozytorium i generuje plik `toon.yaml` zawierający metryki takie jak średnia złożoność cyklomatyczna (CC̄), liczba funkcji, klas i modułów. Analiza 20 tys. linii kodu trwa około 6 sekund — algorytmicznie, bez wywoływania modeli LLM.

Narzędzie wspiera inteligentne zapytania do kodu (code queries), co pozwala szybko zlokalizować god modules, funkcje o wysokim fan-out i inne problematyczne wzorce.

## Rola w ekosystemie Semcod

code2llm jest fundamentem pipeline'u Semcod — dostarcza dane wejściowe dla narzędzi takich jak redup (detekcja duplikacji), regix (indeks regresji), llx (routing modeli) i ReDSL (planowanie refaktoryzacji). Bez code2llm żadne z tych narzędzi nie mogłoby działać, ponieważ potrzebują ustrukturyzowanych metryk kodu zamiast surowych plików.

## Jak zacząć

```bash
pip install code2llm
code2llm analyze ./src --output project.toon
```

Wynik to plik TOON z pełną mapą projektu — gotowy do dalszej analizy lub bezpośredniego podania do LLM.

## Repozytorium

- GitHub: [github.com/semcod/code2llm](https://github.com/semcod/code2llm)
- Licencja: Apache-2.0
