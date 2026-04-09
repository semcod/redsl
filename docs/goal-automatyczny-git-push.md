---
title: "goal — Automatyczny git push z inteligentnym generowaniem commitów"
slug: goal-automatyczny-git-push
date: 2026-04-09
author: Tom Sapletta
categories:
  - Automatyzacja
  - Git
tags:
  - git
  - automation
  - commit
  - changelog
  - versioning
excerpt: "goal automatyzuje cykl git push — analizuje zmiany w kodzie, generuje konwencjonalne commity na podstawie głębokiej analizy i zarządza workflow release'ów."
featured_image: ""
status: publish
path: /home/tom/github/semcod/goal
---

## Czym jest goal?

goal to narzędzie do automatyzacji operacji git, które analizuje zmiany w kodzie i generuje inteligentne, konwencjonalne commity (conventional commits). Zamiast pisać ręcznie "fix: naprawiono bug w parsowaniu", goal analizuje diff, rozumie kontekst zmian i sam generuje precyzyjny komunikat.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 2.1.177 |
| Język | Python |
| Pliki źródłowe | 138 |
| Linie kodu | 24 623 |
| Pliki testowe | 21 |

## Kluczowe funkcje

goal obsługuje pełny workflow: od analizy zmian, przez generowanie commitów z użyciem LLM, po automatyczne zarządzanie wersjami i changelogami. Wspiera interaktywny tryb release'ów, gdzie developer wybiera typ wersji (patch/minor/major), a goal automatycznie aktualizuje wersje, tworzy tagi i generuje changelog.

Głęboka analiza kodu pozwala goal rozróżniać typy zmian — refaktoryzacja, fix, feature, chore — i odpowiednio kategoryzować commity.

## Rola w ekosystemie Semcod

goal jest narzędziem operacyjnym używanym we wszystkich projektach Semcod. Automatyzuje cykl commitu i release'u, co jest kluczowe przy 29 projektach w organizacji. Integruje się z planfile (strategiczne zarządzanie sprintami).

## Jak zacząć

```bash
pip install goal
goal push --auto-commit
```

## Repozytorium

- GitHub: [github.com/semcod/goal](https://github.com/semcod/goal)
- Licencja: Apache-2.0
