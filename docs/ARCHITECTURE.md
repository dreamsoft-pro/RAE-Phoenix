# Architektura Projektu Feniks

Feniks został zaprojektowany jako elastyczny i rozszerzalny silnik do refaktoryzacji kodu, napędzany przez duże modele językowe (LLM). Jego architektura opiera się na wtyczkach i recepturach, co pozwala na łatwe dostosowanie do różnych języków programowania i zadań.

## Główne Komponenty

Architektura składa się z czterech głównych komponentów:

1.  **Silnik (Engine)**: Centralna część aplikacji, która orkiestruje całym procesem refaktoryzacji.
2.  **Baza Wektorowa (Vector Database)**: Przechowuje fragmenty kodu (chunki) w postaci wektorowej, umożliwiając szybkie i semantyczne wyszukiwanie.
3.  **Wtyczki Językowe (Plugins)**: Moduły specyficzne dla danego języka programowania, odpowiedzialne za analizę i transformację kodu (np. operacje na Abstrakcyjnym Drzewie Składni - AST).
4.  **Receptury (Recipes)**: Pliki konfiguracyjne YAML, które definiują konkretne zadanie refaktoryzacji, zawierając m.in. szablony promptów dla LLM.

## Przepływ Danych (Data Flow)

Proces refaktoryzacji przebiega następująco:

1.  **Inicjacja**: Użytkownik uruchamia agenta (`scripts/refactor_agent.py`) z zapytaniem (`--query`) opisującym, jaki kod chce znaleźć, oraz ścieżką do receptury lub katalogu z recepturami (`--recipe`).

2.  **Wyszukiwanie**: Silnik wysyła zapytanie do bazy wektorowej (Qdrant), aby znaleźć najbardziej pasujące fragmenty kodu.

3.  **Wybór Narzędzi (Dla każdego fragmentu kodu)**:
    a. **Wybór Receptury**: Jeśli jako argument podano katalog, silnik ocenia wszystkie receptury w tym katalogu i wybiera tę z najwyższym wynikiem dopasowania do aktualnego fragmentu kodu. Oceniane są m.in. tagi i zgodność języka.
    b. **Wybór Wtyczki**: Na podstawie metadanych fragmentu kodu (pola `language`), silnik dynamicznie ładuje odpowiednią wtyczkę językową (np. `PythonPlugin` dla kodu w Pythonie).

4.  **Generowanie Prompta**: Silnik używa szablonu z wybranej receptury (`prompt_template`) i wstawia w niego treść fragmentu kodu, aby stworzyć precyzyjny prompt dla modelu LLM.

5.  **Interakcja z LLM**: Prompt jest wysyłany do modelu językowego, który zwraca sugestię zrefaktoryzowanego kodu.

6.  **Transformacja i Zastosowanie Zmian (w przygotowaniu)**:
    *   Odpowiedź LLM wraz z oryginalnym kodem jest przekazywana do wtyczki językowej.
    *   Wtyczka parsuje oba fragmenty kodu do postaci AST, a następnie próbuje zintegrować zmiany w sposób bezpieczny i składniowo poprawny.
    *   Zmiany są zapisywane z powrotem do pliku źródłowego.

Dzięki tej modułowej architekturze, dodanie wsparcia dla nowego języka programowania lub nowego rodzaju refaktoryzacji sprowadza się do stworzenia odpowiedniej wtyczki i receptury, bez potrzeby modyfikacji głównego silnika.
