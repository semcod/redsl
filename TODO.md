# ReDSL — TODO / Improvement Backlog

Wygenerowano po testach na projektach `/home/tom/github/semcod/*` — 2026-04-07

---

## 🔴 Krytyczne (blokują realne użycie)

### ✅ T001 — Obsługa formatu `HEALTH[N]:` + `🟡 CC` z code2llm

**Problem:** `ToonParser` nie parsuje rzeczywistego formatu generowanego przez `code2llm`:
```
HEALTH[20]:
  🟡 CC    analyze_typescript_js CC=41 (limit:10)
  🟡 CC    analyze_php CC=29 (limit:10)
```
Parser oczekuje:
```
ALERTS (2):
  !!! cc_exceeded func = 36 (limit:15)
```
**Efekt:** 0 plików, 0 alertów mimo 69 krytycznych funkcji w projekcie.  
**Plik:** `app/analyzers/__init__.py` → `ToonParser.parse_project_toon()`  
**Akcja:** Dodać drugi branch parsowania dla formatu emoji + `CC=N (limit:N)`

---

### ✅ T002 — Obsługa sekcji `LAYERS:` jako zastępstwa MODULES

**Problem:** code2llm generuje `LAYERS:` zamiast `MODULES:`:
```
LAYERS:
  code2llm/                       CC̄=4.8    ←in:0  →out:5
  │ !! index_generator            721L  1C    7m  CC=5      ←0
  │ !! project_yaml_exporter      513L  1C   18m  CC=13     ←0
```
Parser ignoruje tę sekcję całkowicie.  
**Plik:** `app/analyzers/__init__.py` → `ToonParser.parse_project_toon()`  
**Akcja:** Dodać parser sekcji `LAYERS:` z regex do ekstrakcji `721L`, `CC=5`

---

### ✅ T003 — Obsługa formatu `M[N]:` + `file_path,line_count`

**Problem:** `project.toon` z code2llm/code2logic używa:
```
M[186]:
  advanced_data_analyzer.py,1076
  code2logic/cli.py,907
```
Parser oczekuje `M[app/models.py] 450L C:3 F:12 CC↑35`.  
**Plik:** `app/analyzers/__init__.py` → `ToonParser._parse_module_line()`  
**Akcja:** Wykrywać i parsować oba formaty modułów

---

### ✅ T004 — Fallback: bezpośrednia analiza plików `.py` gdy brak toon

**Problem:** `pfix/` ma 15560 plików `.py` bez żadnego toon — `redsl analyze` zwraca 0 wyników. Brak możliwości użycia bez wcześniejszego uruchomienia `code2llm`.  
**Plik:** `redsl/analyzers/python_analyzer.py` → `PythonAnalyzer.analyze_python_files()`  
**Akcja:** ✅ Zaimplementowane — `ToonAnalyzer.analyze_project()` fallback do `PythonAnalyzer.analyze_python_files()` gdy brak toon files. Używa stdlib ast do liczenia CC.

---

### ✅ T005 — File discovery: `analysis.toon` nie jest parsowany jako toon projektu

**Problem:** `_find_toon_files` mapuje `analysis.toon` → klucz `"analysis"` ale `analyze_project()` przetwarza tylko klucz `"project"`. Efekt: code2llm (ma `analysis.toon`) zwraca 0 wyników.  
**Plik:** `app/analyzers/__init__.py` → `_find_toon_files()` + `analyze_project()`  
**Akcja:** Użyć `analysis` jako fallback dla `project` jeśli `project` brak

---

## 🟡 Ważne (istotnie obniżają jakość)

### ✅ T006 — Obsługa `project.functions.toon` (format YAML z CC per funkcja)

**Problem:** `goal/project.functions.toon` ma najlepsze dane (CC per funkcja, linie, sygnatury) ale używa formatu YAML:
```yaml
function_details:
  goal/cli.py:
    functions[54]{name,kind,sig,loc,async,lines,cc,does}:
      main,function,(),42-98,false,56,17,Main CLI entry
```
**Plik:** `redsl/analyzers/parsers/functions_parser.py` → `FunctionsParser`  
**Akcja:** ✅ Zaimplementowane — `ToonAnalyzer._process_project_ton()` wykrywa format (zaczyna się od `project:` + zawiera `function_details:`) i używa `FunctionsParser.parse_functions_toon()`

---

### T007 — Confidence 0.0 we wszystkich propozycjach LLM

**Problem:** Każda wygenerowana propozycja ma `confidence=0.0`:
```
Generated proposal: extract_functions for app/models.py (confidence=0.00)
```
**Plik:** `app/refactors/__init__.py`  
**Akcja:** LLM prompt powinien zwracać pole `confidence` (0.0-1.0) a parser powinien je odczytywać

---

### T008 — Brak radon/flake8 jako źródła metryk CC

**Problem:** Parser opiera się wyłącznie na toon files. Radon (`pip install radon`) potrafi bezpośrednio liczyć CC dla Python.  
**Akcja:** W `CodeAnalyzer.analyze_project()` — jeśli brak toon, uruchom `radon cc -j <dir>` jako subprocess i parsuj wyniki

---

### ✅ T009 — Zduplikowane metryki dla tej samej funkcji

**Problem:** Ta sama funkcja może pojawić się jako metryka raz z modułu i raz z alertu, generując dwie osobne decyzje z tym samym targetem.  
**Plik:** `app/analyzers/__init__.py` → `analyze_from_toon_content()`  
**Akcja:** Deduplikacja metryk po `(file_path, function_name)` przed ewaluacją DSL

---

### ✅ T010 — Brak obsługi `duplication.toon` (format `[hash] ! STRU`)

**Problem:** Parser duplikatów szuka `STRU|EXAC` w nawiasach `[`, ale kod2llm generuje:
```
[1899ff8e67d31c77] ! STRU  setup_logging  L=25 N=3 saved=50 sim=1.00
```
Spacja przed `STRU` powoduje, że warunek `"STRU" in stripped` nie działa gdy linia zaczyna się od `[hash]`.  
**Plik:** `app/analyzers/__init__.py` → `ToonParser.parse_duplication_toon()`  
**Akcja:** Poprawić regex by obsługiwał `[hash] ! STRU` format

---

## 🟢 Ulepszenia (jakość i UX)

### T011 — CLI: `redsl analyze` powinien wyświetlać top decyzji DSL od razu

**Problem:** `analyze` wyświetla surowe metryki ale nie decyzje. Użytkownik musi osobno wywołać `explain`. Dwa kroki to za dużo.  
**Akcja:** Połączyć output — po metrikach wyświetlić top 5 decyzji DSL

---

### T012 — Makefile: target `analyze` z konkretnym projektem

**Problem:** Brak wygodnego skrótu do analizy zewnętrznego projektu.  
**Akcja:** Dodać `make analyze PROJECT=/path/to/project` do Makefile

---

### T013 — Obsługa wielu toon plików z jednego katalogu (merge)

**Problem:** Projekty mogą mieć `project.toon` + `analysis.toon` + `duplication.toon`. Teraz tylko pierwszy znaleziony plik per typ jest używany.  
**Akcja:** Łączyć dane z wszystkich dostępnych toon files zamiast wybierać pierwszy

---

### T014 — Raport HTML z wynikami refaktoryzacji

**Problem:** `refactor_output/` zawiera `.py` + `metadata.json` ale nie ma czytelnego podsumowania.  
**Akcja:** Generować `refactor_output/report.md` lub `report.html` z tabelą zmian, CC before/after, reflection notes

---

### T015 — Test integracyjny na prawdziwym projekcie

**Problem:** Testy unit (`tests/`) używają mocków i danych syntetycznych. Brak testu end-to-end na prawdziwym kodzie.  
**Akcja:** Dodać `tests/test_integration.py` — parsuj `code2llm/analysis.toon` i sprawdź że DSL zwraca > 0 decyzji

---

### T016 — `redsl serve` — dokumentacja API w Swagger

**Problem:** FastAPI generuje `/docs` automatycznie ale `redsl serve` nie wyświetla URL po starcie.  
**Akcja:** Wypisać `http://localhost:8000/docs` po uruchomieniu serwera

---

### ✅ T017 — Obsługa `#` header line z metadanymi w toon

**Problem:** Linia `# code2llm | 113f 20532L | python:109 | 2026-03-25` zawiera cenne dane (total files, lines, langs) które są ignorowane przez parser.  
**Akcja:** Parsować komentarz nagłówkowy → uzupełniać `AnalysisResult.total_files`, `total_lines`

---

### T018 — `REFACTOR_LLM_MODEL` nie propaguje do reflection_model

**Problem:** Zmiana `REFACTOR_LLM_MODEL` na openrouter nie aktualizuje `reflection_model` w `AgentConfig.from_env()`.  
**Plik:** `app/config.py` → `AgentConfig.from_env()`  
**Akcja:** ✅ Naprawione w sesji (pole `reflection_model` już czyta `REFACTOR_LLM_MODEL`) — do weryfikacji testem

---

## 📋 Kolejność realizacji

| Priorytet | Ticket | Opis | Status |
|-----------|--------|------|--------|
| 1 | T001 | Parser HEALTH[N] emoji format | ✅ DONE |
| 2 | T002 | Parser LAYERS sekcja | ✅ DONE |
| 3 | T003 | Parser M[N] file,line format | ✅ DONE |
| 4 | T005 | analysis.toon jako project fallback | ✅ DONE |
| 5 | T009 | Deduplikacja metryk | ✅ DONE |
| 6 | T010 | Parser duplication.toon | ✅ DONE |
| 7 | T017 | Header metadata (#project|Nf NL) | ✅ DONE |
| 8 | T004 | Fallback AST/radon gdy brak toon | ✅ DONE |
| 9 | T006 | Parser project.functions.toon YAML | ✅ DONE |
| 10 | T007 | Confidence z LLM | ⏳ next |
| 11 | T008 | Integracja radon/flake8 | ⏳ next |
| 12 | T015 | Test integracyjny na prawdziwym projekcie | ⏳ next |
