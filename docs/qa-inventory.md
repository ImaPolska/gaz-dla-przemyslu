# Zakres testów P1.1

- Identyczny SHA256 WXR w A/B/C i identyczne drzewo bloków.
- Każdy kierunek: schemat Blueprint, świeży start CLI, HTTP 200 strony głównej i cena-stala oraz stubów.
- Brak wtyczek projektu, motyw aktywny gdp-child, rodzic blocksy, PHP 8.3 i zanotowana wersja WP.
- Pełny audyt post_content page/post/wp_block przez parser core: bloki zakazane, obcy namespace, shortcode z wyłączeniem literalnych placeholderów [[ ]], jeden h1 na stronie, contentOnly i polska nazwa każdej sekcji.
- Odczyt debug.log po zapytaniach, zero notice/warning/fatal.
- Główny CTA, link cena stała, otwieranie i zamykanie FAQ, hamburger oraz powrót na stronę główną.
- Widoki 1440×900 i 360×800 obu stron na każdym kierunku: dwanaście zrzutów; pomocniczo 768×1024.
- Brak overflow strony, CTA nad linią zgięcia; tabela przewija się we własnym kontenerze.
- Fonty i zasoby frontendu tylko z własnego hosta; oddzielić zasoby startowe instalatora.
- Dodatkowe przypadki: bardzo wąski viewport oraz wejście bezpośrednio na permalink produktu po świeżym starcie.
- Nie zaliczać publicznego linku na podstawie lokalnego CLI. Publiczny link wymaga świeżego uruchomienia playground.wordpress.net z rzeczywistym publicznym blueprint-url na tagu.
