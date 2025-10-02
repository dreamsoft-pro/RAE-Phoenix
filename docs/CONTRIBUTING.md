# Przewodnik dla Współtwórców

Witaj w projekcie Feniks! Cieszymy się, że chcesz nam pomóc. Ten przewodnik pokaże Ci, jak możesz rozszerzyć możliwości naszego narzędzia.

## Jak Dodać Nową Recepturę?

Receptury to serce operacji refaktoryzacyjnych. Definiują one, co i jak ma zostać zmienione.

**Krok 1: Stwórz plik YAML**

Stwórz nowy plik z rozszerzeniem `.yml` w katalogu `recipes/` (lub dowolnym innym, który potem wskażesz).

**Krok 2: Zdefiniuj strukturę receptury**

Receptura musi zawierać następujące pola:

*   `name`: Krótka, czytelna nazwa (np. "AngularJS Service to TypeScript Function").
*   `description`: Szczegółowy opis zadania, który zostanie użyty w prompcie. Wyjaśnij, co jest celem refaktoryzacji.
*   `language`: Język programowania, którego dotyczy receptura (np. `javascript`, `python`). Kluczowe dla mechanizmu scoringu.
*   `tags`: Lista tagów, które pomagają agentowi dopasować recepturę do kodu. Np. jeśli refaktoryzujesz serwis Angular, dodaj tagi `service` i `angularjs`.
*   `prompt_template`: Szablon promptu dla LLM. Musi zawierać zmienne `{code}`, `{file_path}` i `{description}`.

**Przykład: `recipes/angularjs-service-to-ts-function.yml`**

```yaml
name: "AngularJS Service to TypeScript Function"
description: "Przekształć poniższy serwis AngularJS w czystą, eksportowalną funkcję TypeScript. Zachowaj logikę biznesową, ale usuń wszystkie zależności od Angulara. Funkcja powinna przyjmować niezbędne zależności jako argumenty."
language: "javascript"
tags:
  - "angularjs"
  - "service"
  - "typescript"
  - "refactor"
prompt_template: |
  ### ZADANIE
  Opis: {description}
  Plik: `{file_path}`

  ### ORYGINALNY KOD (AngularJS Service)
  ```javascript
  {code}
  ```

  ### INSTRUKCJE
  1. Przeanalizuj powyższy kod serwisu AngularJS.
  2. Zidentyfikuj kluczową logikę biznesową.
  3. Napisz nową funkcję w TypeScript, która realizuje tę samą logikę.
  4. Usuń wszystkie elementy związane z Angularem (`.service`, `.factory`, wstrzykiwanie zależności przez `$inject`).
  5. Zadbaj o odpowiednie typowanie w TypeScript.

  ### ZREFRAKTORYZOWANY KOD (TypeScript Function)
```

## Jak Stworzyć Nową Wtyczkę Językową?

Wtyczki pozwalają Feniksowi rozumieć i modyfikować kod w różnych językach.

**Krok 1: Utwórz szkielet wtyczki**

Przejdź do pliku `feniks/plugins.py` i dodaj nową klasę dziedziczącą po `BasePlugin`. Musisz zaimplementować dwie metody: `get_trees` i `transform`.

**Przykład szkieletu dla języka Go:**

```python
# W feniks/plugins.py

# ... (istniejące importy)
from tree_sitter import Language, Parser
# Potrzebujesz parsera dla danego języka, np. pip install tree-sitter-go

# ... (istniejące klasy wtyczek)

class GoPlugin(BasePlugin):
    def __init__(self):
        # W przyszłości można tu załadować parser Tree-sitter dla Go
        # GO_LANGUAGE = Language('build/my-languages.so', 'go')
        # self.parser = Parser()
        # self.parser.set_language(GO_LANGUAGE)
        print("GoPlugin initialized (implementacja w toku)")

    def get_trees(self, code: str):
        """
        Parsuje kod Go i zwraca jego reprezentację AST.
        """
        # TODO: Zaimplementować parsowanie za pomocą tree-sitter lub innego narzędzia
        # return self.parser.parse(bytes(code, "utf8"))
        raise NotImplementedError("Parsowanie dla Go nie zostało jeszcze zaimplementowane.")

    def transform(self, original_code: str, new_code_suggestion: str):
        """
        Integruje sugestie LLM z oryginalnym kodem.
        """
        # TODO: Zaimplementować logikę transformacji AST
        raise NotImplementedError("Transformacja dla Go nie została jeszcze zaimplementowana.")

```

**Krok 2: Zarejestruj wtyczkę**

W tym samym pliku (`feniks/plugins.py`), dodaj swoją nową klasę do funkcji `get_plugin`:

```python
# W funkcji get_plugin(language: str)

    # ...
    elif language == "javascript":
        return JavaScriptPlugin()
    elif language == "go":
        return GoPlugin()
    else:
        raise ValueError(f"Unsupported language: {language}")
```

## Jak Uruchomić Testy?

Aby upewnić się, że Twoje zmiany nie zepsuły istniejącej funkcjonalności, uruchom testy. Projekt używa `pytest`.

**Krok 1: Zainstaluj zależności**

Upewnij się, że masz zainstalowane wszystkie zależności deweloperskie:
```bash
pip install -r requirements.txt
pip install pytest
```

**Krok 2: Uruchom testy**

Z głównego katalogu projektu wykonaj polecenie:
```bash
pytest
```

Jeśli wszystko jest w porządku, testy powinny przejść pomyślnie.
