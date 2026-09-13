# Inwentarz weryfikacji P1.2

## Zakres i dowody

- Wszystkie adresy mapy: odpowiedź 200 i jeden H1. Rzeczywisty błąd 404 ma status 404, nie 200. Archiwum kategorii testowane z wpisami i puste.
- Blueprint: JSON Schema oraz zimne uruchomienie lokalnego bundle. Osobno status publicznego linku: niedostarczony.
- Treść: pięć liczników zakazanych bloków/shortcode, blokady sekcji, pięć artykułów, dwa szablony komentarzy, dziesięć wzorców synchronizowanych i osiem starterów.
- Front: strona główna, hub oferty, cena stała, ceny i artykuł; desktop, tablet, mobile; szerokość dokumentu, CTA w nagłówku nad zgięciem, przewijanie tabel w kontenerze.
- Dostępność: axe-core na czterech wymaganych adresach. Osobno klawiatura, skip-link, Details i menu mobilne.
- Nawigacja: podmenu oferty i narzędzi, linki stopki, wyszukiwarka wiedzy, przejście do artykułu i powrót.
- Edycja: Redaktor zmienia tytuł strony głównej; dodaje akapit i tabelę pod drugim nagłówkiem artykułu; nie może usuwać sekcji ani przesuwać kolumn. Administrator może przesunąć całe sekcje i zmienić globalne zastrzeżenie.
- Nadpisania: instancja CTA zmienia tytuł i podtytuł bez zmiany pozostałych. FAQ: pytania i odpowiedzi sprawdzane oddzielnie.
- Zależności: hosty zasobów frontu, błędy JS, nieudane żądania, debug.log PHP.

## Scenariusze brzegowe

- Losowy adres: właściwy status 404, widoczne przejścia do strony głównej i uploadu.
- Wyszukiwanie nieistniejącego słowa i pusta kategoria: czytelny stan pusty, bez fikcyjnego wpisu.
- Próba zmiany układu przez core REST jako Redaktor: odmowa 403, dotychczasowa treść zachowana.
- Zmiany testowe edytora odwracane; źródło prototypu pozostaje w repo.
