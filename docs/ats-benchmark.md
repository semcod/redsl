---
title: "ats-benchmark — Benchmarki dla automatyzacji testów i analizy kodu"
slug: ats-benchmark
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - Benchmarking
tags:
  - benchmark
  - testing
  - performance
  - automation
excerpt: "ats-benchmark to zestaw benchmarków do pomiaru wydajności narzędzi automatyzacji testów i analizy kodu w ekosystemie Semcod."
featured_image: ""
status: publish
path: /home/tom/github/semcod/ats-benchmark
---

## Czym jest ats-benchmark?

ats-benchmark to zestaw benchmarków mierzących wydajność narzędzi automatyzacji — od czasu analizy statycznej, przez throughput LLM, po jakość generowanego kodu. Największy projekt w ekosystemie pod względem danych (85k linii), ponieważ zawiera obszerne zestawy testowe i dane referencyjne.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 1.0.9 |
| Język | Python |
| Pliki źródłowe | 57 |
| Linie kodu | 84 719 |
| Pliki testowe | 1 |

## Kluczowe funkcje

ats-benchmark zawiera klasy do mierzenia wyników naprawy kodu przez LLM (RepairResult), przykładową aplikację e-commerce (ProductCatalog, ShoppingCart, PaymentProcessor, OrderService, AnalyticsService) służącą jako realistyczny target benchmarków, oraz infrastrukturę do porównywania modeli i narzędzi.

## Rola w ekosystemie Semcod

ats-benchmark dostarcza dane do qualbench i jest używany do walidacji, że zmiany w pipeline Semcod nie pogarszają wydajności. Przykładowa aplikacja e-commerce służy jako standardowy benchmark dla nowych wersji narzędzi.

## Repozytorium

- GitHub: [github.com/semcod/ats-benchmark](https://github.com/semcod/ats-benchmark)
- Licencja: Apache-2.0
