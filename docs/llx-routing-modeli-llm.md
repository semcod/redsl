---
title: "llx — Inteligentny routing modeli LLM oparty na metrykach kodu"
slug: llx-routing-modeli-llm
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - LLM
tags:
  - llm
  - model-routing
  - code-analysis
  - litellm
  - optimization
excerpt: "llx automatycznie wybiera optymalny model LLM do zadania na podstawie realnych metryk kodu — złożoności, rozmiaru i typu operacji."
featured_image: ""
status: publish
path: /home/tom/github/semcod/llx
---

## Czym jest llx?

llx to inteligentny router modeli LLM, który analizuje metryki kodu (z code2llm) i na ich podstawie decyduje, który model jest optymalny dla danego zadania. Proste poprawki (rename, extract variable) trafiają do taniego modelu lokalnego, a złożone refaktoryzacje (god module split, architektura) do modelu klasy GPT-4 lub Claude Opus.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.55 |
| Język | Python |
| Pliki źródłowe | 131 |
| Linie kodu | 22 765 |
| Pliki testowe | 19 |
| Ocena dojrzałości | A+ |

## Kluczowe funkcje

llx jest następcą projektu preLLM i integruje się z litellm, co daje dostęp do dziesiątek providerów LLM (OpenAI, Anthropic, Ollama, OpenRouter). Routing odbywa się na podstawie złożoności cyklomatycznej, fan-out, rozmiaru pliku i typu operacji refaktoryzacji.

Efekt: typowy koszt analizy i refaktoryzacji projektu 20k LOC spada z kilku dolarów do kilkudziesięciu centów, bo 80% operacji wykonuje tani model.

## Rola w ekosystemie Semcod

llx współpracuje z proxym (proxy AI) i ReDSL (silnik refaktoryzacji). Kiedy ReDSL generuje plan refaktoryzacji, llx decyduje, który model wykonuje każdy krok — optymalizując stosunek koszt/jakość.

## Jak zacząć

```bash
pip install llx
llx route --metrics project.toon --task "split god module"
```

## Repozytorium

- GitHub: [github.com/semcod/llx](https://github.com/semcod/llx)
- Licencja: Apache-2.0
