---
title: "toonic — Uniwersalny format TOON zoptymalizowany dla LLM"
slug: toonic-format-toon
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Formaty danych
tags:
  - toon
  - format
  - llm
  - serialization
  - platform
excerpt: "toonic to platforma uniwersalnego formatu TOON — zoptymalizowanego pod przetwarzanie przez modele LLM, z parserem, generatorem i narzędziami konwersji."
featured_image: ""
status: publish
path: /home/tom/github/semcod/toonic
---

## Czym jest toonic?

toonic to platforma do pracy z formatem TOON (Text-Optimized Object Notation) — formatem danych zaprojektowanym specjalnie pod przetwarzanie przez modele LLM. TOON jest bardziej kompaktowy niż JSON/YAML, zachowując czytelność i strukturę — co przekłada się na mniejsze zużycie tokenów i szybsze przetwarzanie.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 1.0.15 |
| Język | Python |
| Pliki źródłowe | 76 |
| Linie kodu | 11 583 |
| Pliki testowe | 15 |

## Kluczowe funkcje

toonic zawiera parser i generator formatu TOON, narzędzia konwersji (JSON → TOON, YAML → TOON), walidator schematu i bibliotekę do programistycznego tworzenia dokumentów TOON. Format jest używany przez code2llm do zapisu metryk kodu i przez inne narzędzia Semcod jako lingua franca między komponentami pipeline'u.

## Rola w ekosystemie Semcod

toonic jest fundamentem wymiany danych w ekosystemie. Pliki `.toon` (validation.toon, project.toon, flow.toon, calls.toon) są generowane przez code2llm i konsumowane przez llx, redup, regix i ReDSL.

## Jak zacząć

```bash
pip install toonic
toonic convert project.yaml --to toon --output project.toon
```

## Repozytorium

- GitHub: [github.com/semcod/toonic](https://github.com/semcod/toonic)
- Licencja: Apache-2.0
