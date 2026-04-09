---
title: "cost — Kalkulator kosztów AI per commit z automatycznymi badge'ami"
slug: cost-kalkulator-kosztow-ai
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Koszty
tags:
  - ai-cost
  - tracking
  - badge
  - litellm
  - devops
excerpt: "cost to zero-config kalkulator kosztów AI per commit i model — automatycznie generuje badge'e, raporty i integruje się z CI/CD przez pre-commit hooki."
featured_image: ""
status: publish
path: /home/tom/github/semcod/costs
---

## Czym jest cost?

cost (costs) to narzędzie CLI, które analizuje historię commitów w repozytorium git i oblicza koszty użycia modeli AI. Dla każdego commitu, który był wspomagany przez LLM, cost oblicza koszt na podstawie modelu, liczby tokenów i cennika providera. Wynik to raport z łącznym kosztem AI i porównaniem z kosztem czasu developera.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.48 |
| Język | Shell / Python |
| Pliki źródłowe | 17 |
| Linie kodu | 1 478 |
| Pliki testowe | 1 |

## Kluczowe funkcje

cost oferuje automatyczne generowanie badge'ów (np. "AI Cost: $7.50", "Human Time: 16.8h"), integrację z pre-commit hookami (badge aktualizuje się automatycznie przy każdym commit), raporty Markdown/HTML i integrację z GitHub Actions.

Model biznesowy narzędzia to dwa tiery: BYOK (darmowy, używasz własnego klucza API) i SaaS ($9/miesiąc z managed keys i dashboardem).

## Rola w ekosystemie Semcod

cost jest używany we wszystkich projektach Semcod do śledzenia ROI automatyzacji. Pozwala odpowiedzieć na pytanie: ile kosztowało nas AI vs ile zaoszczędziliśmy czasu developera?

## Jak zacząć

```bash
pip install costs
costs analyze --repo . --model gpt-4o
costs auto-badge
```

## Repozytorium

- GitHub: [github.com/semcod/cost](https://github.com/semcod/cost)
- Licencja: Apache-2.0
