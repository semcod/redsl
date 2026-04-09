---
title: "metrun — Profilowanie wydajności z bottleneck engine i flamegraph"
slug: metrun-profilowanie-wydajnosci
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Wydajność
tags:
  - profiling
  - performance
  - bottleneck
  - flamegraph
  - tracing
excerpt: "metrun to narzędzie do profilowania wydajności z bottleneck engine, który automatycznie identyfikuje wąskie gardła i generuje raporty flamegraph."
featured_image: ""
status: publish
path: /home/tom/github/semcod/metrun
---

## Czym jest metrun?

metrun (Execution Intelligence Tool) to narzędzie do profilowania wydajności kodu Python. Zawiera bottleneck engine — algorytm automatycznie identyfikujący najwolniejsze ścieżki wykonania — oraz generator raportów flamegraph, które wizualizują, gdzie program spędza najwięcej czasu.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.12 |
| Język | Python |
| Pliki źródłowe | 39 |
| Linie kodu | 4 092 |
| Pliki testowe | 19 |
| Ocena dojrzałości | A |

## Kluczowe funkcje

Bottleneck engine analizuje profil wykonania i generuje czytelny raport z top 10 wąskich gardeł, wraz z sugestiami optymalizacji. Raporty flamegraph mogą być eksportowane do HTML lub SVG, co ułatwia ich udostępnianie w zespole.

metrun generuje raporty zrozumiałe dla człowieka — nie surowe dane tracingu, ale przetworzone wnioski z konkretnymi rekomendacjami.

## Rola w ekosystemie Semcod

metrun uzupełnia statyczną analizę code2llm o dane runtime. W pipeline Semcod może być uruchomiony po refaktoryzacji, aby zweryfikować, że zmiany nie pogorszyły wydajności.

## Jak zacząć

```bash
pip install metrun
metrun profile ./src/main.py --output report.html
```

## Repozytorium

- GitHub: [github.com/semcod/metrun](https://github.com/semcod/metrun)
- Licencja: Apache-2.0
