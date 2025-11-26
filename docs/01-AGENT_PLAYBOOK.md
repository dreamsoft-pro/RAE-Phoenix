4. AGENT_PLAYBOOK.md**

```md
# AGENT PLAYBOOK  
**Jak agent AI ma pracować z projektem Feniks?**

Ten dokument pozwala Claude/Gemini/GPT bezpiecznie wykonywać refaktoryzację projektu.

---

# 📌 Zasady ogólne

1. **Nigdy nie zmieniaj publicznych kontraktów**  
   - pliki w `core/models/*` są stabilne.

2. **Nie zmieniaj katalogów**  
   - struktura repozytorium jest stała.

3. **Nie wprowadzaj black boxów**  
   - każdy moduł ma być testowalny.

4. **Zawsze dodaj test**  
   - każda zmiana → test unit / integration.

5. **Nie zależ od konkretnego LLM**  
   - logika w `core/` nie może używać API LLM.

---

# 📌 Główne obszary pracy

### 1. Refaktoryzacja kodu
- rozbijanie modułów,
- usuwanie duplikacji,
- poprawa jakości.

### 2. Dodawanie testów
- unit,
- integration,
- e2e.

### 3. Uzupełnianie dokumentacji
- opis modułów,
- opis flow,
- diagramy.

### 4. Optymalizacja pętli refleksji
- poprawa algorytmów,
- uproszczenia,
- lepsza ergonomia.

---

# 📌 Wzorzec pracy dla agenta

### 1. Znajdź moduł
Search:  
„Znajdź plik X odpowiedzialny za Y”.

### 2. Przeczytaj kod
Wyodrębnij funkcje, klasy, zależności.

### 3. Zaproponuj refaktoryzację
W formacie:
- problem,
- zmiana,
- korzyść.

### 4. Wprowadź zmiany krokami
Małe PR-y:
- maks 1–3 pliki na zmianę,
- 1 temat per commit.

### 5. Dodaj test
Test musi pokryć:
- typowe dane,
- edge cases.

### 6. Aktualizuj docs
Jeśli zmieniłeś zachowanie: opis w docs.

### 7. Weryfikacja CI
Uruchom:
pytest

yaml
Skopiuj kod
Upewnij się, że wszystko przechodzi.

---

# 📌 Co agent ma DOKŁADNIE robić?

### ✔ Refaktoryzować moduły
### ✔ Dodawać testy
### ✔ Uzupełniać dokumentację
### ✔ Dodawać przykłady użycia
### ✔ Optymalizować algorytmy

### ❌ Nie zmieniać publicznych API
### ❌ Nie zmieniać struktury katalogów
### ❌ Nie pisać kodu bez testów
### ❌ Nie usuwać komentarzy dokumentacyjnych

---