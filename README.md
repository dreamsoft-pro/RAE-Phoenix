# Feniks: Inteligentny Silnik do Refaktoryzacji Kodu

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Feniks to uniwersalne i rozszerzalne narzędzie, które wykorzystuje moc dużych modeli językowych (LLM) do automatyzacji procesu refaktoryzacji kodu. Dzięki architekturze opartej na wtyczkach i recepturach, Feniks może być łatwo dostosowany do pracy z dowolnym językiem programowania i szerokim zakresem zadań modernizacyjnych.

## Główne Cechy

- **Wsparcie dla Wielu Języków**: Elastyczny system wtyczek pozwala na łatwe dodawanie wsparcia dla nowych języków programowania.
- **Sterowanie przez Receptury**: Zadania refaktoryzacji są definiowane w prostych plikach YAML, co pozwala na precyzyjne sterowanie procesem bez zmiany kodu silnika.
- **Inteligentne Wyszukiwanie**: Wykorzystuje wektorową bazę danych (Qdrant) do semantycznego wyszukiwania fragmentów kodu, które wymagają refaktoryzacji.
- **Dynamiczne Dopasowanie Narzędzi**: Agent automatycznie dobiera najlepszą recepturę i wtyczkę językową do znalezionego kodu.
- **Otwarty na Rozwój**: Zaprojektowany z myślą o społeczności – dodawanie nowych funkcji jest proste i dobrze udokumentowane.

## Architektura

Feniks opiera się na modułowej architekturze, która oddziela logikę orkiestracji od specyfiki języków i zadań.

Szczegółowy opis komponentów i przepływu danych znajdziesz w dokumencie [**ARCHITECTURE.md**](docs/ARCHITECTURE.md).

## Pierwsze Kroki

*(Ta sekcja zostanie rozwinięta w przyszłości o instrukcje instalacji i użytkowania)*

## Jak Współtworzyć Projekt?

Chcesz pomóc w rozwoju Feniksa? Świetnie! Stworzyliśmy przewodnik, który krok po kroku wyjaśnia, jak dodawać nowe receptury, wtyczki językowe i jak weryfikować swoje zmiany.

Zapoznaj się z naszym [**Przewodnikiem dla Współtwórców**](docs/CONTRIBUTING.md).

## Licencja

Projekt jest udostępniany na licencji MIT. Zobacz plik `LICENSE`, aby uzyskać więcej informacji.
