# Historia zmian

## 2026-09-13 · P1.0 i P1.1

- Odczytano pełny dokument nadrzędny oraz sześć wymaganych procedur WordPress/agent-skills.
- Utworzono lokalne repo Git; stwierdzono brak własnego konta agenta do publicznej publikacji.
- Wybrano Playground CLI i headless Chromium, bez Docker, dostępów użytkownika i wtyczek projektu.
- Utworzono A: przemysłowy, B: kontraktowy, C: redakcyjny na wspólnym WXR i strukturze bloków.
- Dodano child theme, tokeny, fonty lokalne, konfigurację builderów, menu i blokowych widgetów.
- Dodano generator WXR, kontrolowany importer core API, setup, audyt bloków, walidację schematu i testy przeglądarkowe.
- Usunięto cache domyślnych kolorów Blocksy po imporcie; poprawiono podwójne marginesy sekcji i kontrast obrysowego CTA w B.
- Sprawdzono serializację wszystkich 16 obiektów przez Gutenberg. Zapisano 12 zrzutów.
- Nie wykonano publikacji remote ani testu publicznych linków. Nie rozpoczęto P1.2.

## 2026-09-13 · P1.2 · etap1-v0.1

- Po wyborze C rozwijano tylko ten kierunek; A/B/C pozostają niezmienionymi tagami historycznymi.
- Zbudowano pełną mapę: 26 stron wraz z pomocniczymi źródłami szablonów, pięć artykułów i dwa komentarze-szablony.
- Dodano dziesięć wzorców zsynchronizowanych, osiem starterów, docelowe menu, stopkę i statyczne sloty.
- Dodano routing wpisów i archiwów oraz polskie wyniki wyszukiwania oparte na post_content i core Query Loop.
- Zweryfikowano pytania i odpowiedzi FAQ jako osobne nadpisania, oba pola CTA oraz propagację zastrzeżenia cen do treści i stopki.
- Przeprowadzono trzy operacje edycji: zapis nagłówka, akapit i tabela 3×3, blokady Redaktora i przesunięcie sekcji przez Administratora. Próba naruszenia układu przez REST otrzymała 403.
- Dopuszczono startery w nowym auto-draft Redaktora i zablokowano kolejność po pierwszym zapisie.
- Poprawiono szerokość tekstu artykułu, font nagłówków edytora i sprawdzono w pełni otwarte menu mobilne.
- Zarejestrowano 400 kanonicznych wystąpień placeholderów; bez danych cenowych, koncesji czy fikcyjnych klientów.
- Dołączono audyt, zrzuty w trzech rozdzielczościach, instrukcję edycji i odtwarzalny Blueprint Bundle.
- Nadal nie dostarczono publicznego repo ani linku Playground. Nie deklaruje się pełnego odbioru P1.2 ani akceptacji etapu 1.

## 2026-09-14 · Publiczne udostępnienie P1.2

- Po zatwierdzeniu przez zleceniodawcę utworzono publiczne repozytorium na koncie ImaPolska.
- Opublikowano oryginalne tagi A/B/C i `etap1-v0.1`, bez przepisywania historii.
- Dodano tag `etap1-v0.1-public` z publicznym punktem uruchomienia JSON. Nie zmieniono treści, motywu, konfiguracji ani progu `[[X]]`.
- Sprawdzono cztery dokładne publiczne linki w świeżych kontekstach: wszystkie uruchamiają stronę główną bez interwencji.
- Pełny C: 41 adresów, prawidłowe końcowe statusy, jeden H1; kanoniczne przekierowanie strony głównej odnotowane.
- Wszystkie cztery instancje: zero wtyczek, zakazanych bloków, błędów JavaScript i zapisów debug.log. Sprawdzono też strony ceny stałej i wykonano 16 nowych zrzutów.
- Uaktualniono raport, instrukcję i rejestr otwartych pozycji. Odbiór przez zleceniodawcę nadal pozostaje punktem kontrolnym P1.2.
