---
title: "proxym — Inteligentne proxy AI z routingiem, cache'em i delta bufferami"
slug: proxym-proxy-ai
date: 2026-04-09
author: Tom Sapletta
categories:
  - Infrastruktura
  - LLM
tags:
  - proxy
  - multi-provider
  - semantic-cache
  - routing
  - delta-context
excerpt: "proxym to proxy AI obsługujące wielu providerów LLM z semantycznym cache'em, routingiem kosztów i delta context bufferami — infrastruktura dla całego pipeline'u Semcod."
featured_image: ""
status: publish
path: /home/tom/github/semcod/proxym
---

## Czym jest proxym?

proxym to inteligentne proxy dla wywołań API modeli LLM. Stoi pomiędzy aplikacją a providerami (OpenAI, Anthropic, Ollama, OpenRouter) i dodaje warstwy optymalizacji: semantyczny cache (identyczne zapytania nie są powtarzane), routing kosztów (tańszy provider dla prostych zadań) i delta context buffers (zamiast wysyłać cały kontekst, wysyła tylko zmienione fragmenty).

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.123 |
| Język | Python |
| Pliki źródłowe | 94 |
| Linie kodu | 21 778 |
| Pliki testowe | 78 |
| Ocena dojrzałości | A+ |

## Kluczowe funkcje

proxym obsługuje routing multi-provider, co oznacza, że jedno zapytanie może być automatycznie przekierowane do najtańszego lub najszybszego dostępnego modelu. Semantyczny cache redukuje koszty o 30-50% w typowych scenariuszach refaktoryzacji, gdzie wiele plików wymaga podobnych operacji.

Delta context buffers to unikalna funkcja — zamiast wysyłać 4000 tokenów kontekstu za każdym razem, proxym śledzi, co się zmieniło i wysyła tylko delta, oszczędzając tokeny i koszty.

## Rola w ekosystemie Semcod

proxym jest warstwą infrastrukturalną, przez którą przechodzą wszystkie wywołania LLM w pipeline Semcod. llx podejmuje decyzję o routingu, a proxym ją wykonuje, dodając cache i optymalizacje kontekstu.

## Jak zacząć

```bash
pip install proxym
proxym serve --port 9999 --config proxy.yaml
```

## Repozytorium

- GitHub: [github.com/semcod/proxym](https://github.com/semcod/proxym)
- Licencja: Apache-2.0
