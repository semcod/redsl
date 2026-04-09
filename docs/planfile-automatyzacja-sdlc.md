---
title: "planfile — Platforma automatyzacji SDLC ze strategicznym zarządzaniem sprintami"
slug: planfile-automatyzacja-sdlc
date: 2026-04-09
author: Tom Sapletta
categories:
  - Automatyzacja
  - Zarządzanie projektami
tags:
  - sdlc
  - strategy
  - sprint
  - jira
  - cicd
excerpt: "planfile automatyzuje cykl życia oprogramowania — od definiowania strategii i sprintów w YAML, przez integrację z Jira/GitHub, po automatyczne pętle fix-test-retest."
featured_image: ""
status: publish
path: /home/tom/github/semcod/planfile
---

## Czym jest planfile?

planfile to platforma automatyzacji SDLC (Software Development Life Cycle), która pozwala definiować strategie projektowe i sprinty w plikach YAML, a następnie automatycznie synchronizować je z systemami ticketowymi (GitHub Issues, Jira, GitLab) i pipeline'ami CI/CD.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 0.1.52 |
| Język | Python |
| Pliki źródłowe | 99 |
| Linie kodu | 12 627 |
| Pliki testowe | 17 |
| Koszt LLM | $7.50 (53 commity) |
| Czas developerski | ~16.8h |

## Kluczowe funkcje

planfile oferuje strategiczne modelowanie projektów (YAML), automatyczną pętlę CI/CD (test → ticket → fix → retest), integrację z wieloma backendami (GitHub, Jira, GitLab, generic HTTP), LLM-powered auto-fix i generowanie strategii z AI, a także REST API (FastAPI) i CLI.

Unikalna funkcja to checkbox-tickets — natywne wsparcie dla markdown checkboxów jako ticketów, co pozwala zarządzać zadaniami bezpośrednio w plikach `.md`.

## Rola w ekosystemie Semcod

planfile jest warstwą zarządzania projektami. Koordynuje sprinty, śledzi postęp i integruje się z ekosystemem narzędzi (code2llm, llx, proxym) przez MCP i REST API.

## Jak zacząć

```bash
pip install planfile
planfile strategy generate ./my-project --model gpt-4o
planfile apply strategy.yaml --backend github
```

## Repozytorium

- GitHub: [github.com/semcod/planfile](https://github.com/semcod/planfile)
- Licencja: Apache-2.0
