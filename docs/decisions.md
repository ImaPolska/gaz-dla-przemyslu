# Decyzje i założenia

## 2026-09-13 · P1.0

- Zakres: tylko P1.0–P1.1. Pełna mapa i test edycji artykułów należą do P1.2, po wyborze kierunku.
- Dokument dostarczony w tej rozmowie zastępuje wcześniejsze informacje projektowe. Nie korzystano z pamięci projektu.
- Środowisko: Node 20.20.1, npm 10.8.2, Git 2.53.0; zainstalowano Playground CLI 3.1.53 i Chromium headless przez Playwright. Brak Docker, zatem wp-env nie jest ścieżką wykonania.
- WordPress `latest`, PHP `8.3`. Faktyczną rozwiązaną wersję zapisuje test runtime.
- Załadowano sześć plików SKILL.md z WordPress/agent-skills: wp-block-themes, wp-block-development, wp-rest-api, wp-wpcli-and-ops, blueprint, wp-playground. Commit upstream: `d87ee6916e740c7960b6959220c0481a41b320c7`. Procedury dotyczące własnych bloków/FSE/endpointów nie są wykonywane, ponieważ projekt jest hybrydowym motywem używającym wyłącznie core.
- Publiczne repozytorium: BLOKADA ŚRODOWISKA. Agent nie ma własnego konta GitHub ani uprawnienia publikowania na nim; wykryty connector GitHub użytkownika jest DISCONNECTED. Nie poproszono o połączenie ani dane. Repo lokalne jest prawdziwym repo Git, ale nie zastępuje publicznego URL.
- Paleta: `config/tokens.json` jest źródłem wartości, generator zapisuje zgodne `theme.json` i `theme_mods_A/B/C.json`. Te same slugi `base, contrast, primary, secondary, surface, line, success, warning`. Customizer odpowiada za Header/Footer Builder; edytor za paletę, skalę i odstępy. Test porównuje wartości, nie zakłada zgodności.
- Fonty self-hosted WOFF2: A IBM Plex Sans; B Manrope + Source Sans 3; C Source Serif 4 + Source Sans 3. Zestawy latin i latin-ext, licencje w repo. Brak fontów pobieranych przez przeglądarkę z Google Fonts. Stos systemowy tylko awaryjny.
- Companion: NIE instalować. Nagłówek i stopka są skonfigurowane przez free builder. Sticky/shrink, jeśli natywnie niedostępny bez dodatku, to CSS oraz mały skrypt prezentacyjny motywu potomnego; nie moduł biznesowy.
- Logo: tekstowa nazwa witryny; brak opracowanego znaku, palety A/B/C robocze.
- Bez zdjęć, stocków, fikcyjnych aktywów, liczb i referencji.
- Formularze są statycznymi blokami core, oznaczone jako prototyp i nie przyjmują danych. CTA modułów prowadzą do `/kontakt/`. „24 h” pochodzi wyłącznie z briefu i jest celem roboczym do potwierdzenia, nie wynikiem pomiaru.
- Domyślny brak GUD-K, domyślna lista produktów zgodna z 1.3; bez pytań do użytkownika.
- Konflikt `importWxr` / zero wtyczek: w Playground CLI 3.1.53 kompilator wstawia `installPlugin wordpress-importer` bezwarunkowo przed krokiem `importWxr` (plik upstream blueprints/index.js, fragment 14469–14479). Zachowujemy twardy zakaz wtyczek. Skrypt `scripts/import-wxr.php` importuje nasz ograniczony, kontrolowany WXR przez core WordPress API, uruchamiany `runPHP`; nie jest wtyczką i nie jest kodem motywu. To jawne odstępstwo od dosłownego kroku z 11.1. Brak załączników w P1.1, więc nie ma pobierania obrazów.
- SQLite i pliki runtime dodane przez sam Playground są infrastrukturą Playground, nie wtyczkami projektu. Raport wymienia je oddzielnie od zainstalowanych wtyczek aplikacyjnych.
- P1.1 sprawdza dwa docelowe URL oraz pomocnicze stuby. Nie oznaczamy całej mapy P1.2 jako zaliczonej.
- Pierwszy test A wykrył stary transient `blocksy_dynamic_styles_descriptor` utworzony przed importem konfiguracji. Samo `db->wipe_cache()` nie wystarcza. Setup usuwa transient i wywołuje `blocksy:dynamic-css:refresh-caches`. To usuwa konflikt z domyślnym niebieskim; nie mnożymy palet ani nie maskujemy błędu inline CSS.
- Wersja `latest` rozwiązała się w pierwszym teście do WordPress 7.1; PHP 8.3.33. Wymagany ruchomy `latest` pozostaje w blueprintach, więc przyszłe uruchomienia mogą dostać inną wersję.
- Komponent Site Title w Header Builderze jest natywną tekstową nazwą witryny Blocksy, a nie dosłownym blokiem core/site-title. Zapisane ustawienia nie dodają drugiego H1. To jawna interpretacja hybrydowego nagłówka.
- P1.1 wykorzystuje referencje do tymczasowych stubów lub kotwic zamiast pozornie gotowych podstron P1.2. Pełne drzewo docelowe URL pozostaje do P1.2.

## Dokumentacja techniczna

- [Procedury WordPress](https://github.com/WordPress/agent-skills)
- [Kroki Blueprint](https://wordpress.github.io/wordpress-playground/blueprints/steps/)
- [Przykłady Blueprint](https://wordpress.github.io/wordpress-playground/blueprints/examples/)
- [Treść dla demonstracji](https://wordpress.github.io/wordpress-playground/guides/providing-content-for-your-demo/)
- [Diagnostyka](https://wordpress.github.io/wordpress-playground/blueprints/troubleshoot-and-debug/)
- [Dokumentacja Blocksy](https://creativethemes.com/blocksy/docs/)
# Wybór kierunku C i P1.2

- 2026-09-13: zleceniodawca napisał „Wybieram kierunek C”. `main` rozwija wyłącznie C; tagi `etap1-A`, `etap1-B`, `etap1-C` pozostają niezmienione.
- Wszystkie adresy produktów i narzędzi zastępują skróty P1.1. CTA w nagłówku prowadzi do `/wgraj-fakture/`, a przyciski atrap do `/kontakt/`.
- `/wiedza/` pozostaje stroną wpisów WordPress. `home.php` renderuje jej `post_content`, dzięki czemu wyszukiwarka, kategorie i Query Loop pozostają edytowalnymi blokami core.
- Permalinki w opcji WordPress pozostają `/%postname%/`; routing i filtr odnośnika wpisu dodają prefiks `/wiedza/` wymagany mapą. `/komentarz-rynkowy/` jest rzeczywistym archiwum kategorii, nie osobną listą ręczną.
- Jedyny wyjątek od blokady wnętrza sekcji dotyczy prozy artykułu. Sekcja 14 wymaga dodawania akapitu i tabeli przez Redaktora; nagłówki i CTA pozostają sekcjami układu. Zakres wyjątku podlega testowi.
- Brak własnego konta publikacyjnego nadal blokuje wymagane publiczne repo i link Playground. Nie proszę o dostępy zleceniodawcy, nie używam innego hostingu podglądu i nie uznaję lokalnego testu za publiczny link.
