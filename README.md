# Gaz dla Przemysłu · P1.2

Wybrany kierunek C: redakcyjny, ciepłe tło, butelkowa zieleń, Source Serif 4 i Source Sans 3. Blocksy free z wordpress.org, `gdp-child`, wyłącznie bloki core, bez Companion i innych wtyczek. Dokument zleceniodawcy z 13.09.2026 jest nadrzędny.

## Stan dostarczenia

Publiczne repozytorium oraz wymagany link `playground.wordpress.net/?blueprint-url=...` nie zostały dostarczone. Agent nie ma własnego konta publikacyjnego. Nie użyto infrastruktury ani kont zleceniodawcy. Lokalny test CLI nie jest dowodem uruchomienia publicznego linku.

`dist/etap1-v0.1.zip` jest odtwarzalnym Blueprint Bundle: `blueprint.json`, `gdp-child.zip` i `site.wxr`. `blueprints/main.json` wykorzystuje zasoby `bundled`, dlatego sam JSON bez towarzyszących zasobów nie jest przenośnym publicznym adresem uruchomienia.

## Odtworzenie lokalne

Wymagane: Node 20+, npm, Python 3. Docker nie jest używany. Wersje narzędzi zapisano w `package-lock.json`; konfiguracja WordPress pozostaje `latest`, PHP `8.3`, zgodnie z briefem.

```sh
npm ci
python3 scripts/build.py
node scripts/validate-blueprints.mjs
npx wp-playground-cli server --blueprint=dist/main \
  --blueprint-may-read-adjacent-files --port=9403 --workers=1
```

Generator od P1.2 rozwija tylko C. Pozostałe kierunki odtwarza się z niezmienionych historycznych tagów, nie przez generator `main`. Zimny start kończy się po zakończeniu importu i wyrenderowaniu strony, nie w chwili otwarcia portu.

Źródłem treści są pliki `content/pages`, `content/posts`, `content/patterns`. `build-wxr.py` waliduje je i składa WXR. `generate-content.py` jest narzędziem odtworzenia początkowej treści roboczej P1.2; nie uruchamia się automatycznie podczas zwykłego builda, aby nie nadpisywać późniejszych ręcznych poprawek.

## Repozytorium z Git bundle

```sh
git clone gaz-dla-przemyslu-repo.bundle gaz-dla-przemyslu
cd gaz-dla-przemyslu
git checkout etap1-v0.1
npm ci
python3 scripts/build.py
```

Tagi `etap1-A/B/C` zachowują P1.1. `main` i `etap1-v0.1` obejmują wybrane C oraz pełną mapę P1.2. Są to rzeczywiste tagi lokalnego Git, nie opublikowanego remote.

## Architektura

- Jedno źródło tokenów: `config/tokens.json`; z niego powstają `theme.json` oraz paleta Customizera. Aktywne ustawienia są w `theme_mods_gdp-child`, z lustrem `theme_mods_blocksy`.
- Nagłówek i stopka pochodzą z free builderów Blocksy. Treść stopki to widgety bloków core; dane podmiotu pozostają placeholderami.
- `/wiedza/` jest stroną wpisów, której bloki renderuje child `home.php`. Query Loop i wyszukiwarka są natywne.
- Wszystkie wpisy mają adres `/wiedza/<slug>/`. Opcja permalinków pozostaje `/%postname%/`; child dodaje regułę i filtr odnośników.
- `/komentarz-rynkowy/` jest archiwum kategorii. `category.php` renderuje edytowalny wzorzec strony; inne kategorie korzystają z `archiwum-kategorii`.
- Błąd 404 wykorzystuje filtr Blocksy i treść strony `blad-404`. Szablony PHP nie zawierają tekstów biznesowych.
- Sekcje układu są nazwane po polsku i blokowane `contentOnly`. Redaktor nie przesuwa sekcji. Wyjątek: nazwana „Treść artykułu” umożliwia dodanie akapitu i tabeli, wymagane w sekcji 14 briefu. Blokady sprawdzane są też na core REST save.
- Nadpisania wzorców korzystają z `core/pattern-overrides`. Dla `core/details.summary` child włącza obsługiwany filtr core 6.9+, bez własnego bloku i bez wtyczki.
- Fonty są lokalne WOFF2 latin/latin-ext z licencjami. Brak osadzonych map, CDN i Google Fonts.
- Sloty nie przyjmują plików ani danych, nie wykonują obliczeń i nie wysyłają wiadomości. Ich przyciski prowadzą do `/kontakt/`. Funkcje M1–M9 należą do etapu 4.

## Import i bezpieczniki

Importer jest jednorazowym skryptem core API dla kontrolowanego WXR projektu, uruchamianym przez `runPHP`. Nie jest wtyczką. Wbudowany `importWxr` instaluje importer WordPress, dlatego nie jest stosowany przy twardym zakazie wtyczek. Obrazy są placeholderami; importer odmawia obcych typów i nie deklaruje obsługi mediów.

Skrypty wymagają `GDP_PROTOTYPE` i świeżej instancji. Nigdy nie uruchamiać ich na istniejącej stronie. Usuwanie domyślnych wpisów i przykładowych wtyczek dotyczy tylko jednorazowego Playground.

Loginy demonstracyjne: Administrator `admin` / `password`; Redaktor `redaktor` / `GDP-prototyp-2026`. To dane publicznego prototypu, nie kont użytkownika. Nie stosować na hostingu.

## Weryfikacja

- `docs/qa/inventory-p12.md`: zakres i scenariusze testów.
- `scripts/verify-blocks.php`: audyt bazy WordPress; testowy blueprint zapisuje `gdp-audit.json`.
- `scripts/qa-p12.mjs`: front, adresy, responsywność, hosty, axe-core i interakcje.
- `docs/qa/p12-browser.json`: surowe wyniki frontu i dostępności.
- `docs/qa/schema-p12.json`: JSON Schema.
- `docs/screenshots/p12`: widoki 360×800, 768×1024 i 1440×900.
- `docs/test-edycji.md`: ilustrowany test dla zleceniodawcy.
- `docs/open-items.md`: kanoniczne wystąpienia placeholderów.
- `docs/P1.2.md`: krótki raport kontrolny, z ograniczeniami odbioru.

Po buildzie uruchom instancję testową zamiast zwykłej, aby włączyć logowanie i zapisać audyt importu:

```sh
npx wp-playground-cli server --blueprint=.runtime/test-main \
  --blueprint-may-read-adjacent-files --port=9403 --workers=1
```

W drugim terminalu: `npx playwright install chromium`, następnie `node scripts/run-qa-p12.mjs`. Skrypt sprawdza front i serializację; nie zastępuje operacji edycji opisanych w instrukcji. Używa wyłącznie kont demonstracyjnych świeżej instancji i portu 9403.

## Publikacja i kolejne etapy

Po uzyskaniu legalnej możliwości publikacji na własnym koncie agenta trzeba opublikować zasoby, przygotować URL-owy blueprint wskazujący pliki na tagu i przetestować dokładny link Playground aż do wyrenderowanej strony głównej. Bundle ani zrzut lokalny nie zastępują tego testu.

P1.2 jest punktem na uwagi. P1.3 obejmie uzgodnione poprawki. Dopiero pisemna akceptacja P1.4 i odrębne nadanie dostępów umożliwiają etap 2. Nie wykonano wdrożenia, konfiguracji infrastruktury ani instalacji wtyczek. Procedura odtworzenia na hostingu jest osobnym elementem zamknięcia P1.4.
