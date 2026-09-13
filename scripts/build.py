#!/usr/bin/env python3
"""Build deterministic child ZIPs + self-contained Blueprint bundles from Git files."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FONT_NAMES = {"ibm-plex-sans": "IBM Plex Sans", "manrope": "Manrope", "source-sans-3": "Source Sans 3", "source-serif-4": "Source Serif 4"}

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def archive(folder, output, prefix=""):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(prefix + path.relative_to(folder).as_posix(), (2026, 9, 13, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())

def block(name, html, attrs=None):
    return f'<!-- wp:{name}' + (" " + json.dumps(attrs, ensure_ascii=False) if attrs else "") + f" -->\n{html}\n<!-- /wp:{name} -->\n"

def footer_data():
    groups = [
        ("Oferta", [("Cena stała","/oferta/cena-stala/"),("Cena indeksowana TGE","/oferta/cena-indeksowana-tge/"),("Model transzowy","/oferta/model-transzowy/"),("Umowa dla MŚP","/oferta/umowa-kompleksowa-msp/"),("Biometan: wkrótce","/oferta/biometan/")]),
        ("Narzędzia", [("Wgraj fakturę","/wgraj-fakture/"),("Kalkulator wypowiedzenia","/kalkulator-wypowiedzenia/"),("Analiza umowy","/analiza-umowy/"),("Dla agentów AI","/dla-agentow-ai/")]),
        ("Wiedza", [("Komentarz rynkowy","/komentarz-rynkowy/"),("Ceny i rynek","/category/ceny-i-rynek/"),("Zmiana sprzedawcy","/category/zmiana-sprzedawcy/"),("Umowy i wypowiedzenia","/category/umowy-i-wypowiedzenia/"),("Biometan i raportowanie","/category/biometan-i-raportowanie/"),("Sprzedaż rezerwowa","/category/sprzedaz-rezerwowa/")]),
        ("Firma", [("O nas","/o-nas/"),("Dokumenty","/dokumenty/"),("Kontakt","/kontakt/"),("Dla doradców","/dla-doradcow/")]),
    ]
    data = []
    for title, links in groups:
        items = "".join(block("list-item",f'<li><a href="{url}">{text}</a></li>') for text,url in links)
        data.append(block("heading",f'<h2 class="wp-block-heading">{title}</h2>') + block("list",f'<ul class="wp-block-list">{items}</ul>'))
    data.append(block("paragraph",'<p>[[PBM Sp. z o.o., adres, NIP, KRS, kapitał zakładowy]]</p>') + block("paragraph",'<p>Koncesja OPG nr [[ ]] wydana przez Prezesa URE. Grupa IMA Polska.</p>'))
    data.append(block("paragraph",'<p><a href="/polityka-prywatnosci/">Polityka prywatności</a> · <a href="/regulamin/">Regulamin serwisu</a> · Informacja o plikach cookie: [[slot CMP: etap 3]]</p>') + '<!-- wp:block {"ref":102} /-->\n' + block("paragraph",'<p>Paleta robocza, logo i kolory firmowe: [[dostarczy zleceniodawca]]. Prototyp etapu 1.</p>'))
    return data

def menus_data():
    return [
        {"slug":"gdp-main","locations":["menu_1","menu_mobile"],"items":[
            {"title":"Oferta","url":"/oferta/","children":[
                {"title":"Cena stała","url":"/oferta/cena-stala/"},
                {"title":"Cena indeksowana TGE","url":"/oferta/cena-indeksowana-tge/"},
                {"title":"Model transzowy","url":"/oferta/model-transzowy/"},
                {"title":"Umowa dla MŚP","url":"/oferta/umowa-kompleksowa-msp/"},
                {"title":"Biometan (wkrótce)","url":"/oferta/biometan/"}]},
            {"title":"Ceny orientacyjne","url":"/ceny-orientacyjne/"},
            {"title":"Narzędzia","url":"/wgraj-fakture/","children":[
                {"title":"Wgraj fakturę","url":"/wgraj-fakture/"},
                {"title":"Kalkulator wypowiedzenia","url":"/kalkulator-wypowiedzenia/"},
                {"title":"Analiza umowy","url":"/analiza-umowy/"},
                {"title":"Dla agentów AI","url":"/dla-agentow-ai/"}]},
            {"title":"Wiedza","url":"/wiedza/"},
            {"title":"Dla doradców","url":"/dla-doradcow/"},
            {"title":"O nas","url":"/o-nas/"},
            {"title":"Kontakt","url":"/kontakt/"}]},
        {"slug":"gdp-legal","locations":["footer"],"items":[{"title":"Polityka prywatności","url":"/polityka-prywatnosci/"},{"title":"Regulamin","url":"/regulamin/"}]}
    ]

def build(direction, tokens, activate=False):
    t = tokens[direction]
    temp = ROOT / ".runtime" / f"theme-{direction}"
    if temp.exists(): shutil.rmtree(temp)
    shutil.copytree(ROOT / "theme/gdp-child", temp)
    fontdir = temp / "assets/fonts"
    if fontdir.exists(): shutil.rmtree(fontdir)
    fontdir.mkdir(parents=True)
    fontcss = ""
    for slug in t["fonts"]:
        src = ROOT / "node_modules/@fontsource-variable" / slug
        shutil.copyfile(src / "LICENSE", fontdir / f"{slug}-LICENSE.txt")
        for subset in ["latin", "latin-ext"]:
            file = f"{slug}-{subset}-wght-normal.woff2"
            shutil.copyfile(src / "files" / file, fontdir / file)
        fontcss += f"""@font-face{{font-family:'{FONT_NAMES[slug]}';font-style:normal;font-weight:100 900;font-display:swap;src:url('assets/fonts/{slug}-latin-ext-wght-normal.woff2') format('woff2');unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF;}}
@font-face{{font-family:'{FONT_NAMES[slug]}';font-style:normal;font-weight:100 900;font-display:swap;src:url('assets/fonts/{slug}-latin-wght-normal.woff2') format('woff2');unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD;}}
"""
    sizes = [("xs","12px","12px"),("s","14px","14px"),("m","16px","18px"),("l","20px","24px"),("xl","28px","40px"),("xxl","39px","66px")]
    palette = [{"slug":k,"name":k,"color":v} for k,v in t["palette"].items()]
    theme = {
        "$schema":"https://schemas.wp.org/trunk/theme.json","version":3,
        "settings":{
            "appearanceTools":False,
            "color":{"custom":False,"customGradient":False,"defaultPalette":False,"defaultGradients":False,"palette":palette},
            "typography":{"customFontSize":False,"fluid":True,"defaultFontSizes":False,
                "fontFamilies":[{"slug":"heading","name":"Nagłówki","fontFamily":f"'{t['heading']}', serif" if direction=="C" else f"'{t['heading']}', sans-serif"},
                                {"slug":"body","name":"Tekst","fontFamily":f"'{t['body']}', sans-serif"}],
                "fontSizes":[{"slug":slug,"name":slug,"size":hi,"fluid": {"min":lo,"max":hi} if hi != lo else False} for slug,lo,hi in sizes]},
            "spacing":{"customSpacingSize":False,"defaultSpacingSizes":False,"spacingSizes":[
                {"slug":slug,"name":slug,"size":f"clamp({low}px, {vw}vw, {high}px)"} for slug,low,vw,high in [("20",8,1,12),("30",12,1.5,20),("40",18,2,28),("50",24,3,40),("60",32,4,56),("70",44,5,72),("80",56,7,100)]]},
            "layout":{"contentSize":"760px","wideSize":"1200px"}},
        "styles":{"color":{"background":"var:preset|color|base","text":"var:preset|color|contrast"},
            "typography":{"fontFamily":"var:preset|font-family|body","fontSize":"var:preset|font-size|m","lineHeight":"1.6"},
            "elements":{"heading":{"typography":{"fontFamily":"var:preset|font-family|heading"}},
                "link":{"color":{"text":"var:preset|color|primary"}},
                "button":{"color":{"background":"var:preset|color|primary","text":"#ffffff"}}}}
    }
    dump(temp / "theme.json", theme)
    css = f"""/*
Theme Name: Gaz dla Przemysłu — {direction}: {t['name']}
Template: blocksy
Version: 0.1.0-{direction}
Text Domain: gdp-child
Requires at least: 6.6
Requires PHP: 8.3
License: GPL-2.0-or-later
*/
{fontcss}
:root{{--gdp-radius:{t['radius']};}}
"""
    css += (ROOT / "theme/style-base.css").read_text() + (ROOT / f"theme/style-{direction}.css").read_text()
    (temp / "style.css").write_text(css)
    patterns = temp / "patterns"
    patterns.mkdir(exist_ok=True)
    starter_specs = [
        ("hero-produkt","Otwarcie produktu",block("heading",'<h1 class="wp-block-heading">[[nazwa produktu]]</h1>',{"level":1})+block("paragraph",'<p>[[bezpośrednia odpowiedź: dla kogo i jak działa]]</p>')),
        ("jak-to-dziala","Jak to działa",block("heading",'<h2 class="wp-block-heading">Jak to działa</h2>')+block("list",'<ol class="wp-block-list">'+''.join(block("list-item",f'<li>[[{s}]]</li>') for s in ["Dokumenty","Analiza","Warunki","Decyzja"])+'</ol>',{"ordered":True})),
        ("dla-kogo","Dla kogo",block("heading",'<h2 class="wp-block-heading">Dla kogo</h2>')+block("paragraph",'<p>[[profil zużycia i potrzeby firmy]]</p>')),
        ("ryzyka-i-ograniczenia","Ryzyka i ograniczenia",block("heading",'<h2 class="wp-block-heading">Ryzyka i ograniczenia</h2>')+block("paragraph",'<p>[[ryzyka modelu i ograniczenia umowne]]</p>')),
        ("przyklad-liczbowy","Przykład liczbowy",block("heading",'<h2 class="wp-block-heading">Przykład: dane do uzupełnienia</h2>')+block("table",'<figure class="wp-block-table gdp-price-table"><table class="has-fixed-layout"><thead><tr><th>Składnik</th><th>Wartość</th></tr></thead><tbody><tr><td>[[składnik]]</td><td>[[wartość]]</td></tr></tbody></table></figure>',{"className":"gdp-price-table"})+'<!-- wp:block {"ref":102} /-->'),
        ("tabela-porownawcza","Tabela porównawcza",block("heading",'<h2 class="wp-block-heading">Porównaj modele</h2>')+block("table",'<figure class="wp-block-table gdp-comparison-table"><table class="has-fixed-layout"><thead><tr><th>Cecha</th><th>Model A</th><th>Model B</th></tr></thead><tbody><tr><td>[[cecha]]</td><td>[[opis]]</td><td>[[opis]]</td></tr></tbody></table></figure>',{"className":"gdp-comparison-table"})),
        ("naglowek-artykulu","Nagłówek artykułu",block("heading",'<h1 class="wp-block-heading">[[tytuł artykułu]]</h1>',{"level":1})+block("paragraph",'<p>[[odpowiedź w maksymalnie 60 słowach]]</p>')+block("paragraph",'<p>Autor: [[imię i nazwisko, stanowisko]]. Aktualizacja: [[data]].</p>')),
        ("zrodla","Źródła",block("heading",'<h2 class="wp-block-heading">Źródła</h2>')+block("list",'<ul class="wp-block-list">'+block("list-item",'<li>[[źródło i link]]</li>')+'</ul>')),
    ]
    for slug, title, inner in starter_specs:
        starter = block("group",f'<div class="wp-block-group gdp-section gdp-product-content">{inner}</div>',{"metadata":{"name":title},"templateLock":"contentOnly","className":"gdp-section gdp-product-content"})
        (patterns / f"{slug}.php").write_text(f"<?php\n/**\n * Title: {title}\n * Slug: gdp/{slug}\n * Categories: gdp\n * Block Types: core/group\n */\n?>\n{starter}\n")
    mods = json.loads((ROOT / "config/builder-base.json").read_text())
    mapping = ["primary","secondary","contrast","contrast","line","surface","base","base"]
    mods["colorPalette"] = {f"color{i+1}":{"color":t["palette"][key]} for i,key in enumerate(mapping)}
    mods.update({"single_page_structure":"type-4","single_page_content_style":"wide","single_page_hero_enabled":"no",
        "single_page_vertical_spacing":"none","maxSiteWidth":1200,
        "gdp_mobile_cta_label":"Oferta w 24 h"})
    mods.update({"single_blog_post_hero_enabled":"no","single_blog_post_structure":"type-4","single_blog_post_content_style":"wide"})
    for item in mods["header_placements"]["sections"][0]["items"]:
        if item["id"]=="button": item["values"]["header_button_link"]="/wgraj-fakture/"
    dump(ROOT / "config/theme_mods_main.json", mods)
    bundle = ROOT / "dist/main"
    bundle.mkdir(parents=True, exist_ok=True)
    archive(temp, bundle / "gdp-child.zip", "gdp-child/")
    shutil.copyfile(ROOT / "content/site.wxr", bundle / "site.wxr")
    widgets = footer_data()
    menus = menus_data()
    dump(ROOT / "config/widgets.json",widgets)
    dump(ROOT / "config/menus.json", menus)
    blueprint = {
        "$schema":"https://playground.wordpress.net/blueprint-schema.json",
        "meta":{"title":f"Gaz dla Przemysłu · P1.2 · {direction}: {t['name']}","author":"agent","description":"Pełny prototyp bez wtyczek. Paleta robocza. Brak wysyłania danych."},
        "preferredVersions":{"php":"8.3","wp":"latest"},
        "features":{"networking":True},
        "landingPage":"/","login":True,
        "constants":{"GDP_PROTOTYPE":True,"WP_DEBUG":True,"WP_DEBUG_LOG":True,"WP_DEBUG_DISPLAY":False},
        "steps":[
            {"step":"installTheme","themeData":{"resource":"wordpress.org/themes","slug":"blocksy"},"options":{"activate":False}},
            {"step":"installTheme","themeData":{"resource":"bundled","path":"/gdp-child.zip"},"options":{"activate":True}},
            {"step":"writeFile","path":"/tmp/site.wxr","data":{"resource":"bundled","path":"/site.wxr"}},
            {"step":"runPHP","code":(ROOT / "scripts/import-wxr.php").read_text()},
            {"step":"writeFile","path":"/tmp/theme_mods.json","data":json.dumps(mods,ensure_ascii=False)},
            {"step":"writeFile","path":"/tmp/menus.json","data":json.dumps(menus,ensure_ascii=False)},
            {"step":"writeFile","path":"/tmp/widgets.json","data":json.dumps(widgets,ensure_ascii=False)},
            {"step":"runPHP","code":(ROOT / "scripts/setup.php").read_text()},
            {"step":"wp-cli","command":"wp user create redaktor redaktor@example.invalid --role=editor --user_pass=GDP-prototyp-2026"},
            {"step":"wp-cli","command":"wp rewrite flush"},
        ]
    }
    dump(bundle / "blueprint.json",blueprint)
    dump(ROOT / "blueprints/main.json", blueprint)
    archive(bundle, ROOT / "dist/etap1-v0.1.zip")
    # Test bundle adds only read-only audit artifacts. The public candidate above stays clean.
    test = copy.deepcopy(blueprint)
    test["steps"] += [
        {"step":"runPHP","code": "<?php ob_start(); ?>" + (ROOT / "scripts/verify-blocks.php").read_text() + "\n<?php $report = ob_get_clean(); file_put_contents('/wordpress/gdp-audit.json', $report); ?>"},
    ]
    # Avoid nested PHP boundaries when source has no closing tag.
    verify = (ROOT / "scripts/verify-blocks.php").read_text().removeprefix("<?php")
    test["steps"][-1]["code"] = "<?php ob_start();\n" + verify + "\n$report = ob_get_clean(); file_put_contents('/wordpress/gdp-audit.json', $report);"
    testfolder = ROOT / ".runtime/test-main"
    testfolder.mkdir(parents=True,exist_ok=True)
    for f in ["gdp-child.zip","site.wxr"]: shutil.copyfile(bundle/f,testfolder/f)
    dump(testfolder/"blueprint.json",test)
    if activate:
        shutil.rmtree(ROOT / "theme/gdp-child")
        shutil.copytree(temp, ROOT / "theme/gdp-child")
        shutil.copyfile(bundle/"gdp-child.zip", ROOT/"dist/gdp-child.zip")
    return {"direction":direction,"wxr_sha256":hashlib.sha256((bundle/"site.wxr").read_bytes()).hexdigest(),"bundle_sha256":hashlib.sha256((ROOT/"dist/etap1-v0.1.zip").read_bytes()).hexdigest()}

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--active",choices=["C"],default="C",help="Od P1.2 rozwijany jest wyłącznie wybrany C.")
    args=p.parse_args()
    subprocess.run(["python3",str(ROOT/"scripts/build-wxr.py")],check=True)
    tokens=json.loads((ROOT/"config/tokens.json").read_text())
    reports=[build("C",tokens, True)]
    dump(ROOT/"docs/build-manifest.json",reports)
    print(json.dumps(reports,indent=2))
