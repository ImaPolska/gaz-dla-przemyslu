#!/usr/bin/env python3
"""Index placeholders in canonical sources, not repeated WXR/ZIP/blueprint copies."""
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
rows=[]
def scan(text, source, default):
    stack=[]
    for m in re.finditer(r'<!--\s*(/?)wp:([a-z-]+)(.*?)-->|(\[\[[\s\S]*?\]\])',text):
        if m.group(4):
            section=next((n for n in stack if n),default)
            rows.append([source,section,text[:m.start()].count('\n')+1,m.group(4)])
        elif m.group(2)=='group':
            if m.group(1):
                if stack: stack.pop()
            else:
                raw=m.group(3).strip().rstrip('/').strip()
                try: attrs=json.loads(raw) if raw else {}
                except json.JSONDecodeError: attrs={}
                stack.append(attrs.get('metadata',{}).get('name',''))

for file in sorted((root/'content').glob('*/*.html')):
    scan(file.read_text(),str(file.relative_to(root)),file.stem)
for i,content in enumerate(json.loads((root/'config/widgets.json').read_text()),1):
    scan(content,f'config/widgets.json, widget {i}',f'Stopka: kolumna/wiersz {i}')
for file in sorted((root/'theme/gdp-child/patterns').glob('*.php')):
    scan(file.read_text(),str(file.relative_to(root)),'Wzorzec startowy do P1.2')

text=f"""# Otwarte pozycje

Stan P1.1, 2026-09-13. **{len(rows)} wystąpień** `[[ ]]` w kanonicznych źródłach: treść HTML, konfiguracja widgetów i wzorce startowe. To nie jest liczba niezależnych pytań. Wspólny wzorzec liczony jest raz w źródle, a nie ponownie na każdej stronie; WXR, ZIP i trzy blueprinty nie są ponownie liczone.

## Decyzja teraz

- Wybór kierunku A, B, C lub kombinacji. Nie rekomendujemy żadnego.
- Publiczne repo oraz trzy publiczne linki pozostają niedostarczone: środowisko nie ma konta agenta do publikacji. Nie prosimy o dostęp do infrastruktury, kont, domeny, poczty ani HubSpot.

## Grupy danych do uzupełnienia później

- Logo i kolory firmowe: P1.3; teraz obowiązują palety robocze.
- Dane rejestrowe PBM, adresy kontaktowe i numer koncesji OPG: P1.3.
- Autorzy, daty i zatwierdzone komentarze rynkowe: P1.3.
- Próg segmentacji `[[X]]` GWh/rok: P1.2.
- Parametry produktów i cennika: do zatwierdzenia; niczego nie wypełniono fikcyjnymi danymi. Lista produktów przyjęta domyślnie z briefu.
- Zgody, polityka, regulamin: treści zleceniodawcy, finalizacja prawna poza P1.1.
- Zdjęcia aktywów: opcjonalnie P1.3; obecnie brak zdjęć i zewnętrznych osadzeń.
- Wzorce startowe z placeholderami: do rozwinięcia w P1.2, nie są ukończonymi artykułami.

## Rejestr wystąpień

| Plik | Sekcja | Linia źródła | Placeholder |
|---|---|---:|---|
"""
for source,section,line,value in rows:
    text+=f'| `{source}` | {section.replace("|","/")} | {line} | `{value.replace("|","/")}` |\n'
(root/'docs/open-items.md').write_text(text)
(root/'docs/qa/open-items.json').write_text(json.dumps({'count':len(rows),'items':rows},ensure_ascii=False,indent=2)+'\n')
print(f'{len(rows)} placeholder occurrences indexed')
