#!/usr/bin/env python3
"""Deterministic core-block content for P1.2 C. Preserves the accepted two pages.

Run this file, then build-wxr.py. No WordPress/plugin/API dependencies.
"""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def block(name, html="", attrs=None, dynamic=False):
    attributes = " " + json.dumps(attrs, ensure_ascii=False, separators=(",", ":")) if attrs else ""
    if dynamic:
        return f"<!-- wp:{name}{attributes} /-->\n"
    return f"<!-- wp:{name}{attributes} -->\n{html}\n<!-- /wp:{name} -->\n"


def group(name, body, cls="gdp-section", lock="contentOnly", anchor=None):
    attrs = {"metadata": {"name": name}, "templateLock": lock}
    if cls:
        attrs["className"] = cls
    if anchor:
        attrs["anchor"] = anchor
    return block("group", f'<div class="wp-block-group{(" " + cls) if cls else ""}"'
                 + (f' id="{anchor}"' if anchor else "") + f">\n{body}</div>", attrs)


def p(text, cls=None, binding=None):
    attrs = {}
    if cls:
        attrs["className"] = cls
    if binding:
        attrs["metadata"] = {"name": binding, "bindings": {"__default": {"source": "core/pattern-overrides"}}}
    class_attr = f' class="{cls}"' if cls else ""
    return block("paragraph", f'<p{class_attr}>{text}</p>', attrs)


def h(text, level=2, anchor=None):
    attrs = {"level": level} if level != 2 else {}
    if anchor:
        attrs["anchor"] = anchor
    return block("heading", f'<h{level} class="wp-block-heading"'
                 + (f' id="{anchor}"' if anchor else "") + f">{text}</h{level}>", attrs)


def li(items, ordered=False):
    tag = "ol" if ordered else "ul"
    return block("list", f'<{tag} class="wp-block-list">\n'
                 + "".join(block("list-item", f"<li>{i}</li>") for i in items)
                 + f"</{tag}>", {"ordered": True} if ordered else None)


def table(headers, rows, caption=None, numeric=False):
    cls = "gdp-numeric" if numeric else ""
    html = '<figure class="wp-block-table' + (" " + cls if cls else "") + '"><table class="has-fixed-layout"><thead><tr>'
    html += "".join(f"<th>{x}</th>" for x in headers) + "</tr></thead><tbody>"
    html += "".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows)
    html += "</tbody></table>"
    if caption:
        html += f'<figcaption class="wp-element-caption">{caption}</figcaption>'
    return block("table", html + "</figure>", {"className": cls} if cls else None)


def button(text, url, outline=False):
    cls = " is-style-outline" if outline else ""
    return block("buttons", '<div class="wp-block-buttons">\n'
                 + block("button", f'<div class="wp-block-button{cls}"><a class="wp-block-button__link wp-element-button" href="{url}">{text}</a></div>',
                         {"className": "is-style-outline"} if outline else None) + "</div>")


def ref(id, overrides=None):
    attrs = {"ref": id}
    if overrides:
        attrs["content"] = {key: {"content": value} for key, value in overrides.items()}
    return block("block", attrs=attrs, dynamic=True)


def details(question, answer):
    return block("details", f'<details class="wp-block-details"><summary>{question}</summary>\n'
                 + p(answer) + "</details>")


def section(name, body, priced=False, anchor=None):
    return group(name, h(name) + body + (ref(102) if priced else ""), anchor=anchor)


def hero(title, answer, cta="Wgraj fakturę", url="/wgraj-fakture/", note=None, priced=False):
    return group("Otwarcie: " + title, h(title, 1) + p(answer, "gdp-lead")
                 + (button(cta, url) if cta else "") + (p(note, "gdp-small") if note else "")
                 + (ref(102) if priced else ""), "gdp-section gdp-product-hero")


def sources(items=None):
    return section("Źródła i aktualizacja", li(items or [
        "[[warunki produktu PBM — dokument do zatwierdzenia]]",
        "[[źródło: dokument, wersja i link po weryfikacji merytorycznej]]",
    ]) + p("Ostatnia aktualizacja: [[data]]. Autor: [[autor]].", "gdp-small")
        + p("Materiał roboczy. Zakres oferty i odwołania do źródeł wymagają zatwierdzenia przed publikacją.", "gdp-small"))


def cta(title="Przygotuj dane do rozmowy.", subtitle="Faktura i obecna umowa pozwolą uporządkować pytania o Twój zakup gazu."):
    return group("Następny krok", ref(103, {"Tytuł CTA": title, "Podtytuł CTA": subtitle}), "gdp-section gdp-final")


CONSENT = "[[treść zgody dostarczy zleceniodawca]]. <a href=\"/polityka-prywatnosci/\">Polityka prywatności</a>."
DISTRIBUTION = "Jeżeli PBM nie ma zawartej generalnej umowy dystrybucyjnej z Twoim operatorem, podpiszesz osobno umowę dystrybucyjną; pomożemy w tym."
CAUTION = ("Nie rekomendujemy rozwiązania obecnej umowy przed czasem. Dokument wypowiedzenia jest weryfikowany przez człowieka przed wysyłką. "
           "Skutki błędnego wypowiedzenia, w tym sprzedaż rezerwową i kary, ponosi klient. Dlatego PBM stosuje kolejność: "
           "umowa z PBM → pełnomocnictwo → wypowiedzenie i zgłoszenie do OSD. "
           "Terminy, tryb i skutki dla konkretnej umowy: [[do weryfikacji prawnej]].")
PROTO = "Prototyp: pola są nieaktywne. Przycisk prowadzi do kontaktu i nie przesyła danych."


def consent():
    return p(CONSENT, "gdp-consent")


def warning():
    return section("Zanim wyślesz jakikolwiek dokument", p(CAUTION, "gdp-prototype-note")
                   + p("Wynik porządkowania danych nie jest poradą prawną ani zatwierdzonym wypowiedzeniem. Nie zastępuje oceny całej umowy, aneksów i zasad operatora."))


def form_slot(name, fields, action, intro, extra=""):
    body = h(name) + p(intro)
    body += group("Pola demonstracyjne", "".join(p(f"<strong>{label}</strong> {placeholder}", "gdp-field") for label, placeholder in fields),
                  "gdp-fields")
    return group("Slot: " + name.lower(), body + extra + button(action, "/kontakt/")
                 + p(PROTO, "gdp-prototype-note") + consent(), "gdp-upload")


def query(name, category_ids=None, number=6, market=False, inherit=False):
    q = {"perPage": number, "pages": 0, "offset": 0, "postType": "post", "order": "desc",
         "orderBy": "date", "author": "", "search": "", "exclude": [], "sticky": "exclude", "inherit": False}
    if category_ids:
        q["taxQuery"] = {"category": category_ids}
    if market:
        q["gdpCategory"] = "komentarz-rynkowy"
    if inherit:
        q = {"inherit": True}
    card = (p("[[data]] · " + ("Szablon komentarza" if market else "Artykuł roboczy"), "gdp-data-note")
            + block("post-title", attrs={"level": 3, "isLink": True}, dynamic=True)
            + (p("[[komentarz]]") if market else block("post-excerpt", attrs={"moreText": "Czytaj artykuł"}, dynamic=True))
            + p("Autor: [[autor]]" + (" · Zespół analiz PBM — placeholder" if market else ""), "gdp-author"))
    post_template = block("post-template", group("Karta wpisu", card, "gdp-market-card"))
    empty = block("query-no-results", p("Ta kategoria czeka na pierwszy zatwierdzony materiał. Wróć do bazy wiedzy lub porozmawiaj z PBM."))
    return block("query", '<div class="wp-block-query gdp-market-query">\n' + post_template + empty + "</div>",
                 {"queryId": 2 if market else 3, "query": q, "className": "gdp-market-query"})


def write(folder, slug, content):
    path = CONTENT / folder / (slug + ".html")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def patterns():
    write("patterns", "calculator", form_slot(
        "Kalkulator terminu wypowiedzenia",
        [("Koniec obowiązywania umowy", "[[data z umowy]]"),
         ("Okres wypowiedzenia", "[[wartość i jednostka z umowy]]"),
         ("Klauzula prolongacyjna", "[[pełne brzmienie klauzuli]]"),
         ("E-mail do przypomnienia", "[[adres e-mail — opcjonalnie w przyszłym module]]")],
        "Oblicz termin", "Zestaw dane umowy, zanim ustalisz datę działania. Nie wpisuj danych do prototypu.",
        group("Wynik: karta demonstracyjna", h("Termin do sprawdzenia", 3)
              + p("[[wynik kalkulatora po analizie sposobu liczenia terminu]]")
              + p("Status: oczekuje na sprawdzenie dokumentów. Przypomnienie nie jest ustawiane.", "gdp-small"), "gdp-card")
        + p(CAUTION, "gdp-small")))
    write("patterns", "analysis", form_slot(
        "Analiza umowy",
        [("Umowa i aneksy", "[[miejsce na plik — nieaktywne]]"),
         ("E-mail", "[[adres e-mail]]"), ("NIP", "[[NIP firmy]]")],
        "Prześlij umowę",
        "Docelowy moduł ma wskazać zapisy wymagające uwagi. Nie będzie samodzielnie podejmować decyzji o wypowiedzeniu.",
        h("Co ma odczytać moduł", 3) + li([
            "Strony umowy oraz numery punktów poboru.",
            "Okres obowiązywania i daty dostaw.",
            "Okres wypowiedzenia oraz sposób jego liczenia.",
            "Klauzulę przedłużenia i warunki rezygnacji z prolongaty.",
            "Sposób doręczenia i adresata dokumentów.",
            "Zapisy o wcześniejszym zakończeniu, opłatach i odpowiedzialności.",
        ]) + p(CAUTION, "gdp-small")))
    write("patterns", "advisor", form_slot(
        "Zgłoszenie doradcy",
        [("Imię i nazwisko", "[[imię i nazwisko]]"), ("Firma / NIP", "[[dane doradcy]]"),
         ("E-mail / telefon", "[[dane kontaktowe]]"),
         ("Profil obsługiwanych firm", "[[branże i sposób pracy]]"),
         ("Zakres współpracy", "[[zapytania indywidualne lub portfel klientów]]")],
        "Zgłoś się", "Przedstaw swój model obsługi klientów. Nie przesyłaj danych klientów bez potwierdzenia uprawnienia i zasad przekazania."))
    # Accepted shared patterns: keep their visual structure and supported bindings.
    path = CONTENT / "patterns/final-cta.html"
    text = path.read_text()
    text = text.replace('href="/kontakt/"', 'href="/wgraj-fakture/"')
    text = text.replace("Prototyp: przejdziesz do kontaktu, bez przesyłania pliku.",
                        "Zobacz, jakie dane przygotować. Upload w prototypie jest nieaktywny.")
    path.write_text(text)
    path = CONTENT / "patterns/faq-product.html"
    text = path.read_text()
    question_index = 0
    def question_binding(match):
        nonlocal question_index
        question_index += 1
        attrs = json.loads(match.group(1) or "{}")
        attrs["metadata"] = {"name": f"Pytanie FAQ {question_index}",
                             "bindings": {"__default": {"source": "core/pattern-overrides"}}}
        return "<!-- wp:details " + json.dumps(attrs, ensure_ascii=False, separators=(",", ":")) + " -->"
    text = re.sub(r"<!-- wp:details(?: (\{.*?\}))? -->", question_binding, text)
    path.write_text(text)
    path = CONTENT / "patterns/segments.html"
    text = path.read_text().replace('href="/kontakt/">Zapytaj o gaz dla MŚP', 'href="/dla-kogo/msp/">Zapytaj o gaz dla MŚP')
    text = text.replace('href="/kontakt/">Porozmawiaj o potrzebach zakładu', 'href="/dla-kogo/przemysl/">Porozmawiaj o potrzebach zakładu')
    text = text.replace('href="/kontakt/">Zapytaj o współpracę', 'href="/dla-doradcow/">Zapytaj o współpracę')
    path.write_text(text)


def product_pages():
    products = [
        ("Cena stała", "/oferta/cena-stala/", "Uzgadniasz stawkę paliwa dla opisanego okresu i zakresu. Sprawdź tolerancje wolumenu oraz składniki poza ceną."),
        ("Cena indeksowana TGE", "/oferta/cena-indeksowana-tge/", "Rozliczenie odnosi się do uzgodnionego indeksu. Wybór indeksu, okresu uśredniania i składników ceny musi być zapisany w umowie."),
        ("Model transzowy", "/oferta/model-transzowy/", "Dzielisz ustalanie ceny na części. Potrzebujesz reguł decyzji, harmonogramu i opisu części niezabezpieczonej."),
        ("Umowa kompleksowa dla MŚP", "/oferta/umowa-kompleksowa-msp/", "Zacznij od zakresu obsługi, nie od nazwy umowy. Na start zakładamy osobną umowę dystrybucyjną."),
        ("Biometan — wkrótce", "/oferta/biometan/", "Kierunek rozwoju związany z aktywami Grupy. Dostępność, dokumenty i warunki wymagają potwierdzenia."),
    ]
    cards = group("Karty produktów", "".join(group(title, h(title, 3) + p(desc) + p(f'<a href="{url}">Poznaj model: {title.lower()}</a>'), "gdp-audience-card")
                                                    for title, url, desc in products), "gdp-audience-grid")
    write("pages", "oferta", hero("Wybierz sposób zakupu, nie tylko stawkę.",
          "Oferta gazu dla firmy zaczyna się od Twojego profilu zużycia i sposobu zarządzania ryzykiem. Porównaj cenę stałą, indeks TGE, model transzowy oraz zakres obsługi MŚP. Biometan pozostaje kierunkiem „wkrótce”; warunki produktów wymagają indywidualnego potwierdzenia.", priced=True)
          + section("Modele zakupu gazu", cards, priced=True)
          + section("Porównaj te same cechy", table(
              ["Cecha", "Cena stała", "Indeks TGE", "Transze", "Obsługa MŚP", "Biometan"],
              [["Punkt odniesienia", "Uzgodniona stawka", "Indeks z umowy", "Reguły dla części wolumenu", "Zakres sprzedaży i dystrybucji", "Warunki do określenia"],
               ["Decyzja kupującego", "Akceptacja ceny i okresu", "Akceptacja zmienności", "Zasady i momenty decyzji", "Sprawdzenie dokumentów", "Zgłoszenie zainteresowania"],
               ["Co sprawdzić", "Wolumen i odchylenia", "Indeks i formuła", "Niezamknięta część", "Osobna dystrybucja", "Dokumenty i certyfikacja"],
               ["Warunki liczbowe", "[[ ]]", "[[ ]]", "[[ ]]", "[[ ]]", "Niepublikowane"]]), priced=True)
          + section("Dla kogo który model", li([
              "Planujesz koszt paliwa w budżecie? Porównaj cenę stałą z ryzykiem zmiany zużycia.",
              "Akceptujesz zmienność i śledzisz mechanizm rozliczenia? Omów indeks TGE.",
              "Masz osobę odpowiedzialną za decyzje zakupowe? Sprawdź reguły modelu transzowego.",
              "Chcesz uporządkować dokumenty małej firmy? Zacznij od ścieżki MŚP i ustalenia roli operatora.",
          ]) + p(DISTRIBUTION), priced=True) + sources() + cta())
    product_data = [
        ("cena-indeksowana-tge", "Cena indeksowana TGE. Jasna formuła zamiast domysłów.",
         "Cena indeksowana to model, w którym cena paliwa wynika z uzgodnionego odniesienia rynkowego i składników określonych w umowie. Nie oznacza jednej uniwersalnej stawki TGE. Przed wyborem sprawdź nazwę indeksu, okres obliczeń, datę rozliczenia i pozostałe opłaty.",
         "Gdy akceptujesz zmianę ceny paliwa",
         "Rozważ ten model, gdy potrafisz uwzględnić zmienność kosztów w swojej działalności. Porównaj sezonowość poboru, sposób ustalania cen własnych produktów i dostępność osoby analizującej rozliczenia. Samo obserwowanie pojedynczego notowania nie zastąpi poznania formuły umownej.",
         ["Wybierz dokładne odniesienie: [[indeks lub instrument TGE]].",
          "Ustal okres uśredniania i przypisanie poboru do okresów rozliczenia: [[ ]].",
          "Sprawdź składnik handlowy, bilansowanie i inne elementy formuły: [[ ]].",
          "Uzgodnij sposób udokumentowania wyliczenia na fakturze: [[ ]]."],
         ["Wzrost wartości odniesienia może zwiększyć koszt paliwa zgodnie z formułą.",
          "Różne indeksy i okresy uśredniania nie są tym samym produktem.",
          "Profil sezonowy wpływa na udział poszczególnych okresów w kosztach.",
          "Dystrybucja i inne składniki nie znikają po wyborze indeksu."],
         [("Czy kupuję gaz bezpośrednio na giełdzie?", "Ta strona opisuje model ceny w ofercie PBM, nie samodzielny dostęp klienta do giełdy. Zakres usług i formułę określi umowa."),
          ("Gdzie sprawdzić indeks?", 'Korzystaj z publicznych materiałów <a href="https://tge.pl/">Towarowej Giełdy Energii</a>. Nazwę konkretnego indeksu i właściwe zestawienie potwierdź w umowie: [[link do właściwego indeksu]].'),
          ("Czy indeks musi być tańszy od ceny stałej?", "Nie przyjmuj takiego założenia. Porównanie zależy od okresu, poboru, formuły i pozostałych warunków. Nie publikujemy prognozy ani obietnicy oszczędności.")]),
        ("model-transzowy", "Model transzowy. Decyzje rozłożone na części.",
         "W modelu transzowym cenę ustalasz dla uzgodnionych części zakupu według reguł zapisanych w umowie. Część wolumenu może pozostać rozliczana inaczej. Model wymaga planu poboru, uprawnień do decyzji i jasnego sposobu potwierdzania każdej transzy.",
         "Gdy masz proces podejmowania decyzji",
         "To punkt wyjścia do rozmowy dla firmy, która chce świadomie dzielić ustalanie ceny. Ustal, kto obserwuje rynek, kto akceptuje decyzję i jak zastąpić tę osobę podczas nieobecności. Bez tego podział na transze może utrudnić zarządzanie zakupem zamiast je uporządkować.",
         ["Opisz okres dostaw oraz wolumen do objęcia modelem: [[ ]].",
          "Ustal dopuszczalne części, momenty decyzji i sposób potwierdzania: [[ ]].",
          "Zapisz formułę części, dla której cena nie została ustalona: [[ ]].",
          "Sprawdź rozliczenie odchyleń i zmiany planu produkcji: [[ ]]."],
         ["Podział na transze nie gwarantuje najniższej ceny.",
          "Brak decyzji powinien mieć opisany skutek w umowie, nie pozostawać domysłem.",
          "Zmiana zużycia wymaga sprawdzenia tolerancji i rozliczenia różnic.",
          "Nie porównuj średniej ceny transz bez uwzględnienia ich udziału w rzeczywistym poborze."],
         [("Czy mogę dowolnie zmieniać udział transz?", "Nie zakładaj dowolności. Zasady, dopuszczalne zakresy i sposób zmian będą zapisane w indywidualnych warunkach."),
          ("Kto podejmuje decyzję zakupową?", "Zakres umocowania i sposób akceptacji wymagają uzgodnienia. Prototyp nie zawiera automatu podejmującego decyzje."),
          ("Co z częścią niezamkniętą?", "Jej formułę, okres rozliczenia i skutki braku decyzji trzeba opisać przed zawarciem umowy: [[warunki do zatwierdzenia]].")]),
        ("umowa-kompleksowa-msp", "Gaz dla MŚP. Najpierw ustal zakres umów.",
         "Ścieżka MŚP porządkuje zakup gazu i dokumenty Twojej firmy. Nazwa „umowa kompleksowa” nie przesądza, że PBM zapewni sprzedaż i dystrybucję w jednym dokumencie. Na start zakładamy osobną umowę dystrybucyjną; zakres dla Twojego operatora wymaga potwierdzenia.",
         "Gdy gaz jest ważny, a czas na formalności ograniczony",
         "Piekarnia, suszarnia, przetwórnia czy szklarnia potrzebuje warunków czytelnych dla osoby prowadzącej firmę. Przygotuj fakturę, dane punktu poboru i obecną umowę. Rozmowa powinna wyjaśnić, kto sprzedaje paliwo, kto odpowiada za sieć i jakie dokumenty podpisujesz.",
         ["Wskaż punkt poboru i operatora na podstawie dokumentów.",
          "Porównaj modele ceny dla Twojego zużycia i rytmu pracy.",
          "Potwierdź zakres umowy z PBM oraz osobnej dystrybucji.",
          "Przejdź przez dokumenty i kolejność zmiany sprzedawcy dopiero po weryfikacji."],
         ["Nie utożsamiaj ceny gazu z całym rachunkiem.",
          "Sprawdź dane punktu poboru i warunki operatora.",
          "Nie wypowiadaj obecnej umowy na podstawie samego porównania cen.",
          "Zakres obsługi, płatności i wymagane dokumenty: [[do zatwierdzenia]]."],
         [("Czy na start podpiszę osobną dystrybucję?", DISTRIBUTION),
          ("Czy muszę znać wszystkie parametry techniczne?", "Zacznij od dokumentów, które już masz. Brakujące informacje trzeba oznaczyć i potwierdzić, zamiast uzupełniać je szacunkiem."),
          ("Czy ta strona jest gotową ofertą?", "Nie. Pokazuje ścieżkę i pytania do rozmowy. Warunki dla firmy określą indywidualna oferta i umowy.")]),
    ]
    for slug, title, answer, audience_title, audience, mechanism, risks, faqs in product_data:
        is_trans = slug == "model-transzowy"
        extra = ""
        if slug == "cena-indeksowana-tge":
            extra = p('Publiczne materiały o rynku i indeksach: <a href="https://tge.pl/">Towarowa Giełda Energii</a>. '
                      'Właściwy indeks, publikacja i zasady wykorzystania: [[źródło]]. Nie pokazujemy bieżących notowań.')
        if is_trans:
            extra = table(["Część zakupu", "Wolumen / udział", "Reguła ceny", "Potwierdzenie"],
                          [["Transza [[oznaczenie]]", "[[ ]]", "[[ ]]", "[[sposób akceptacji]]"],
                           ["Kolejna transza [[oznaczenie]]", "[[ ]]", "[[ ]]", "[[sposób akceptacji]]"],
                           ["Część niezamknięta", "[[ ]]", "[[formuła umowna]]", "[[warunki]]"]],
                          "Schemat rozmowy; nie jest harmonogramem ani rekomendacją zakupu.")
        body = hero(title, answer, "Zapytaj o model" if is_trans else "Wgraj fakturę",
                    "/kontakt/" if is_trans else "/wgraj-fakture/", priced=True)
        body += section(audience_title, p(audience), priced=True)
        body += section("Jak działa ten model", li(mechanism, True) + extra, priced=True)
        body += section("Ryzyka i ograniczenia", li(risks), priced=True)
        body += section("Przykład do uzupełnienia", table(
            ["Parametr", "Dane", "Co potwierdzić"],
            [["Rozliczany pobór", "[[ ]] MWh", "Okres i profil"],
             ["Cena / formuła", "[[ ]]", "Zakres składników"],
             ["Koszt paliwa", "[[ ]] PLN", "Sposób obliczenia"],
             ["Pozostałe składniki", "[[ ]]", "Dystrybucja, akcyza, opłaty, marża"]],
            "Bez wartości liczbowych. Schemat nie wycenia Twojej umowy.", True), priced=True)
        body += section("Pytania przed wyborem", "".join(details(q, a) for q, a in faqs)
                        + details("Jak sprawdzić zmianę sprzedawcy?", 'Zacznij od <a href="/analiza-umowy/">analizy zapisów umowy</a>, nie od wysłania wypowiedzenia.')
                        + details("Jakie dane przygotować?", "Fakturę, umowę z aneksami, informacje o zużyciu i planowanych zmianach pracy.")
                        + details("Czy mogę już przesłać dokument?", "Upload jest nieaktywny. W prototypie zobaczysz zakres potrzebnych danych, a przycisk modułu prowadzi do kontaktu."), priced=True)
        if slug == "umowa-kompleksowa-msp":
            body += section("Osobna umowa dystrybucyjna", p(DISTRIBUTION)) + warning()
        body += sources() + cta()
        write("pages", slug, body)


def tool_pages():
    write("pages", "wgraj-fakture", hero("Jedna faktura. Konkretne pytania o zakup gazu.",
          "Faktura pomaga rozpoznać zużycie, punkt poboru i składniki rachunku. Przygotuj ją do rozmowy o warunkach zakupu gazu. W tym prototypie nie przesyłasz pliku ani danych; docelowa ścieżka oferty indykatywnej wymaga uruchomienia i zatwierdzenia.",
          "Wgraj fakturę", "#upload", note="Miejsce na upload jest nieaktywne; nie przechowujemy tu dokumentu.")
          + group("Prześlij fakturę: podgląd modułu", ref(101), anchor="upload")
          + section("Co odczytamy z faktury", li([
              "Dane firmy i identyfikator punktu poboru — do sprawdzenia z dokumentem.",
              "Okres rozliczenia oraz zużycie z podaną jednostką.",
              "Elementy dotyczące paliwa i dystrybucji, bez ich automatycznego utożsamiania.",
              "Nazwy opłat i podatków pokazanych w dokumencie.",
              "Dane potrzebne do dalszych pytań; braków nie zastąpimy wymyślonymi wartościami.",
          ]))
          + section("Co dostaniesz w 24 h — cel do potwierdzenia",
                    p("Oferta indykatywna w 24 h to roboczy, niepotwierdzony cel obsługi z briefu, nie gwarancja. Prototyp nie przygotowuje oferty i nie uruchamia biegu terminu.")
                    + li(["Docelowo: uporządkowane dane o profilu i zakresie zapytania.",
                          "Docelowo: wskazanie brakujących dokumentów lub parametrów.",
                          "Docelowo: indywidualne warunki indykatywne po potwierdzeniu danych i procesu: [[zakres odpowiedzi]]."]), priced=True)
          + section("Co przygotować poza fakturą", p("Pojedynczy rachunek nie musi opisywać sezonowości. Przygotuj zestawienie zużycia z dostępnych okresów, plan zmian produkcji oraz obecną umowę z aneksami.")
                    + p('Jeśli nie znasz terminu zakończenia, przejdź do <a href="/analiza-umowy/">analizy umowy</a>. Nie wysyłaj wypowiedzenia na podstawie samej faktury.'))
          + section("Bezpieczeństwo danych", p("Nie przesyłaj tu dokumentów poufnych. Pola są tekstową makietą; nie ma uploadu, skrzynki odbiorczej ani połączenia z CRM.")
                    + table(["Zasada przyszłego procesu", "Status"],
                            [["Retencja i usuwanie dokumentów", "[[okres retencji i procedura]]"],
                             ["Dostęp do danych i odbiorcy", "[[role, podmioty i zasady dostępu]]"],
                             ["Cel i podstawa przetwarzania", "[[treść dostarczy zleceniodawca]]"],
                             ["Bezpieczny kanał przekazania", "[[do zatwierdzenia przed uruchomieniem]]"]])
                    + p('Szczegóły: <a href="/polityka-prywatnosci/">Polityka prywatności</a>.'))
          + section("Pytania o przygotowanie faktury", details("Czy faktura zastąpi umowę?", "Nie zakładaj tego. Klauzule wypowiedzenia, przedłużenia i odpowiedzialności sprawdza się w komplecie dokumentów umownych.")
                    + details("Czy mogę usunąć dane z kopii?", "Zakres anonimizacji i niezbędnych danych należy ustalić przed przekazaniem. W prototypie nie wysyłaj żadnego pliku.")
                    + details("Czy ta ścieżka obejmuje kilka punktów poboru?", "Przygotuj listę punktów oraz przypisanie dokumentów do każdego z nich. Docelowy zakres obsługi: [[do potwierdzenia]]."))
          + sources())
    write("pages", "ceny-orientacyjne", hero("Cena gazu. Zobacz, co porównujesz.",
          "Pasma orientacyjne są punktem wyjścia do rozmowy, nie wyceną dla Twojej firmy. Aby porównać oferty, zestaw ten sam profil zużycia, okres dostaw i zakres składników. Tabela prototypu zawiera wyłącznie miejsca na dane; nie prezentuje aktualnych notowań.", priced=True)
          + group("Pełna tabela cen orientacyjnych", h("Pasma dla modeli zakupu") + ref(104))
          + section("Dekompozycja rachunku", table(["Składnik", "Co porównać", "Czego nie zakładać"],
              [["Gaz", "Stawkę lub formułę dla okresu i profilu", "Że to cała kwota rachunku"],
               ["Dystrybucja", "Zakres umowy i rozliczenia operatora", "Że jest zawarta w cenie paliwa"],
               ["Akcyza", "Sposób ujęcia i podstawę: [[do weryfikacji prawnej]]", "Automatycznego zastosowania zwolnienia"],
               ["Opłaty", "Nazwę, częstotliwość i warunek naliczenia", "Że brak jednej opłaty usuwa pozostałe"],
               ["Marża / składnik handlowy", "Czy jest w stawce, czy osobną pozycją", "Podwójnego dodawania składnika już uwzględnionego"]]), priced=True)
          + section("Jak czytać pasma", li([
              "Sprawdź datę aktualizacji. Brak daty lub wartości oznacza brak gotowej informacji cenowej.",
              "Porównuj ten sam okres dostaw, jednostkę i profil poboru.",
              "Przeczytaj zakres ceny, sposób ujęcia podatków i listę opłat dodatkowych.",
              "Ustal tolerancje wolumenu i zasady rozliczenia odchyleń.",
              "Poproś o indywidualną ofertę, zanim podejmiesz decyzję zakupową.",
          ], True), priced=True)
          + section("Przykład karty porównania", table(["Parametr", "Oferta obecna", "Warunki PBM"],
              [["Okres i punkty poboru", "[[ ]]", "[[ ]]"], ["Profil / wolumen", "[[ ]]", "[[ ]]"],
               ["Cena paliwa lub formuła", "[[ ]]", "[[ ]]"], ["Składniki poza ceną", "[[ ]]", "[[ ]]"],
               ["Odchylenia, zabezpieczenia i płatności", "[[ ]]", "[[ ]]"]]), priced=True)
          + sources(["[[źródło pasm cen i metodologia po zatwierdzeniu]]",
                     'Materiały instytucjonalne do weryfikacji: <a href="https://tge.pl/">TGE</a>; właściwa publikacja: [[link]].',
                     "[[warunki handlowe PBM i dane rozliczeniowe operatora]]"])
          + cta("Porównaj warunki dla swojego poboru.", "Przygotuj fakturę i okres dostaw. Nie podejmuj decyzji wyłącznie na podstawie pasma orientacyjnego."))
    write("pages", "kalkulator-wypowiedzenia", hero("Termin z umowy, nie z domysłu.",
          "Termin wypowiedzenia trzeba ustalić z pełnej umowy, aneksów i klauzuli przedłużenia. Kalkulator ma pomóc uporządkować dane, nie zastępować sprawdzenia prawnego. W prototypie nie liczy dat i nie ustawia przypomnień.",
          "Oblicz termin", "#kalkulator")
          + group("Kalkulator: podgląd modułu", ref(108), anchor="kalkulator")
          + section("Skąd wziąć dane z umowy", table(["Informacja", "Gdzie szukać", "Co przepisać"],
              [["Koniec umowy", "Okres obowiązywania, aneksy", "Pełne brzmienie i datę"],
               ["Okres wypowiedzenia", "Warunki zakończenia", "Wartość, jednostkę i sposób liczenia"],
               ["Prolongata", "Automatyczne przedłużenie", "Warunek, termin i skutek braku działania"],
               ["Doręczenie", "Komunikacja i oświadczenia", "Adresata, formę i moment skuteczności"],
               ["Operator", "Umowa dystrybucyjna", "Właściwy OSD i dokumenty"]]))
          + section("Dane niepełne? Zatrzymaj obliczenie.", p("Nie wpisuj daty na podstawie pamięci ani daty ostatniej faktury. Jeżeli aneks zmienia okres albo klauzula odwołuje się do regulaminu, potrzebny jest także ten dokument. Wynik powinien pokazywać założenia i pozycje wymagające wyjaśnienia.")
                    + details("Czy termin wysłania i doręczenia to to samo?", "Nie przyjmuj tego bez sprawdzenia umowy i właściwych przepisów. Znaczenie daty nadania, odbioru oraz kanału komunikacji: [[do weryfikacji prawnej]]."))
          + warning() + section("Sprawdź komplet dokumentów", p("Jeśli zapisy są niejednoznaczne, zacznij od analizy, nie od gotowego pisma.")
                                + button("Prześlij umowę do analizy", "/analiza-umowy/"))
          + sources(["[[umowa klienta, aneksy, regulamin i właściwa instrukcja operatora]]",
                     "[[źródło: aktualne przepisy o liczeniu terminów i zmianie sprzedawcy — do weryfikacji prawnej]]"]))
    write("pages", "analiza-umowy", hero("Przeczytaj umowę, zanim wybierzesz termin.",
          "Analiza umowy ma wskazać dane i zapisy potrzebne do bezpiecznego planowania zmiany sprzedawcy. Obejmuje okres obowiązywania, prolongatę, doręczenie i ryzyka zakończenia. Nie jest automatyczną zgodą na wypowiedzenie; przed wysyłką dokument sprawdza człowiek.",
          "Prześlij umowę", "#analiza")
          + group("Analiza: podgląd modułu", ref(109), anchor="analiza")
          + section("Proces: od dokumentów do sprawdzonej decyzji", li([
              "<strong>Komplet dokumentów.</strong> Zbierz umowę, aneksy, regulamin i dane punktów poboru. Oznacz brakujące załączniki.",
              "<strong>Odczyt i pytania.</strong> Docelowo moduł porządkuje zapisy, a niepewności pozostawia do wyjaśnienia.",
              "<strong>Weryfikacja przez człowieka.</strong> Osoba sprawdzająca ocenia kompletność danych, termin, uprawnienia i ryzyka przed przygotowaniem wysyłki.",
              "<strong>Uzgodnienie współpracy.</strong> Obowiązuje kolejność: umowa z PBM → pełnomocnictwo. Nie zaczynamy od rozwiązania dotychczasowej umowy.",
              "<strong>Kontrolowana realizacja.</strong> Dopiero po sprawdzeniu dokumentu przez człowieka: wypowiedzenie i zgłoszenie do OSD, z potwierdzeniami i terminami [[do weryfikacji prawnej]].",
          ], True))
          + section("Co robimy / czego nie robimy", table(["Zakres planowanej analizy", "Granica"],
              [["Porządkujemy zapisy i dane", "Nie dopisujemy brakujących klauzul ani dat"],
               ["Wskazujemy pytania o ryzyko", "Nie obiecujemy wyjścia bez kosztów"],
               ["Przewidujemy projekt dokumentu", "Nie wysyłamy automatycznie"],
               ["Sprawdzamy chronologię", "Nie rekomendujemy rozwiązania przed czasem"],
               ["Zbieramy potwierdzenia", "Nie zastępujemy indywidualnej oceny prawnej"]]))
          + warning() + section("Czego nie wysyłać do prototypu", p("Nie udostępniaj tu umów, podpisów ani danych kontrahentów. Docelowy kanał przekazania, zakres dostępu oraz retencja: [[do zatwierdzenia]].")
                               + p('Zasady przetwarzania: <a href="/polityka-prywatnosci/">Polityka prywatności</a>.'))
          + sources(["[[umowa klienta i dokumenty powiązane]]", "[[procedura PBM: zatwierdzenie prawne i operacyjne]]"])
          + section("Następny krok: omów zakres analizy", p("Powiedz, które zapisy budzą wątpliwości. W prototypie nie przyjmujemy dokumentów.")
                    + button("Prześlij umowę — przejdź do kontaktu", "/kontakt/")))


def remaining_pages():
    write("pages", "archiwum-kategorii",
          group("Nagłówek archiwum kategorii",
                block("query-title", attrs={"type": "archive", "showPrefix": False, "level": 1}, dynamic=True)
                + p("Wybierz artykuł z tej kategorii. Treści robocze porządkują pytania do rozmowy; źródła i terminy oznaczone do weryfikacji wymagają zatwierdzenia.", "gdp-lead")
                + p('<a href="/wiedza/">Wróć do wszystkich tematów</a>'))
          + section("Materiały w tej kategorii", query("Bieżąca kategoria", inherit=True))
          + section("Nie znalazłeś odpowiedzi?", p("Brak wpisu nie oznacza braku możliwości rozmowy. Przygotuj dokumenty i pytania o zakup gazu.")
                    + button("Przejdź do bazy wiedzy", "/wiedza/", True))
          + cta())
    write("pages", "biometan", hero("Biometan. Kierunek rozwoju, nie obietnica dostawy.",
          "PBM przewiduje ścieżkę biometanu powiązaną z aktywami Grupy IMA Polska. To zapowiedź przyszłej oferty, bez potwierdzonych terminów, wolumenów i cen. Dokumentacja produktu oraz sposób wykorzystania przez klienta wymagają osobnego sprawdzenia.",
          "Zapisz się na informację", "#zainteresowanie")
          + section("Od aktywów do udokumentowanego produktu", p("Chcemy rozmawiać o potrzebach odbiorcy i wymaganych dokumentach, zanim przedstawimy ofertę. Opis aktywów, pochodzenia paliwa i planowanego modelu dostawy zostanie uzupełniony po zatwierdzeniu.")
                    + li(["Aktywa Grupy: [[opis aktywów do zatwierdzenia]].",
                          "Opis produktu i ścieżki pochodzenia: [[dokumentacja produktu]].",
                          "Model dostawy i zakres odpowiedzialności: [[do uzgodnienia]]."]))
          + section("Dokumenty przed deklaracją", p("Certyfikacja, potwierdzenie pochodzenia i wymagania odbiorcy nie są zamiennymi pojęciami. Zakres dokumentów trzeba uzgodnić dla konkretnego zastosowania. Sam zapis zainteresowania nie potwierdza spełnienia wymagań klienta.")
                    + p("Nie deklarujemy zaliczenia biometanu do celów regulacyjnych Twojej firmy. Ocena dokumentów i warunków użycia: [[do weryfikacji prawnej i certyfikacyjnej]]."))
          + section("Raportowanie Scope 1 per punkt poboru — wkrótce", p("M9 to miejsce na przyszły moduł porządkowania danych dla punktów poboru. Nie działa kalkulator emisji ani raport CSRD/ETS. Nie obiecujemy zgodności regulacyjnej.")
                    + table(["Zakres do zaprojektowania", "Status"],
                            [["Dane punktu i okres rozliczenia", "[[specyfikacja danych]]"],
                             ["Metodologia i współczynniki", "[[do zatwierdzenia]]"],
                             ["Dokumenty i sposób prezentacji", "[[do weryfikacji]]"]]))
          + group("Zainteresowanie biometanem", form_slot("Informacja o biometanie",
                  [("Firma", "[[nazwa firmy]]"), ("E-mail", "[[adres e-mail]]"),
                   ("Cel rozmowy", "[[potrzeby zakupowe lub dokumentacyjne]]")], "Zapisz się na informację",
                  "Docelowo zostawisz kontakt, aby otrzymać informację o zatwierdzonym zakresie oferty. Dziś to nieaktywny podgląd."), anchor="zainteresowanie")
          + sources(["[[zatwierdzony opis aktywów Grupy IMA Polska]]",
                     "[[dokumentacja biometanu i właściwe wymagania certyfikacyjne]]"]))
    write("pages", "dla-kogo", hero("Zacznij od tego, jak pracuje Twoja firma.",
          "Inaczej przygotowuje zakup zakład przemysłowy, inaczej mniejsza firma, a inaczej doradca reprezentujący portfel klientów. Wybierz ścieżkę, by zobaczyć potrzebne dane i pytania do rozmowy. Próg zużycia pozostaje roboczy.",
          "Wybierz ścieżkę", "#segmenty")
          + group("Segmenty klientów", h("Twój profil zakupu") + ref(105), anchor="segmenty")
          + sources() + cta())
    segment_data = [
        ("przemysl", "Gaz dla przemysłu. Warunki pod rytm zakładu.",
         "Zakup gazu dla przemysłu wymaga połączenia profilu poboru, planu produkcji i zasad zarządzania ryzykiem. Przygotuj dane dla punktów poboru, sezonowość oraz plan zmian pracy zakładu. Rozmowa z opiekunem ma dopasować zakres oferty do tych danych, nie zastąpić je średnią.",
         "Porozmawiaj z opiekunem", "/kontakt/",
         ["Planowane postoje, rozruchy i zmiany mocy procesu mogą zmienić zapotrzebowanie.",
          "Różne punkty poboru potrzebują czytelnego przypisania danych i dokumentów.",
          "Budżet, zakupy i produkcja powinny pracować na tych samych założeniach.",
          "Tolerancje wolumenu, zabezpieczenia i płatności wymagają analizy obok ceny."],
         ["Profil zużycia dla punktów poboru: [[dostępny zakres danych]].",
          "Plan produkcji oraz zmiany zapotrzebowania: [[założenia]].",
          "Preferencje ceny i osoby uprawnione do decyzji.",
          "Obecne umowy, aneksy i warunki dystrybucji."]),
        ("msp", "Gaz dla MŚP. Mniej domysłów przed podpisem.",
         "Dla mniejszej firmy punktem wyjścia jest faktura, obecna umowa i informacja, kiedy zużywasz gaz. Nie musisz zaczynać od wyboru produktu. Najpierw sprawdź składniki rachunku, okres umowy i to, czy dystrybucja wymaga osobnego dokumentu.",
         "Wgraj fakturę", "/wgraj-fakture/",
         ["Rachunek może zawierać więcej niż cenę paliwa — nazwij każdą pozycję.",
          "Sezon grzewczy lub rytm wypieku, suszenia i produkcji zmieniają pobór.",
          "Termin końca umowy nie zawsze wystarczy do zaplanowania kolejnego zakupu.",
          "Osoba podpisująca dokumenty powinna znać zasady płatności i zmian zużycia."],
         ["Faktura i dane punktu poboru.",
          "Umowa, aneksy oraz informacja o przedłużeniu.",
          "Opis sezonowości: kiedy pracujesz więcej, a kiedy mniej.",
          "Planowane zmiany działalności i dane do kontaktu."]),
    ]
    for slug, title, answer, action, url, problems, documents in segment_data:
        write("pages", slug, hero(title, answer, action, url)
              + section("Co warto uporządkować", li(problems))
              + section("Produkty do rozmowy", table(["Potrzeba", "Model do porównania", "Pytanie kontrolne"],
                  [["Znana cena paliwa", '<a href="/oferta/cena-stala/">Cena stała</a>', "Czy profil i tolerancje pasują do planu?"],
                   ["Rozliczenie według odniesienia rynkowego", '<a href="/oferta/cena-indeksowana-tge/">Indeks TGE</a>', "Czy rozumiesz formułę i akceptujesz zmienność?"],
                   ["Podział decyzji zakupowych", '<a href="/oferta/model-transzowy/">Model transzowy</a>', "Kto i jak potwierdza transze?"],
                   ["Uporządkowanie dokumentów", '<a href="/oferta/umowa-kompleksowa-msp/">Ścieżka MŚP</a>', "Kto zawiera umowę dystrybucyjną?"]]), priced=True)
              + section("Przygotuj dane do rozmowy", li(documents))
              + section("Jak przejdziesz przez proces", li([
                  "Przygotuj dokumenty i opisz oczekiwany okres dostaw.",
                  "Omów profil, ograniczenia i brakujące dane.",
                  "Porównaj warunki oferty w tym samym zakresie.",
                  "Sprawdź umowę i chronologię działań przed podpisem lub wysyłką oświadczeń.",
              ], True) + p(DISTRIBUTION))
              + warning() + sources() + section("Zacznij od swojego profilu", p("Nie wybieraj modelu na podstawie samej nazwy. Przygotuj dane i porównaj ograniczenia.")
                                                              + button(action, url)))
    write("pages", "dla-doradcow", hero("Twój portfel klientów. Uporządkowana współpraca.",
          "Kanał dla doradców ma ułatwić przygotowanie zapytań o gaz dla reprezentowanych firm. Zacznij od zakresu współpracy, sposobu przekazywania danych i umocowania. Model rozliczeń oraz warunki handlowe są do uzgodnienia, nie są gotowym programem partnerskim.",
          "Zgłoś się", "#doradca")
          + section("Ustalmy sposób pracy", table(["Obszar", "Do uzgodnienia"],
              [["Model współpracy i rozliczeń", "[[model współpracy]]"],
               ["Przypisanie kontaktów i opiekuna", "[[zasady prowadzenia zapytań]]"],
               ["Umocowanie i przekazywanie dokumentów", "[[zakres uprawnień i procedura]]"],
               ["Warunki odpowiedzi i ważność ofert", "[[warunki operacyjne]]"]]))
          + section("Co ma otrzymać doradca", li([
              "Czytelny zakres danych potrzebnych do zapytania dla pojedynczej firmy lub portfela.",
              "Porównywalny opis modeli ceny, z ograniczeniami i zakresem składników.",
              "Uzgodniony sposób przekazywania pytań i aktualizacji dokumentów.",
              "Kontakt po stronie PBM: [[opiekun i zakres obsługi]].",
          ]) + p("To planowany zakres współpracy. Nie deklarujemy prowizji, wyłączności ani terminu odpowiedzi."))
          + section("Najpierw prawo do reprezentacji", p("Przed przekazaniem danych klienta potwierdź uprawnienie, zakres reprezentacji i dopuszczony kanał komunikacji. Sam formularz zainteresowania nie ustanawia pełnomocnictwa ani relacji partnerskiej."))
          + group("Formularz doradcy: podgląd", ref(110), anchor="doradca")
          + sources(["[[regulamin i model współpracy z doradcami]]", "[[zasady umocowania i przekazywania danych]]"]))
    write("pages", "dla-agentow-ai", hero("Kanał dla agentów AI. Specyfikacja przed integracją.",
          "Kanał B2A ma w przyszłości pozwolić agentowi działającemu w imieniu firmy odczytać strukturę oferty i przygotować zapytanie RFQ. W etapie prototypu nie istnieje działający endpoint, klucz API ani automatyczne zawarcie umowy.",
          "Pobierz specyfikację — placeholder", "/kontakt/",
          note="Specyfikacja nie jest jeszcze dostępna do pobrania. Przycisk prowadzi do kontaktu.")
          + section("Co planujemy opisać maszynowo", table(["Zasób", "Planowany zakres", "Status"],
              [["Opis oferty", "Modele zakupu, wymagane dane, ograniczenia", "[[schemat danych]]"],
               ["Zapytanie RFQ", "Firma, umocowanie, punkty poboru, okres i profil", "[[specyfikacja RFQ]]"],
               ["Odpowiedź", "Status kompletności i pytania do klienta", "[[model odpowiedzi]]"],
               ["Wersjonowanie", "Wersja schematu i data aktualizacji", "[[polityka wersji]]"]]))
          + section("Granice działania agenta", li([
              "Agent ma wskazać, kogo reprezentuje i na jakiej podstawie: [[reguły umocowania]].",
              "Nie powinien dopisywać brakujących cen, wolumenów ani danych klienta.",
              "Zapytanie nie jest zawarciem umowy ani zgodą na wypowiedzenie dotychczasowej.",
              "Dane, zgody, uwierzytelnianie i obsługa błędów wymagają zatwierdzonej specyfikacji.",
              "Decyzje i dokumenty wrażliwe wymagają kontroli człowieka.",
          ]))
          + section("Specyfikacja: miejsce na dokument", p("[[specyfikacja B2A: wersja, data, URL]]")
                    + p("Nie publikujemy pozornego adresu API ani przykładowego klucza. Nie wysyłaj automatycznych zapytań do tej witryny w oczekiwaniu na ofertę.")
                    + button("Zapytaj o specyfikację", "/kontakt/"))
          + sources(["[[zatwierdzona specyfikacja B2A i zasady bezpieczeństwa]]"]))
    categories = [
        ("Zmiana sprzedawcy", "zmiana-sprzedawcy", "Kolejność działań, komplet dokumentów i punkty kontrolne."),
        ("Umowy i wypowiedzenia", "umowy-i-wypowiedzenia", "Okres umowy, przedłużenie i pytania do weryfikacji prawnej."),
        ("Ceny i rynek", "ceny-i-rynek", "Mechanizm ceny, profil zużycia i porównanie warunków."),
        ("Biometan i raportowanie", "biometan-i-raportowanie", "Miejsce na materiały o dokumentacji i raportowaniu. Pierwszy artykuł: [[w przygotowaniu]]."),
        ("Sprzedaż rezerwowa", "sprzedaz-rezerwowa", "Ryzyka przejścia między umowami i struktura pytań o koszty."),
    ]
    write("pages", "wiedza", hero("Wiedza, która porządkuje decyzję o gazie.",
          "Baza wiedzy pomaga przygotować pytania o zmianę sprzedawcy, umowę i model ceny. Artykuły są robocze; wymagające potwierdzenia źródła i terminy są oznaczone. Wybierz temat, przeczytaj listę kontrolną i wróć do dokumentów swojej firmy.")
          + section("Wybierz temat", group("Kategorie wiedzy", "".join(group(name, h(name, 3) + p(desc)
                    + p(f'<a href="/category/{slug}/">Zobacz: {name.lower()}</a>'), "gdp-audience-card")
                  for name, slug, desc in categories), "gdp-audience-grid"))
          + section("Najnowsze artykuły", query("Artykuły", [51, 52, 53, 54, 55], 6))
          + section("Znajdź odpowiedź", block("search", attrs={"label": "Szukaj w bazie wiedzy", "showLabel": True,
                      "placeholder": "Wpisz temat, np. prolongata", "buttonText": "Szukaj", "buttonUseIcon": False}, dynamic=True))
          + section("Szukasz komentarza do rynku?", p("Komentarze mają własne archiwum. Obecne wpisy są szablonami, nie opisem bieżących wydarzeń.")
                    + button("Zobacz komentarze rynkowe", "/komentarz-rynkowy/", True))
          + sources(["[[źródła wskazane osobno pod każdym artykułem]]"]) + cta())
    write("pages", "komentarz-rynkowy", hero("Komentarz rynkowy. Kontekst zamiast prognozy bez podstaw.",
          "Komentarze rynkowe mają łączyć obserwację rynku z pytaniami o zakup gazu w firmie. Każdy materiał będzie miał autora, datę i źródła. Obecnie publikujemy wyłącznie szablony; nie zawierają aktualnych danych ani rekomendacji zakupowej.",
          "Subskrybuj — podgląd", "#subskrypcja")
          + section("Wpisy z datą i autorem", query("Komentarze", [50], 6, True))
          + group("Subskrypcja: podgląd", form_slot("Subskrypcja komentarza",
                  [("E-mail", "[[adres e-mail]]")], "Subskrybuj", "Przyszła subskrypcja wymaga zatwierdzenia zasad i zgód. W prototypie nie zapisujemy adresów."), anchor="subskrypcja")
          + sources(["[[źródła rynku podawane osobno w każdym zatwierdzonym komentarzu]]"]))
    write("pages", "o-nas", hero("Gaz dla Przemysłu. Kanał PBM z Grupy IMA Polska.",
          "Gaz dla Przemysłu to kanał akwizycyjny PBM Sp. z o.o., należącej do Grupy IMA Polska. Ma pomagać firmom przygotować dane do zakupu paliw gazowych i porównać warunki. Dane rejestrowe, koncesja, aktywa oraz zespół pozostają oznaczone do uzupełnienia.",
          "Skontaktuj się", "/kontakt/")
          + group("Podmiot i Grupa", h("Kto stoi za kanałem") + ref(106))
          + section("Aktywa: pokażemy dokumenty, nie zastępcze zdjęcia", p("Kontekstem Grupy są przemysł biotechnologiczny i energetyka odnawialna. Konkretny zakres aktywów wykorzystywanych w opisie oferty wymaga zatwierdzenia.")
                    + p("[[aktywa Grupy: opis, lokalizacja i zatwierdzone dane]]")
                    + group("Miejsce na zdjęcie aktywów", p("[[zdjęcie: zatwierdzony widok aktywów Grupy, opis alternatywny i prawa do publikacji]]"), "gdp-card"))
          + section("Zespół i odpowiedzialność", table(["Obszar", "Osoba i zakres"],
              [["Obsługa przemysłu", "[[imię i nazwisko, stanowisko, odpowiedzialność]]"],
               ["Obsługa MŚP i doradców", "[[imię i nazwisko, stanowisko, odpowiedzialność]]"],
               ["Komentarz rynkowy", "[[imię i nazwisko, stanowisko]] — Zespół analiz PBM jako placeholder"]]))
          + section("Dane, które można sprawdzić", p("[[PBM Sp. z o.o., adres, NIP, KRS, kapitał zakładowy]]")
                    + p("Koncesja OPG nr [[ ]] wydana przez Prezesa URE.")
                    + p('Dokumenty i ich wersje: <a href="/dokumenty/">Dokumenty</a>. Nie udostępniamy plików zastępczych.'))
          + section("Jak chcemy pracować z Twoimi danymi", li([
              "Oddzielamy cenę paliwa od pozostałych składników rachunku.",
              "Oznaczamy brakujące dane zamiast uzupełniać je za klienta.",
              "Pokazujemy ograniczenia produktu obok jego przeznaczenia.",
              "Sprawdzamy dokument przed wysyłką i nie zaczynamy od wypowiedzenia.",
          ])) + sources(["[[materiały zatwierdzone przez PBM i Grupę IMA Polska]]", "[[odpis rejestrowy i dokument koncesji]]"]))
    docrows = [
        ("Koncesja na obrót paliwami gazowymi", "[[numer koncesji i dokument]]"),
        ("Cennik dla odbiorców biznesowych", "[[zatwierdzony cennik]]"),
        ("Struktura paliw", "[[dokument i zakres publikacji]]"),
        ("Regulaminy i warunki umowne", "[[zatwierdzone regulaminy]]"),
        ("Informacje RODO", "[[pakiet informacji i zgód]]"),
        ("Decyzje URE", "[[decyzje właściwe dla PBM]]"),
    ]
    write("pages", "dokumenty", hero("Dokumenty. Nazwa, wersja i data w jednym miejscu.",
          "Tutaj znajdziesz miejsce na dokumenty podmiotu, warunki handlowe i informacje prawne. Lista jest robocza: nazwy wymagają potwierdzenia, a pliki nie zostały opublikowane. Placeholder nie jest dokumentem i nie potwierdza uprawnień ani warunków oferty.", cta=None)
          + section("Dokumenty do publikacji", "".join(group("Wiersz dokumentu: " + name,
                  h(name, 3) + table(["Dokument", "Data / wersja", "PDF"], [[desc, "[[data / wersja]]", "[[URL pliku PDF po zatwierdzeniu]]"]]),
                  "gdp-document-row") for name, desc in docrows), priced=True)
          + section("Jak sprawdzić dokument", li(["Porównaj nazwę podmiotu i zakres dokumentu.",
                                                "Sprawdź datę, wersję i okres obowiązywania.",
                                                "Upewnij się, że załączniki należą do tej samej wersji warunków.",
                                                "Jeśli pliku brakuje, zapytaj o właściwy dokument zamiast korzystać z niepotwierdzonej kopii."])
                    + p('Treści serwisowe: <a href="/polityka-prywatnosci/">Polityka prywatności</a> i <a href="/regulamin/">Regulamin serwisu</a>.'))
          + sources(["[[zatwierdzona lista dokumentów PBM i oryginalne pliki]]"]))
    write("pages", "kontakt", hero("Porozmawiajmy o zakupie gazu w Twojej firmie.",
          "Przygotuj informację o firmie, punktach poboru i temacie rozmowy. Kontakt ma pomóc ustalić, jakie dane są potrzebne do zapytania. W prototypie dane adresowe czekają na potwierdzenie, a formularz nie wysyła wiadomości.",
          "Wgraj fakturę", "/wgraj-fakture/")
          + section("Dane kontaktowe", table(["Kontakt", "Dane do uzupełnienia"],
              [["Podmiot", "PBM Sp. z o.o., Grupa IMA Polska"],
               ["Adres / NIP / KRS / kapitał zakładowy", "[[PBM Sp. z o.o., adres, NIP, KRS, kapitał zakładowy]]"],
               ["E-mail", "[[adres e-mail do kontaktu]]"], ["Telefon", "[[numer telefonu]]"],
               ["Godziny obsługi", "[[dni i godziny obsługi]]"]]))
          + group("Formularz kontaktowy: podgląd", form_slot("Kontakt z PBM",
                [("Imię i firma", "[[dane kontaktowe]]"), ("E-mail", "[[adres e-mail]]"),
                 ("Telefon", "[[numer telefonu]]"), ("Temat", "[[zakup gazu, umowa lub współpraca]]"),
                 ("Wiadomość", "[[krótki opis potrzeb]]")], "Przejdź do danych kontaktowych",
                "Pola są makietą. Nie wpisuj ani nie wysyłaj danych osobowych."))
          + section("Lokalizacja", p("[[mapa: lokalizacja biura po potwierdzeniu adresu]]")
                    + p("Nie ładujemy mapy z zewnętrznego serwisu. Adres i wskazówki dojazdu: [[do uzupełnienia]]."))
          + section("Z czym chcesz przyjść?", li([
              '<a href="/dla-kogo/przemysl/">Zakup dla zakładu przemysłowego</a> — profil i plan produkcji.',
              '<a href="/dla-kogo/msp/">Zakup dla MŚP</a> — faktura i obecna umowa.',
              '<a href="/dla-doradcow/">Współpraca doradcy</a> — model obsługi i reprezentacja.',
              '<a href="/analiza-umowy/">Analiza umowy</a> — najpierw zakres dokumentów, bez wysyłki w prototypie.',
          ])) + sources(["[[zatwierdzone dane rejestrowe i kontaktowe PBM]]"]))
    for slug, title, headings in [
        ("polityka-prywatnosci", "Polityka prywatności",
         ["Administrator danych i kontakt", "Cele, zakres i podstawy przetwarzania", "Odbiorcy i podmioty przetwarzające",
          "Retencja i usuwanie danych", "Prawa osób i sposób kontaktu", "Pliki cookie i mechanizm zgód", "Zmiany polityki"]),
        ("regulamin", "Regulamin serwisu",
         ["Podmiot i zakres serwisu", "Charakter informacji i treści roboczych", "Zasady korzystania z narzędzi",
          "Zasady kontaktu i przekazywania dokumentów", "Odpowiedzialność i zgłaszanie uwag", "Wersje i zmiany regulaminu"]),
    ]:
        write("pages", slug, hero(title, "To struktura dokumentu do uzupełnienia i zatwierdzenia przez zleceniodawcę. Nie jest gotową polityką ani regulaminem. Prototyp nie uruchamia formularzy, uploadu i integracji; docelowe zasady wymagają dopasowania do rzeczywistego procesu.", cta=None)
              + "".join(section(heading, p("[[treść dostarczy zleceniodawca]]")
                                + (p("[[slot CMP — etap 3]]") if "cookie" in heading else "")) for heading in headings)
              + sources(["[[zatwierdzony dokument prawny: wersja i osoba akceptująca]]"]))
    write("pages", "blad-404", hero("Nie znaleźliśmy tej strony.",
          "Adres może być niepełny albo nie prowadzi już do dostępnej treści. Wróć na stronę główną lub zacznij od przygotowania faktury do rozmowy o gazie. Żadne dane nie zostały wysłane przez tę stronę.",
          "Wróć na stronę główną", "/")
          + section("Wybierz następny krok", button("Wgraj fakturę", "/wgraj-fakture/", True)
                    + li(['<a href="/oferta/">Porównaj modele zakupu</a>',
                          '<a href="/wiedza/">Poszukaj odpowiedzi w bazie wiedzy</a>',
                          '<a href="/kontakt/">Sprawdź kontakt do PBM</a>'])))


def preserve_c_pages():
    path = CONTENT / "pages/start.html"
    text = path.read_text()
    text = text.replace('href="/kontakt/">Wgraj fakturę', 'href="/wgraj-fakture/">Wgraj fakturę')
    text = text.replace("Prototyp serwisu. CTA prowadzi do kontaktu; nie przesyła faktury.",
                        "Przygotuj fakturę do rozmowy. Upload w prototypie jest nieaktywny.")
    text = text.replace('href="/komentarz-rynkowy-szablon/"', 'href="/wiedza/komentarz-rynkowy-szablon/"')
    text = text.replace("Progi zużycia są robocze; w prototypie każda ścieżka prowadzi do kontaktu.",
                        "Progi zużycia są robocze; wybierz ścieżkę odpowiednią dla Twojej firmy.")
    text = text.replace('href="/oferta/cena-stala/">Sprawdź, co obejmuje cena stała',
                        'href="/ceny-orientacyjne/">Zobacz pełne pasma i składniki ceny')
    def filter_market(match):
        attrs = json.loads(match.group(1))
        attrs["query"]["taxQuery"] = {"category": [50]}
        attrs["query"]["gdpCategory"] = "komentarz-rynkowy"
        return "<!-- wp:query " + json.dumps(attrs, ensure_ascii=False, separators=(",", ":")) + " -->"
    text = re.sub(r"<!-- wp:query (\{.*?\}) -->", filter_market, text)
    # Keep accepted layout; only fix the calculator destination and its prototype note.
    text = text.replace('href="/kontakt/">Sprawdź termin', 'href="/kalkulator-wypowiedzenia/">Sprawdź termin')
    text = text.replace('href="/kontakt/">Zapytaj o termin', 'href="/kalkulator-wypowiedzenia/">Sprawdź termin')
    text = text.replace('href="/kontakt/">Zapytaj o sprawdzenie danych z umowy',
                        'href="/kalkulator-wypowiedzenia/">Sprawdź kalkulator terminu wypowiedzenia')
    # Accepted home already contains the required chronology and human check.
    if "Nie wypowiadaj umowy przed weryfikacją warunków." in text:
        text = text.replace(p(CAUTION, "gdp-small"), "")
    path.write_text(text)
    path = CONTENT / "pages/cena-stala.html"
    text = path.read_text().replace('href="/kontakt/">Wgraj fakturę', 'href="/wgraj-fakture/">Wgraj fakturę')
    text = text.replace("Prototyp: przycisk prowadzi do kontaktu. Nie przesyła danych.",
                        "Zobacz, jakie dane przygotować. Upload w prototypie jest nieaktywny.")
    # Exact price caution also on prose pricing sections; all accepted text stays intact.
    # Do not split nested wrappers for editing. Named root sections selected by original anchors.
    for name in ["Dla kogo cena stała", "Jak działa cena stała", "Ryzyka i ograniczenia", "Pytania o cenę stałą"]:
        marker = f'<!-- wp:group {{"metadata":{{"name":"{name}"}},"templateLock":"contentOnly"'
        start = text.find(marker)
        if start < 0:
            continue
        next_start = text.find('\n\n<!-- wp:group ', start + len(marker))
        end = next_start if next_start >= 0 else len(text)
        chunk = text[start:end]
        if '"ref":102' not in chunk:
            insert_at = chunk.rfind("</div>")
            chunk = chunk[:insert_at] + ref(102) + chunk[insert_at:]
            text = text[:start] + chunk + text[end:]
    path.write_text(text)


def articles():
    data = [
        {
            "slug": "jak-zmienic-sprzedawce-gazu-w-firmie",
            "title": "Jak zmienić sprzedawcę gazu w firmie: kolejność kroków i terminy",
            "answer": "Zmianę sprzedawcy gazu zacznij od sprawdzenia obecnej umowy, aneksów i danych punktów poboru. Nie rozpoczynaj od wypowiedzenia. W ścieżce PBM najpierw zawierasz umowę z PBM, potem udzielasz pełnomocnictwa, a dopiero następnie następują sprawdzone wypowiedzenie i zgłoszenie do OSD.",
            "sections": [
                ("dokumenty", "Zbierz dokumenty, zanim porównasz terminy",
                 p("Połóż obok siebie umowę sprzedaży, aneksy, regulamin, fakturę i dokumenty dystrybucyjne. Sprawdź, czy dotyczą tej samej firmy i tych samych punktów poboru. Nazwa sprzedawcy na rachunku nie wystarczy do ustalenia wszystkich zasad zakończenia umowy. Jeśli brakuje załącznika, oznacz brak i poproś o właściwą wersję.")
                 + p("Przygotuj także opis sezonowości oraz planowanych zmian produkcji. Dzięki temu rozmowa o nowej ofercie nie oprze się wyłącznie na jednym okresie rozliczenia. Nie zakładaj, że dane z faktury automatycznie określają przyszły wolumen.")
                 + li(["Umowa i aneksy: okres, prolongata, doręczenie.", "Punkty poboru: identyfikatory i operator.", "Zużycie: dostępna historia oraz plan zmian."])),
                ("kolejnosc", "Ustal kolejność i osobę odpowiedzialną",
                 p("Rozdziel porównanie ofert od formalnego uruchomienia zmiany. Zestaw zakres ceny, okres dostaw, płatności, zabezpieczenia i tolerancje zużycia. Następnie wskaż osobę, która może zatwierdzić warunki, podpisać dokumenty i sprawdzić zgodność danych. Nie traktuj deklaracji handlowej jak potwierdzenia rozpoczęcia dostaw.")
                 + table(["Krok PBM", "Co trzeba potwierdzić"], [
                     ["Umowa z PBM", "Zakres, okres i warunki współpracy"],
                     ["Pełnomocnictwo", "Osoba podpisująca i zakres umocowania"],
                     ["Weryfikacja przez człowieka przed wysyłką", "Treść dokumentu, tryb i daty"],
                     ["Wypowiedzenie i zgłoszenie do OSD", "Właściwy adresat, komplet dokumentów i potwierdzenia"]])
                 + p("Dokument wypowiedzenia jest weryfikowany przez człowieka przed wysyłką. Skutki błędnego wypowiedzenia, w tym sprzedaż rezerwową i kary, ponosi klient. Dlatego nie rekomendujemy rozwiązania obecnej umowy przed czasem. Zatrzymaj proces, jeśli dokumenty wskazują sprzeczne daty lub inne dane odbiorcy.")),
                ("terminy", "Zapisz terminy razem z ich podstawą",
                 p("Dla każdej daty zapisz, z którego paragrafu lub dokumentu wynika. Oddziel koniec dostaw, termin złożenia oświadczenia i czynności wobec operatora. Sprawdź formę oraz sposób doręczenia. Termin ustawowy i reguły jego liczenia: [[do weryfikacji prawnej]]. Ten artykuł nie podaje liczby dni ani gotowej daty dla Twojej firmy.")
                 + p("Zachowaj potwierdzenia i przypisz kolejne działania do konkretnych osób. Jeżeli termin zależy od otrzymania dokumentu, nie zastępuj potwierdzenia odbioru samą notatką o wysłaniu. Zasady skuteczności doręczenia wymagają sprawdzenia dla umowy i właściwych przepisów: [[do weryfikacji prawnej]].")
                 + p(DISTRIBUTION)
                 + p('Przed rozmową przygotuj <a href="/wgraj-fakture/">fakturę</a>. Niejasne klauzule skieruj do <a href="/analiza-umowy/">analizy umowy</a>, a daty porządkuj w <a href="/kalkulator-wypowiedzenia/">kalkulatorze terminu</a>, którego moduł jest jeszcze nieaktywny.')),
            ],
            "sources": ["[[źródło: aktualne Prawo energetyczne, przepisy zmiany sprzedawcy i terminy — do weryfikacji prawnej]]",
                        "[[źródło: właściwa instrukcja operatora i zasady zgłoszeń]]",
                        "[[umowa klienta, regulamin, aneksy i procedura PBM]]"],
            "cta": ("Przygotuj dokumenty do analizy.", "/analiza-umowy/", "Przejdź do analizy umowy"),
            "priced": True,
        },
        {
            "slug": "okres-wypowiedzenia-klauzula-prolongacyjna",
            "title": "Okres wypowiedzenia i klauzula prolongacyjna w umowie na gaz: jak policzyć termin",
            "answer": "Terminu nie ustalisz z samej daty końca umowy. Potrzebujesz okresu wypowiedzenia, sposobu jego liczenia, klauzuli przedłużenia oraz zasad doręczenia. Przepisz pełne zapisy i sprawdź aneksy. Wynik obliczenia wymaga weryfikacji człowieka przed wysłaniem dokumentu.",
            "sections": [
                ("zapisy", "Oddziel trzy różne pytania",
                 p("Najpierw zapytaj, do kiedy obowiązuje obecna umowa. Następnie sprawdź, jak opisano jej zakończenie. Na końcu odczytaj zapis o automatycznym przedłużeniu. To powiązane, ale nie identyczne informacje. Notatka „umowa kończy się w danym miesiącu” może pomijać warunek, który zmienia dalszy bieg współpracy.")
                 + p("Nie skracaj klauzuli do pojedynczej liczby. Zachowaj jednostkę czasu, odniesienie do początku lub końca okresu oraz wszelkie warunki dodatkowe. Gdy umowa odsyła do regulaminu, odczytaj odpowiednią wersję tego dokumentu. Jeśli aneks zmienił zapis, wskaż jego datę i zakres zamiast mieszać stare oraz nowe brzmienie.")
                 + li(["Okres obowiązywania — co wskazuje dokument?", "Wypowiedzenie — kiedy, jak i komu?", "Prolongata — jaki warunek i skutek przewiduje zapis?"])),
                ("karta", "Przygotuj kartę terminu do sprawdzenia",
                 table(["Pole", "Co wpisujesz", "Podstawa"], [
                     ["Koniec okresu", "[[data]]", "[[paragraf / aneks]]"],
                     ["Okres wypowiedzenia", "[[wartość i jednostka]]", "[[pełna klauzula]]"],
                     ["Przedłużenie", "[[warunek]]", "[[pełna klauzula]]"],
                     ["Doręczenie", "[[forma, adresat, moment]]", "[[umowa i przepisy]]"]])
                 + p("Sama tabela nie oblicza terminu. Pozwala zobaczyć braki oraz zapisy, które trzeba odczytać łącznie. Nie przepisuj do niej daty z cudzej umowy i nie zakładaj typowego okresu wypowiedzenia. Przykład liczby dni mógłby stworzyć fałszywe poczucie pewności, dlatego wartości w prototypie pozostają puste.")
                 + p("Jeśli pojawiają się dni wolne, koniec miesiąca albo odwołanie do daty otrzymania oświadczenia, zaznacz to osobno. Właściwa reguła obliczenia oraz podstawa prawna: [[do weryfikacji prawnej]]. Tak samo oznacz niejasną relację między wypowiedzeniem a rezygnacją z przedłużenia.")),
                ("kontrola", "Sprawdź wynik przed działaniem",
                 p("Przedstaw komplet dokumentów osobie sprawdzającej. Powinna potwierdzić nie tylko datę, ale również adresata, sposób podpisania, umocowanie oraz zgodność danych punktu poboru. Zapisz, jakie założenia przyjęto i kto je zaakceptował. Przy sprzecznych dokumentach zatrzymaj wysyłkę, zamiast wybierać termin, który wydaje się wygodniejszy.")
                 + p(CAUTION)
                 + p("W docelowym narzędziu przypomnienie ma wspierać organizację pracy, nie przenosić odpowiedzialności za prawidłowość danych. W prototypie nie ma obliczenia ani powiadomień. Wpisanie lub odczytanie daty na stronie nie uruchamia żadnej czynności wobec sprzedawcy ani operatora.")
                 + p('Zobacz <a href="/kalkulator-wypowiedzenia/">zakres kalkulatora</a> lub przejdź do <a href="/analiza-umowy/">analizy umowy</a>. Przygotuj także pytanie, czy dokumenty dystrybucyjne wymagają osobnych działań.')),
            ],
            "sources": ["[[źródło: umowa, regulamin i aneksy klienta]]",
                        "[[źródło: aktualne przepisy o liczeniu terminów i doręczeniu — do weryfikacji prawnej]]"],
            "cta": ("Uporządkuj dane, zanim ustalisz termin.", "/kalkulator-wypowiedzenia/", "Zobacz kalkulator wypowiedzenia"),
        },
        {
            "slug": "sprzedaz-rezerwowa-gazu",
            "title": "Sprzedaż rezerwowa gazu: kiedy grozi i ile kosztuje",
            "answer": "Ryzyko sprzedaży rezerwowej warto sprawdzić, gdy między dotychczasową a planowaną sprzedażą pojawia się niepotwierdzony okres lub problem z formalnościami. Nie zakładaj automatycznie jej warunków ani kosztu. Przesłanki uruchomienia, zasady rozliczenia i terminy wymagają aktualnego źródła oraz oceny Twojej sytuacji.",
            "sections": [
                ("ryzyko", "Zauważ niepotwierdzony odcinek procesu",
                 p("Kupujący często skupia się na podpisaniu nowej oferty. Równie ważne jest jednak sprawdzenie, czy zgadzają się okresy, punkty poboru i dokumenty. Jeżeli planowane zakończenie jednej umowy nie ma potwierdzonego odpowiednika po drugiej stronie, trzeba wyjaśnić sytuację przed wykonaniem kolejnego kroku. Nie traktuj braku informacji jak potwierdzenia ciągłości sprzedaży.")
                 + p("Sprawdź także, kto prowadzi zgłoszenie i gdzie trafiają pytania o brakujące dane. Jedna osoba powinna wiedzieć, jakie potwierdzenia już są, a na jakie nadal czekasz. Ustawowa definicja, przesłanki i procedura sprzedaży rezerwowej: [[do weryfikacji prawnej]]. Materiał nie rozstrzyga, czy ten tryb wystąpi w konkretnej firmie.")
                 + li(["Brak potwierdzenia okresu nowej sprzedaży.", "Rozbieżne dane firmy lub punktu poboru.", "Niepełne pełnomocnictwo albo dokumentacja.", "Niejasny status zgłoszenia do operatora."])),
                ("koszt", "Pytaj o strukturę kosztu, nie o uniwersalną stawkę",
                 p("Nie ma tu kwoty, którą można przenieść do budżetu Twojej firmy. Poproś o właściwy dokument, datę obowiązywania i zakres rozliczenia. Nie wystarczy porównać nazwy produktu ani samej ceny paliwa. Ustal, za jaki okres i na jakiej podstawie miałoby nastąpić naliczenie poszczególnych składników.")
                 + table(["Obszar kosztu do wyjaśnienia", "Pytanie do dokumentu"], [
                     ["Cena paliwa", "Jaka stawka lub formuła i w jakim okresie?"],
                     ["Dystrybucja", "Które pozycje wynikają z dokumentów operatora?"],
                     ["Opłaty i podatki", "Jaka podstawa i sposób prezentacji kwot?"],
                     ["Okres rozliczenia", "Od jakiej daty i do jakiego zdarzenia?"],
                     ["Inne zobowiązania", "Czy istnieją osobne roszczenia z dotychczasowej umowy?"]])
                 + p("Powyższa lista jest kartą pytań, nie potwierdzeniem, że każda pozycja zostanie naliczona. Właściwy cennik i umowne lub ustawowe podstawy kosztów: [[źródło]]; zakres dla klienta: [[do weryfikacji prawnej]]. Nie publikujemy szacunku oszczędności ani porównania procentowego.")),
                ("dzialanie", "Nie naprawiaj niejasności kolejnym pochopnym pismem",
                 p("Jeżeli status jest niejasny, zbierz umowy, zgłoszenia i potwierdzenia. Zapisz chronologię korespondencji oraz listę pytań do sprzedawcy i operatora. Nie wysyłaj nowego wypowiedzenia tylko dlatego, że poprzedni dokument nie przyniósł oczekiwanej odpowiedzi. Skutki dodatkowego oświadczenia wymagają oceny w kontekście całej sprawy.")
                 + p(CAUTION)
                 + p("Dla osoby odpowiedzialnej za zakup praktycznym wynikiem jest lista sprawdzonych dokumentów, dat i kontaktów, a nie automatyczna decyzja o zmianie trybu sprzedaży. Zakres obowiązków poszczególnych stron i dostępne działania: [[do weryfikacji prawnej]].")
                 + p('Przejdź do <a href="/analiza-umowy/">analizy umowy</a> i porównaj <a href="/wiedza/jak-zmienic-sprzedawce-gazu-w-firmie/">kolejność zmiany sprzedawcy</a>. W prototypie nie przyjmujemy dokumentów ani nie prowadzimy zgłoszeń.')),
            ],
            "sources": ["[[źródło: aktualne przepisy o sprzedaży rezerwowej — do weryfikacji prawnej]]",
                        "[[źródło: właściwy cennik, umowa i informacje operatora]]"],
            "cta": ("Wyjaśnij status, zanim wykonasz kolejny krok.", "/analiza-umowy/", "Sprawdź zakres analizy umowy"),
            "priced": True,
        },
        {
            "slug": "cena-stala-czy-indeksowana-tge",
            "title": "Cena stała czy indeksowana do TGE: dla jakiego profilu zużycia",
            "answer": "Wybór między ceną stałą a indeksem TGE zależy od profilu poboru, sposobu planowania budżetu i gotowości do przyjęcia zmienności. Żaden model nie jest automatycznie najlepszy dla każdej firmy. Porównaj tę samą ilość gazu, okres dostaw, zakres ceny i warunki rozliczenia odchyleń.",
            "sections": [
                ("profil", "Zacznij od profilu, nie od wykresu",
                 p("Zbierz dostępne dane o zużyciu i opisz, kiedy zakład pracuje intensywniej. Uwzględnij sezonowość, postoje oraz planowane zmiany procesu. Sama roczna suma może ukrywać to, w których okresach koszt paliwa najbardziej wpływa na budżet. Oznacz dane historyczne osobno od prognozy, by nie traktować planu produkcji jako potwierdzonego poboru.")
                 + p("Zapytaj też, jak ustalasz ceny własnych produktów i kto monitoruje zakup energii. Firma potrzebująca punktu odniesienia dla kosztu paliwa może inaczej oceniać ryzyko niż firma gotowa regularnie analizować formułę indeksową. To pytania o sposób zarządzania, nie etykieta przypisana automatycznie do branży.")
                 + li(["Kiedy zużywasz gaz i co może zmienić ten rytm?", "Jak aktualizujesz budżet i plan produkcji?", "Kto odczyta formułę oraz sprawdzi fakturę?"])),
                ("modele", "Porównaj mechanizm obu modeli",
                 p("Cena stała oznacza uzgodnioną stawkę w opisanym zakresie, nie stałą kwotę rachunku. Przy indeksie cenę paliwa wyznacza formuła odniesiona do uzgodnionego wskaźnika oraz składników umownych. Nazwa „TGE” nie wystarczy do odtworzenia wyliczenia. Potrzebujesz konkretnego indeksu, okresu uśredniania i sposobu przypisania zużycia.")
                 + table(["Pytanie", "Cena stała", "Cena indeksowana"], [
                     ["Co stanowi punkt odniesienia?", "Stawka dla uzgodnionego zakresu", "Indeks i formuła z umowy"],
                     ["Co przy zmianie rynku?", "Stawka nie musi podążać za notowaniami", "Wpływ określa formuła"],
                     ["Co nadal sprawdzasz?", "Pobór, tolerancje i opłaty", "Pobór, tolerancje i opłaty"],
                     ["Jakie dane są potrzebne?", "Profil i okres dostaw", "Profil, okres i dokładne odniesienie"]])
                 + p("Nie porównuj stałej ceny jednej oferty z pojedynczym notowaniem bez sprawdzenia zakresu. Takie zestawienie pomija momenty poboru oraz składniki, które mogą być prezentowane inaczej. Zwróć uwagę, czy składnik handlowy jest już w cenie, aby nie dodać go ponownie.")),
                ("decyzja", "Wybierz po sprawdzeniu ograniczeń",
                 p("Przy cenie stałej rozważ, czy akceptujesz brak udziału w późniejszym spadku notowań w uzgodnionym zakresie. Przy indeksie sprawdź, jak Twoja firma poradzi sobie ze wzrostem kosztu zgodnym z formułą. Nie opieraj decyzji na zapewnieniu o pewnym kierunku rynku. Ten materiał nie jest prognozą i nie obiecuje oszczędności.")
                 + p("W obu wariantach przeczytaj zasady odchyleń wolumenu, zabezpieczeń i płatności. Ustal, co stanie się po zmianie planu produkcji oraz które opłaty pozostają poza stawką paliwa. Jeżeli chcesz dzielić decyzje, porównaj także model transzowy, ale najpierw wyznacz zasady zatwierdzania części zakupu.")
                 + p('Właściwe publiczne odniesienie potwierdź w materiałach <a href="https://tge.pl/">TGE</a>: [[nazwa indeksu i link]]. Warunki modeli poznasz na stronach <a href="/oferta/cena-stala/">ceny stałej</a>, <a href="/oferta/cena-indeksowana-tge/">ceny indeksowanej</a> i <a href="/oferta/model-transzowy/">transz</a>.')
                 + p("Do rozmowy przynieś fakturę oraz założenia poboru. Poproś o zestawienie warunków dla jednego, wspólnie ustalonego scenariusza. Dopiero wtedy różnice między ofertami będą czytelne.")),
            ],
            "sources": ['Publiczne materiały instytucjonalne: <a href="https://tge.pl/">Towarowa Giełda Energii</a>. Właściwy indeks i publikacja: [[źródło]].',
                        "[[warunki produktów PBM i zasady rozliczenia]]",
                        "[[dane zużycia i założenia klienta — bez publikacji danych poufnych]]"],
            "cta": ("Porównaj modele dla swojego zużycia.", "/wgraj-fakture/", "Przygotuj fakturę"),
            "priced": True,
        },
        {
            "slug": "art-4j-ust-3b-ms-p-kary",
            "title": "Co zmienia art. 4j ust. 3b Prawa energetycznego dla MŚP (od 21.07.2026): kary za wcześniejsze rozwiązanie umowy",
            "answer": "Ten temat wymaga walidacji prawnej. Data z tytułu, aktualne brzmienie przepisu, zakres odbiorców i skutki dla opłat są niepotwierdzone: [[do weryfikacji prawnej]]. Nie wyciągaj z tytułu wniosku, że Twoja firma może wcześniej zakończyć umowę bez kosztów. Poniżej znajdziesz listę kontrolną do analizy, nie wykładnię przepisu.",
            "notice": "WERYFIKACJA PRAWNA WYMAGANA. Tytuł zachowuje temat z briefu, nie potwierdza wejścia w życie regulacji ani jej zastosowania.",
            "sections": [
                ("przepis", "Najpierw potwierdź przepis i datę",
                 p("Zanim porównasz zapis ustawowy z umową, znajdź aktualny tekst aktu oraz właściwe przepisy zmieniające. Oznacz wersję, datę publikacji i podstawę wejścia w życie. Nie opieraj wniosku na samym tytule artykułu, streszczeniu w wyszukiwarce ani cudzym przykładzie. W tym szkicu nie przeprowadzono weryfikacji pierwotnego źródła.")
                 + p("Dokładne brzmienie art. 4j ust. 3b: [[do weryfikacji prawnej]]. Data wskazana w tytule i właściwe reguły przejściowe: [[do weryfikacji prawnej]]. Relacja nowej regulacji do umów zawartych wcześniej: [[do weryfikacji prawnej]]. Każde z tych pytań wymaga osobnej odpowiedzi; nie należy zastępować jej ogólną deklaracją o zmianie prawa.")),
                ("zakres", "Sprawdź, kogo i jakich umów dotyczy analiza",
                 p("Określenie MŚP użyte w komunikacji biznesowej nie rozstrzyga samo w sobie zastosowania konkretnego przepisu. Osoba weryfikująca powinna ustalić właściwe kryteria odbiorcy, przedmiot umowy oraz ewentualne dodatkowe warunki. Nie przypisujemy tu Twojej firmie żadnego statusu prawnego. Nie podajemy progów ani wyjątków bez potwierdzonego źródła.")
                 + table(["Pytanie do oceny", "Materiał do przygotowania", "Status"], [
                     ["Jaki jest zakres odbiorców?", "Dane firmy i właściwe definicje ustawowe", "[[do weryfikacji prawnej]]"],
                     ["Jakie umowy obejmuje przepis?", "Umowa, data zawarcia, produkt i aneksy", "[[do weryfikacji prawnej]]"],
                     ["Od kiedy i na jakich zasadach?", "Akt zmieniający i przepisy przejściowe", "[[do weryfikacji prawnej]]"],
                     ["Jak wpływa na rozliczenie?", "Klauzule i podstawa żądanej kwoty", "[[do weryfikacji prawnej]]"]])
                 + p("Do porównania przygotuj pełną umowę, regulamin i aneksy, a nie tylko akapit nazwany karą. Zaznacz każde postanowienie dotyczące zakończenia, rozliczenia oraz odpowiedzialności. Nazwa użyta w dokumencie nie zastępuje oceny podstawy i charakteru żądania. Wnioski dotyczące konkretnego zapisu pozostają do oceny prawnej.")),
                ("skutki", "Oddziel ocenę kosztu od decyzji o wysyłce",
                 p("Prawidłowo przygotowana notatka powinna wskazywać, które ustalenia są potwierdzone, które zależą od dokumentów i czego nadal nie wiadomo. Zapytaj o uzasadnienie, a nie tylko odpowiedź „można” albo „nie można”. W szkicu nie rozstrzygamy dopuszczalności opłat, ich wysokości, ograniczeń ani sposobu dochodzenia roszczeń.")
                 + p(CAUTION)
                 + p("Nawet po uzyskaniu oceny prawnej potrzebny jest plan operacyjny: właściwe dane punktów poboru, pełnomocnictwo, uzgodniony zakres nowej umowy oraz potwierdzenia czynności. Nie mieszaj oceny pojedynczej klauzuli z potwierdzeniem całego procesu zmiany sprzedawcy.")
                 + p('Jeżeli chcesz przygotować komplet do sprawdzenia, zobacz <a href="/analiza-umowy/">analizę umowy</a>. Ten prototyp nie generuje pisma i nie podejmuje działania w Twoim imieniu. Przed publikacją artykuł musi zostać uzupełniony o aktualne źródła i akceptację osoby odpowiedzialnej za treści prawne.')),
            ],
            "sources": ["[[źródło pierwotne: aktualny tekst Prawa energetycznego i art. 4j ust. 3b — do weryfikacji prawnej]]",
                        "[[źródło pierwotne: akt zmieniający, data wejścia w życie i przepisy przejściowe — do weryfikacji prawnej]]",
                        "[[akceptacja prawna: osoba, data, zakres i odwołania do przepisów]]"],
            "cta": ("Zacznij od dokumentów, nie od wypowiedzenia.", "/analiza-umowy/", "Zobacz zakres analizy"),
            "priced": True,
        },
    ]
    article_report = []
    for article in data:
        heading = group("Nagłówek artykułu",
                        h(article["title"], 1) + p(article["answer"], "gdp-lead")
                        + (p(article["notice"], "gdp-prototype-note") if article.get("notice") else "")
                        + p("Ostatnia aktualizacja: [[data]]. Autor: [[autor]]. Materiał roboczy.", "gdp-small"))
        toc = section("Spis treści", li([f'<a href="#{anchor}">{title}</a>' for anchor, title, _ in article["sections"]]))
        body = group("Treść artykułu", "".join(h(title, 2, anchor) + html for anchor, title, html in article["sections"])
                     + (ref(102) if article.get("priced") else ""), "gdp-section gdp-article-body", lock=False)
        footer = sources(article["sources"])
        ctitle, url, action = article["cta"]
        full = heading + toc + body + footer + section(ctitle, p("Przygotuj pytania i komplet dokumentów. Moduły prototypu nie przesyłają danych.") + button(action, url))
        write("posts", article["slug"], full)
        visible = re.sub(r"<!--.*?-->|<[^>]+>", " ", full, flags=re.S)
        article_report.append({"slug": article["slug"], "visible_words": len(visible.split()),
                               "lead_words": len(article["answer"].split()), "article_body_templateLock": False})
    for slug, angle in [("komentarz-rynkowy-szablon", "Co wydarzyło się na rynku"),
                         ("perspektywa-rynku-szablon", "Co sprawdzić przed decyzją zakupową")]:
        write("posts", slug,
              hero("[[tytuł komentarza]]", "[[komentarz: krótka odpowiedź o zmianie na rynku i znaczeniu dla kupującego gaz]]", cta=None)
              + section("Data i autor", p("Data publikacji: [[data]]. Ostatnia aktualizacja: [[data]].")
                        + p("Autor: [[imię i nazwisko, stanowisko]]. Zespół analiz PBM — placeholder.")
                        + p("Szablon redakcyjny, nie analiza bieżącego rynku."))
              + section(angle, p("[[komentarz]]")
                        + li(["[[obserwacja z potwierdzonym źródłem]]", "[[znaczenie dla profilu zakupu]]", "[[ograniczenie i niepewność analizy]]"]), priced=True)
              + sources(["[[źródło danych: instytucja, publikacja, data i URL]]", "[[weryfikacja merytoryczna i zatwierdzenie komentarza]]"])
              + cta())
    (CONTENT / "p12-article-review.json").write_text(json.dumps(article_report, ensure_ascii=False, indent=2) + "\n")


def main():
    patterns()
    product_pages()
    tool_pages()
    remaining_pages()
    articles()
    preserve_c_pages()
    print("Generated full P1.2 core-block sources; run build-wxr.py next.")


if __name__ == "__main__":
    main()
