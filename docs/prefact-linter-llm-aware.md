---
title: "prefact — Linter Python z regułami LLM-aware i systemem pluginów"
slug: prefact-linter-llm-aware
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Jakość kodu
tags:
  - linting
  - code-quality
  - refactoring
  - llm
  - plugins
excerpt: "prefact to linter Python z regułami świadomymi kontekstu LLM, systemem pluginów i funkcjami enterprise — rozumie, że kod mógł być wygenerowany przez AI."
featured_image: ""
status: publish
path: /home/tom/github/semcod/prefact
---

## Czym jest prefact?

prefact to narzędzie jakości kodu Python, które rozumie specyfikę kodu generowanego przez LLM. Standardowe lintery (ruff, pylint) stosują te same reguły do kodu ludzkiego i maszynowego. prefact dodaje reguły LLM-aware — wykrywa typowe anty-wzorce generowane przez modele (nadmiarowe komentarze, niepotrzebne abstrakcje, powtórzenia z promptu) i sugeruje poprawki.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.30 |
| Język | Python |
| Pliki źródłowe | 37 |
| Linie kodu | 4 022 |
| Pliki testowe | 12 |

## Kluczowe funkcje

System pluginów pozwala dodawać własne reguły specyficzne dla projektu lub organizacji. Funkcje enterprise obejmują konfigurację per-team, raportowanie do dashboardu i integrację z CI/CD.

## Rola w ekosystemie Semcod

prefact uzupełnia pyqual — o ile pyqual egzekwuje quality gates, prefact dostarcza dodatkową warstwę reguł specyficznych dla AI-generated code.

## Jak zacząć

```bash
pip install prefact
prefact check ./src --rules llm-aware
```

## Ograniczenia trybu autonomicznego w ReDSL

W integracji ReDSL z prefact tryb autonomiczny jest ograniczany po stronie orchestratora, żeby nie generować niekończących się list zadań:

- TODO.md z automatycznych skanów jest przycinany do limitu wpisów.
- dodatkowe violationy gate są dopisywane tylko do ustalonego limitu.
- jeśli TODO.md ma już zbyt wiele otwartych pozycji, ponowna regeneracja przez `prefact -a --execute-todos` jest pomijana.

To chroni batchowe uruchomienia przed eksplozją liczby zadań i blokowaniem pipeline'u.

## Repozytorium

- GitHub: [github.com/semcod/prefact](https://github.com/semcod/prefact)
- Licencja: Apache-2.0
