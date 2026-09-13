# Gaz dla Przemysłu · P1.1

Prototyp WordPress: Blocksy free z wordpress.org, `gdp-child`, wyłącznie bloki core. Dokument zleceniodawcy z 13.09.2026 jest nadrzędny. Zrealizowany zakres roboczy: trzy kierunki, wspólna strona główna i `/oferta/cena-stala/`; pomocnicze adresy są oznaczonymi stubami, nie pełnym P1.2.

## Stan dostarczenia

**Publiczne repozytorium i publiczne linki `?blueprint-url=...` nie zostały dostarczone.** Agent nie ma własnego konta publikacyjnego. Nie użyto kont ani infrastruktury użytkownika i nie poproszono o dostęp. Lokalne testy CLI nie dowodzą uruchomienia linku na playground.wordpress.net.

`dist/etap1-A.zip`, `dist/etap1-B.zip`, `dist/etap1-C.zip` są pakietami źródłowymi Blueprint Bundle. W środku każdy ma `blueprint.json`, `gdp-child.zip` i identyczny `site.wxr`. `blueprints/A.json` itp. używają zasobów `bundled`; same JSON-y bez plików ZIP/WXR nie są publicznymi linkami do uruchomienia. Nie wysyłamy fikcyjnych adresów.

## Środowisko i start lokalny

Wymagane Node 20+, npm i Python 3. Git jest źródłem prawdy. Testowano Playground CLI 3.1.53; WordPress `latest` rozwiązał się do 7.1, PHP 8.3 do 8.3.33. Docker nie jest używany.

```sh
npm ci
python3 scripts/build.py --active A
node scripts/validate-blueprints.mjs
npx wp-playground-cli server --blueprint=dist/A \
  --blueprint-may-read-adjacent-files --port=9400 --workers=1
```

`--workers=1` ogranicza koszt izolowanego testu, lecz CLI ostrzega przed ryzykiem blokad przy dużej współbieżności. Testy wykonują żądania kolejno. Po komunikacie o nasłuchiwaniu należy poczekać na zakończenie importu i HTTP 200, nie traktować samego otwarcia portu jako gotowej strony.

Analogicznie `dist/B` i `dist/C`. Aby zbudować tylko nowy wariant aktywny w źródłach, użyj `python3 scripts/build.py --active B` lub `C`. Skrypt zawsze buduje wszystkie trzy pakiety, a `theme/gdp-child` i `dist/gdp-child.zip` wskazują wariant aktywny.

## Odtworzenie repozytorium z załączonego Git bundle

```sh
git clone gaz-dla-przemyslu-repo.bundle gaz-dla-przemyslu
cd gaz-dla-przemyslu
git checkout etap1-A  # analogicznie etap1-B / etap1-C
npm ci
```

Tagi są lokalnymi, rzeczywistymi obiektami Git, nie tagami opublikowanego remote. W dostarczonym archiwum źródeł znajduje się stan `main` z A jako wariantem technicznym; nie oznacza to wyboru kierunku.

## Zasady techniczne

- Jedno WXR i identyczna struktura bloków A/B/C. Zmieniają się tokeny, fonty, CSS i ustawienia prezentacyjne.
- `config/tokens.json` generuje `theme.json` i zgodną paletę Blocksy. Nagłówek i czterokolumnowa stopka pochodzą z free builderów; widgety stopki są blokami core.
- Fonty WOFF2 latin/latin-ext są w `assets/fonts`, z licencjami. Remote Google Fonts jest wyłączony.
- Każda główna sekcja jest nazwaną po polsku grupą z `templateLock: contentOnly`. UI oraz core REST save pilnują układu dla Editor. Nie deklarujemy zaliczenia pełnego testu edycji z P1.2.
- Siedem `wp_block` jest importowanych jako wzorce zsynchronizowane. CTA ma działające nadpisania tytułu i podtytułu; FAQ używa natywnych Details.
- Formularze i upload to oznaczone, nieaktywne sloty. Przyciski prowadzą do kontaktu. Nie ma wysyłania danych, poczty, HubSpot, endpointów biznesowych ani wtyczek projektu.
- Skrypt importu WXR jest ograniczony do własnego, kontrolowanego formatu i uruchamia core API przez `runPHP`. Nie jest uniwersalnym importerem; nie obsługuje zewnętrznych załączników. To jawne odstępstwo od `importWxr`, którego kompilator instalowałby zakazaną wtyczkę importera.
- `GDP_PROTOTYPE` jest wymaganym bezpiecznikiem dla skryptów czyszczących wyłącznie jednorazową instancję Playground. Nie uruchamiać ich na istniejącej stronie.
- Login demonstracyjny Administrator: `admin` / `password`; Redaktor: `redaktor` / `GDP-prototyp-2026`. To publiczne dane prototypu, nie dane użytkownika. Nigdy nie stosować na hostingu.

## Weryfikacja i pliki

- `docs/qa/browser-runtime.json`: 10 lokalnych tras dla każdego kierunku, pomiary dwóch stron w trzech rozdzielczościach, hosty, błędy JS i testy odczytowe interakcji.
- `docs/qa/gutenberg-serialization.json`: rzeczywista walidacja `wp.blocks.parse` dla 16 obiektów w edytorze.
- `docs/qa/schema.json`: walidacja opublikowanego schematu.
- `docs/screenshots`: 12 pełnych zrzutów, desktop 1440×900 i mobile 360×800; nazwa pliku wskazuje kierunek i stronę.
- `docs/open-items.md`: kanoniczny rejestr placeholderów, z lokalizacjami.
- `docs/decisions.md`, `docs/changelog.md`, `docs/P1.1.md`: decyzje, historia i raport.
- `scripts/verify-blocks.php`: audyt zawartości bazy; testowe blueprinty dopisują wynik do `/gdp-audit.json`.
- `scripts/qa.mjs`: testy w Playwright. Należy przekazać uruchomiony obiekt `browser` do eksportowanej funkcji `run`.

## Publikacja i następny etap

Po uzyskaniu legalnej możliwości publikacji na własnym koncie agenta trzeba umieścić komplet zasobów w publicznym repo, wygenerować URL-owe blueprinty wskazujące pliki na odpowiednich tagach i dopiero wtedy przetestować każdy dokładny adres `https://playground.wordpress.net/?blueprint-url=...` do wyrenderowanej strony głównej. Testów tych nie zastępuje CLI.

P1.2, `main.json`, pełna mapa, pięć artykułów, instrukcja testu edycji oraz pełny audyt 13.3–13.6 czekają na wybór kierunku. Odtworzenie na hostingu przez `restore-on-host.sh` należy dopracować do P1.4. Nie dołączamy obecnie pozornie gotowego skryptu wdrożenia; etap 2 nie został rozpoczęty.
