---
title: "clickmd — Renderowanie Markdown w terminalu z kolorowaniem składni"
slug: clickmd-markdown-terminal
date: 2026-04-09
author: Tom Sapletta
categories:
  - Narzędzia
  - CLI
tags:
  - cli
  - markdown
  - terminal
  - ansi
  - syntax-highlighting
excerpt: "clickmd renderuje pliki Markdown bezpośrednio w terminalu z pełnym kolorowaniem składni, stylowaniem nagłówków i formatowaniem tabel."
featured_image: ""
status: publish
path: /home/tom/github/semcod/clickmd
---

## Czym jest clickmd?

clickmd to biblioteka do renderowania Markdown w aplikacjach CLI. Zamiast wyświetlać surowy tekst Markdown w terminalu, clickmd parsuje go i renderuje z kolorami ANSI — nagłówki, bloki kodu z syntax highlighting, tabele, listy i linki wyglądają profesjonalnie bezpośrednio w konsoli.

## Status projektu

| Metryka | Wartość |
|---------|---------|
| Wersja | 1.1.13 |
| Język | Python |
| Pliki źródłowe | 36 |
| Linie kodu | 7 995 |
| Pliki testowe | 6 |

## Kluczowe funkcje

clickmd wspiera pełne formatowanie Markdown: nagłówki (z kolorami wg poziomu), bloki kodu z syntax highlighting dla wielu języków, tabele ASCII, listy numerowane i nienumerowane, bold/italic/strikethrough i linki. Działa jako biblioteka Python i jako komenda CLI.

## Rola w ekosystemie Semcod

clickmd jest używany przez narzędzia CLI ekosystemu (goal, planfile, domd, pyqual) do wyświetlania raportów i dokumentacji bezpośrednio w terminalu — bez konieczności otwierania przeglądarki.

## Jak zacząć

```bash
pip install clickmd
clickmd render README.md
```

## Repozytorium

- GitHub: [github.com/semcod/clickmd](https://github.com/semcod/clickmd)
- Licencja: Apache-2.0
