---
title: "Ekosystem Semcod — 29 narzędzi open-source do automatyzacji jakości kodu"
slug: ekosystem-semcod-przeglad
date: 2026-04-09
author: Tom Sapletta
categories:
  - Ekosystem
  - Przegląd
tags:
  - semcod
  - ecosystem
  - open-source
  - code-quality
  - automation
excerpt: "Przegląd ekosystemu Semcod — 29 narzędzi open-source tworzących zautomatyzowany pipeline od analizy kodu, przez refaktoryzację z AI, po walidację w sandboxie Docker."
featured_image: ""
status: publish
path: /home/tom/github/semcod/ekosystem
---

## Czym jest Semcod?

Semcod to ekosystem 29 narzędzi open-source do automatyzacji jakości kodu, stworzony przez Toma Saplettę z Gdańska. Pipeline Semcod różni się od narzędzi takich jak SonarQube, Codacy czy CodeClimate jedną kluczową cechą: nie kończy pracy na raporcie. Analizuje algorytmicznie w ~6 sekund, planuje refaktoryzację z pomocą LLM, wykonuje poprawki i waliduje wynik w sandboxie Docker. Output to gotowy PR z poprawionym kodem — nie dashboard do przeglądania.

## Architektura pipeline'u

Pipeline Semcod składa się z warstw, z których każda odpowiada za inny aspekt automatyzacji:

### Warstwa analizy

- **code2llm** (v0.5.103, 25k LOC) — silnik analizy przepływu kodu: CFG, DFG, call graphs w formacie TOON
- **code2logic** (v0.2.1, 48k LOC) — rozszerzenie code2llm o zapytania w języku naturalnym
- **toonic** (v1.0.15, 12k LOC) — platforma formatu TOON zoptymalizowanego pod LLM

### Warstwa jakości

- **pyqual** (v0.1.140, 19k LOC) — deklaratywne quality gates (ruff + mypy + bandit)
- **prefact** (v0.1.30, 4k LOC) — linter z regułami LLM-aware
- **redup** (v0.4.15, 2k LOC) — detekcja duplikacji na poziomie AST
- **regix** (v0.1.11, 7k LOC) — indeks regresji jakości między wersjami git
- **vallm** (v0.1.71, 10k LOC) — walidacja kodu generowanego przez LLM

### Warstwa LLM i routing

- **llx** (v0.1.55, 23k LOC) — inteligentny routing modeli oparty na metrykach kodu
- **proxym** (v0.1.123, 22k LOC) — proxy AI z semantic cache i delta context buffers
- **preLLM** (v0.4.25, 17k LOC) — preprocessing small-then-large dla zapytań LLM
- **algitex** (v0.1.59, 15k LOC) — progresywna algorytmizacja: od LLM do deterministycznego kodu

### Warstwa automatyzacji i DevOps

- **goal** (v2.1.177, 25k LOC) — automatyczny git push z inteligentnym generowaniem commitów
- **planfile** (v0.1.52, 13k LOC) — platforma SDLC z CI/CD i auto-fix loops
- **pfix** (v0.1.72, 9k LOC) — self-healing Python: naprawa runtime errors z LLM
- **pactfix** (v1.0.5, 4k LOC) — analizator i auto-fixer skryptów Bash

### Warstwa observability i raportowania

- **metrun** (v0.1.12, 4k LOC) — profilowanie wydajności z bottleneck engine
- **nfo** (v0.2.20, 13k LOC) — automatyczne logowanie funkcji z dekoratorami
- **cost** (v0.1.48, 1.5k LOC) — kalkulator kosztów AI per commit
- **weekly** (v0.1.41, 4k LOC) — kompleksowy analizator jakości projektu
- **qualbench** (v0.3.0, 4k LOC) — CI benchmarki production readiness kodu AI

### Warstwa dokumentacji i prezentacji

- **code2docs** (v3.0.25, 8k LOC) — automatyczna dokumentacja z kodu źródłowego
- **domd** (v2.2.67, 4k LOC) — walidacja komend z plików Markdown
- **clickmd** (v1.1.13, 8k LOC) — renderowanie Markdown w terminalu

### Narzędzia wsparcia

- **ats-benchmark** (v1.0.9, 85k LOC) — benchmarki i dane referencyjne
- **heal** (v0.1.24, 1k LOC) — eksperymentalny pakiet wellness z LLM
- **shared** (v0.1.0, 0.5k LOC) — współdzielone komponenty ekosystemu

## Statystyki ekosystemu

| Metryka | Wartość |
|---------|---------|
| Liczba narzędzi | 29 |
| Łączne linie kodu | ~370 000 |
| Łączne pliki testowe | ~468 |
| Główny język | Python |
| Licencja | Apache-2.0 |
| Lokalizacja | Gdańsk, Polska |

## Model usługowy

Ekosystem Semcod jest udostępniany zarówno jako open-source (samodzielna instalacja), jak i w formie trzech usług komercyjnych:

- **Code Quality Audit** (2 000–5 000 PLN) — jednorazowy skan z raportem
- **Cleanup Sprint** (15 000–40 000 PLN) — audyt + wykonanie refaktoryzacji w 2-4 tygodnie
- **Quality Retainer** (3 000–8 000 PLN/mies.) — cotygodniowe skany z alertami i drobnymi poprawkami

Cały proces jest asynchroniczny: formularz → wycena mailem → realizacja → raport + PR.

## Jak zacząć

Odwiedź [semcod.dev](https://semcod.dev) lub przeglądaj repozytoria na [github.com/semcod](https://github.com/semcod).
