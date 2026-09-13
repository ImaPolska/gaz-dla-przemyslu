#!/usr/bin/env python3
"""Build the P1.2 direction C content export using only Python's standard library.

Run from any directory: python3 scripts/build-wxr.py
Source of truth: content/pages, content/posts, content/patterns.
All three visual directions MUST import this same WXR file.

wp:post_id is the standard WXR source ID. The explicit wp:import_id and
_gdp_import_id metadata also expose the intended deterministic ID to the
controlled importer. Importers may remap occupied IDs: remap every nested
core/block ref using the source-ID to actual-ID map after import.

The stable technical timestamp below is NOT a publication date or market datum.
Never expose native post dates or native author metadata in this prototype:
the editable content explicitly displays [[data]] and a labelled author stub.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from xml.dom import minidom
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
BASE_URL = "https://gazdlaprzemyslu.example.invalid"
TECHNICAL_DATE = "2000-01-01 00:00:00"
SOURCE_SPEC = (
    "gazdlaprzemyslu_etap1_instrukcja_agenta.md, "
    "sections 1.3, 5, 7, 8, 9, 10, 14, 16; P1.2 direction C"
)
NS = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wfw": "http://wellformedweb.org/CommentAPI/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "wp": "http://wordpress.org/export/1.2/",
}

# Explicit order: patterns first, then parent pages before their children.
# Slugs and IDs form the import contract shared with the blueprint setup.
ITEMS = [
    (101, "wp_block", "upload", "Slot: upload faktury", 0),
    (102, "wp_block", "disclaimer", "Zastrzeżenie cen", 0),
    (103, "wp_block", "final-cta", "CTA: wgraj fakturę", 0),
    (104, "wp_block", "pricing", "Slot: tabela cen", 0),
    (105, "wp_block", "segments", "Wzorzec: segmenty", 0),
    (106, "wp_block", "trust", "Pasek zaufania", 0),
    (107, "wp_block", "faq-product", "FAQ: produkt", 0),
    (108, "wp_block", "calculator", "Slot: kalkulator wypowiedzenia", 0),
    (109, "wp_block", "analysis", "Slot: analiza umowy", 0),
    (110, "wp_block", "advisor", "Slot: formularz doradcy", 0),
    (201, "page", "start", "Start", 0),
    (202, "page", "oferta", "Oferta", 0),
    (203, "page", "cena-stala", "Cena stała", 202),
    (204, "page", "kontakt", "Kontakt", 0),
    (205, "page", "wiedza", "Wiedza", 0),
    (206, "page", "wgraj-fakture", "Wgraj fakturę", 0),
    (207, "page", "polityka-prywatnosci", "Polityka prywatności", 0),
    (208, "page", "cena-indeksowana-tge", "Cena indeksowana TGE", 202),
    (209, "page", "model-transzowy", "Model transzowy", 202),
    (210, "page", "umowa-kompleksowa-msp", "Umowa kompleksowa dla MŚP", 202),
    (211, "page", "biometan", "Biometan — wkrótce", 202),
    (212, "page", "ceny-orientacyjne", "Ceny orientacyjne", 0),
    (213, "page", "kalkulator-wypowiedzenia", "Kalkulator terminu wypowiedzenia", 0),
    (214, "page", "analiza-umowy", "Analiza umowy", 0),
    (215, "page", "dla-kogo", "Gaz dla Twojej firmy", 0),
    (216, "page", "przemysl", "Gaz dla przemysłu", 215),
    (217, "page", "msp", "Gaz dla MŚP", 215),
    (218, "page", "dla-doradcow", "Dla doradców energetycznych", 0),
    (219, "page", "dla-agentow-ai", "Dla agentów AI", 0),
    (220, "page", "komentarz-rynkowy", "Komentarz rynkowy", 0),
    (221, "page", "o-nas", "O nas", 0),
    (222, "page", "dokumenty", "Dokumenty", 0),
    (223, "page", "regulamin", "Regulamin serwisu", 0),
    (224, "page", "blad-404", "Nie znaleziono strony", 0),
    (225, "page", "archiwum-kategorii", "Archiwum kategorii — szablon", 0),
    (226, "page", "wyniki-wyszukiwania", "Wyniki wyszukiwania", 0),
    (301, "post", "komentarz-rynkowy-szablon", "[[tytuł komentarza]]", 0),
    (302, "post", "perspektywa-rynku-szablon", "[[tytuł komentarza]]", 0),
    (303, "post", "jak-zmienic-sprzedawce-gazu-w-firmie", "Jak zmienić sprzedawcę gazu w firmie: kolejność kroków i terminy", 0),
    (304, "post", "okres-wypowiedzenia-klauzula-prolongacyjna", "Okres wypowiedzenia i klauzula prolongacyjna w umowie na gaz: jak policzyć termin", 0),
    (305, "post", "sprzedaz-rezerwowa-gazu", "Sprzedaż rezerwowa gazu: kiedy grozi i ile kosztuje", 0),
    (306, "post", "cena-stala-czy-indeksowana-tge", "Cena stała czy indeksowana do TGE: dla jakiego profilu zużycia", 0),
    (307, "post", "art-4j-ust-3b-ms-p-kary", "Co zmienia art. 4j ust. 3b Prawa energetycznego dla MŚP (od 21.07.2026): kary za wcześniejsze rozwiązanie umowy — do weryfikacji prawnej", 0),
]
CATEGORIES = [
    (50, "komentarz-rynkowy", "Komentarz rynkowy"),
    (51, "zmiana-sprzedawcy", "Zmiana sprzedawcy"),
    (52, "umowy-i-wypowiedzenia", "Umowy i wypowiedzenia"),
    (53, "ceny-i-rynek", "Ceny i rynek"),
    (54, "biometan-i-raportowanie", "Biometan i raportowanie (CSRD/ETS)"),
    (55, "sprzedaz-rezerwowa", "Sprzedaż rezerwowa"),
]
POST_CATEGORIES = {
    301: ["komentarz-rynkowy"], 302: ["komentarz-rynkowy"],
    303: ["zmiana-sprzedawcy"], 304: ["umowy-i-wypowiedzenia"],
    305: ["sprzedaz-rezerwowa"], 306: ["ceny-i-rynek"],
    307: ["umowy-i-wypowiedzenia"],
}
CATEGORY_ROUTES = {
    slug: "/komentarz-rynkowy/" if slug == "komentarz-rynkowy" else f"/category/{slug}/"
    for _, slug, _ in CATEGORIES
}
FOLDERS = {"wp_block": "patterns", "page": "pages", "post": "posts"}
TOKEN = re.compile(
    r"<!--\s*(/?)wp:([a-zA-Z0-9_/-]+)"
    r"(?:\s+(\{.*?\}))?\s*(/?)-->",
    flags=re.DOTALL,
)
PLACEHOLDER = re.compile(r"\[\[[\s\S]*?\]\]")
BANNED_BLOCKS = {"core/html", "core/freeform", "core/shortcode"}
BANNED_PHRASES = [
    "w dzisiejszych czasach",
    "kompleksowe rozwiązania",
    "lider rynku",
    "innowacyjny",
    "game-changer",
]


def canonical_name(short_name: str) -> str:
    return short_name if "/" in short_name else "core/" + short_name


def source_path(kind: str, slug: str) -> Path:
    return CONTENT / FOLDERS[kind] / f"{slug}.html"


def public_path(kind: str, slug: str, parent: int = 0) -> str:
    if kind == "wp_block":
        return f"/?post_type=wp_block&name={slug}"
    if slug == "start":
        return "/"
    if kind == "post":
        return f"/wiedza/{slug}/"
    if parent:
        item = next(i for i in ITEMS if i[0] == parent)
        return public_path(item[1], item[2], item[4]) + slug + "/"
    return f"/{slug}/"


def check_markup(path: Path, markup: str, kind: str) -> dict:
    """Structural checks, not a substitute for Gutenberg JS save validation."""
    errors = []
    counts = Counter()
    stack = []
    top_sections = []
    refs = []
    previous_end = 0
    for token in TOKEN.finditer(markup):
        closing, short, raw_attrs, self_closing = token.groups()
        name = canonical_name(short)
        # Nonempty bytes between top-level blocks must never be freeform HTML.
        if not stack and markup[previous_end:token.start()].strip():
            errors.append("Nonempty content outside top-level block comments")
        previous_end = token.end()
        if closing:
            if not stack or stack[-1] != name:
                errors.append(f"Mismatched closing block: {name}")
            else:
                stack.pop()
            continue
        attrs = json.loads(raw_attrs) if raw_attrs else {}
        counts[name] += 1
        if name in BANNED_BLOCKS or not name.startswith("core/"):
            errors.append(f"Forbidden block: {name}")
        if not stack:
            top_sections.append(attrs.get("metadata", {}).get("name"))
            if name != "core/group":
                errors.append("Top-level section is not core/group")
            article_body = kind == "post" and attrs.get("metadata", {}).get("name") == "Treść artykułu" and attrs.get("templateLock") is False
            if attrs.get("templateLock") != "contentOnly" and not article_body:
                errors.append("Top-level section is not contentOnly")
            if not attrs.get("metadata", {}).get("name"):
                errors.append("Top-level section has no metadata.name")
        if name == "core/block":
            refs.append(attrs.get("ref"))
            if not stack:
                errors.append("Synced reference outside a named section")
        if not self_closing:
            stack.append(name)
    if stack:
        errors.append(f"Unclosed blocks: {stack}")
    if markup[previous_end:].strip():
        errors.append("Nonempty content after final block")
    if not counts:
        errors.append("No blocks")
    h1_count = len(re.findall(r"<h1(?:\s|>)", markup))
    h1_count += sum(1 for t in TOKEN.finditer(markup)
                    if t.group(2) == "query-title" and not t.group(1)
                    and json.loads(t.group(3) or "{}").get("level", 1) == 1)
    if kind in {"page", "post"} and h1_count != 1:
        errors.append(f"Expected one h1, found {h1_count}")
    if kind == "wp_block" and h1_count:
        errors.append("Synced patterns must not add an h1")
    if re.search(r"\sstyle\s*=", markup, re.I):
        errors.append("Inline CSS found")
    if re.search(r"<(?:input|textarea|select|form)\b", markup, re.I):
        errors.append("Real form element found")
    if re.search(
        r"(?<!\[)\[(?!\[)/?[a-z_][a-z0-9_-]*(?:\s[^\]]*)?\](?!\])",
        PLACEHOLDER.sub("", markup),
        re.I,
    ):
        errors.append("Possible shortcode found")
    for phrase in BANNED_PHRASES:
        if phrase in markup.lower():
            errors.append(f"Forbidden wording: {phrase}")
    for table in re.findall(r"<table\b[\s\S]*?</table>", markup):
        if "<thead>" not in table:
            errors.append("Table without thead")
    for token in TOKEN.finditer(markup):
        closing, short, raw_attrs, self_closing = token.groups()
        if closing or self_closing:
            continue
        attrs = json.loads(raw_attrs) if raw_attrs else {}
        expected_classes = attrs.get("className", "").split()
        if not expected_classes:
            continue
        tag = re.match(r"\s*<[^!][^>]*>", markup[token.end():])
        if not tag:
            errors.append(f"Missing HTML wrapper for {short}")
            continue
        match = re.search(r'\bclass="([^"]*)"', tag.group())
        actual_classes = match.group(1).split() if match else []
        for name in expected_classes:
            if name not in actual_classes:
                errors.append(f"{short}: className {name} absent from saved HTML")
    if errors:
        raise ValueError(f"{path.relative_to(ROOT)}: " + "; ".join(errors))
    return {
        "file": str(path.relative_to(ROOT)),
        "blocks": dict(sorted(counts.items())),
        "h1_count": h1_count,
        "top_sections": top_sections,
        "refs": refs,
        "placeholders": PLACEHOLDER.findall(markup),
        "sha256": hashlib.sha256(markup.encode("utf-8")).hexdigest(),
    }


def cdata(value: str) -> str:
    return "<![CDATA[" + value.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def tag(name: str, value: object, raw: bool = False) -> str:
    text = str(value)
    return f"<{name}>{cdata(text) if raw else escape(text)}</{name}>"


def postmeta(key: str, value: str) -> str:
    return (
        "<wp:postmeta>"
        + tag("wp:meta_key", key, True)
        + tag("wp:meta_value", value, True)
        + "</wp:postmeta>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CONTENT / "site.wxr")
    parser.add_argument(
        "--report", type=Path, default=CONTENT / "build-report.json"
    )
    args = parser.parse_args()
    report = {
        "scope": "P1.2 full content; direction C",
        "source_specification": SOURCE_SPEC,
        "technical_timestamp": TECHNICAL_DATE,
        "timestamp_note": (
            "Import bookkeeping only. Visible dates remain [[data]]. "
            "Native theme date/author metadata must be disabled."
        ),
        "validation_scope": (
            "Source structural checks only. Gutenberg save validation, "
            "rendered accessibility and runtime checks are separate."
        ),
        "notes": [
            "Home Query Loop requests three posts; only two placeholder market posts exist.",
            "Five draft knowledge articles; legal facts/terms remain explicit placeholders.",
            "FAQ answers use paragraph pattern overrides. FAQ questions bind native "
            "Details summary via core/pattern-overrides; main theme supplies "
            "block_bindings_supported_attributes_core/details ['summary'] support "
            "for the WordPress 7.1 runtime. Runtime edit/reload test is required.",
            "Existing IDs can be remapped by an importer. Remap nested core/block refs.",
            "Acquisition navigation points to product/tool landings. Inactive module actions point to /kontakt/; no data is submitted.",
            "ct_page_title=no is set for pages and posts to avoid duplicate visible titles.",
            "Render page_for_posts post_content through home.php. Market archive body is page source 220.",
            "Article prose group Treść artykułu has templateLock false: narrow exception required by editing test 14.",
        ],
        "items": [],
    }
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" '
        + " ".join(f'xmlns:{key}="{value}"' for key, value in NS.items())
        + ">",
        "<channel>",
        tag("title", "Gaz dla Przemysłu"),
        tag("link", BASE_URL),
        tag("description", "PBM Sp. z o.o., Grupa IMA Polska. Prototyp P1.2, kierunek C."),
        tag("language", "pl-PL"),
        tag("wp:wxr_version", "1.2"),
        tag("wp:base_site_url", BASE_URL),
        tag("wp:base_blog_url", BASE_URL),
        "<wp:author>",
        tag("wp:author_id", 1),
        tag("wp:author_login", "admin", True),
        tag("wp:author_email", "prototype@example.invalid", True),
        tag("wp:author_display_name", "Zespół analiz PBM (placeholder)", True),
        tag("wp:author_first_name", "", True),
        tag("wp:author_last_name", "", True),
        "</wp:author>",
    ]
    for term_id, slug, name in CATEGORIES:
        parts.extend(["<wp:category>", tag("wp:term_id", term_id),
                      tag("wp:category_nicename", slug, True),
                      tag("wp:category_parent", "", True),
                      tag("wp:cat_name", name, True), "</wp:category>"])
    all_ids = {item[0] for item in ITEMS}
    all_paths = {public_path(kind, slug, parent) for _, kind, slug, _, parent in ITEMS} | set(CATEGORY_ROUTES.values())
    for import_id, kind, slug, title, parent in ITEMS:
        path = source_path(kind, slug)
        markup = path.read_text(encoding="utf-8").strip() + "\n"
        result = check_markup(path, markup, kind)
        for ref in result["refs"]:
            if ref not in all_ids:
                raise ValueError(f"Unknown synced pattern ID {ref} in {path}")
        for href in re.findall(r'\bhref="([^"]+)"', markup):
            path_only = href.split("#", 1)[0]
            if path_only.startswith("/") and path_only not in all_paths:
                raise ValueError(f"Local link has no P1.2 destination: {href} in {path}")
        result.update({
            "import_id": import_id,
            "post_type": kind,
            "slug": slug,
            "title": title,
            "parent_import_id": parent,
            "public_path": public_path(kind, slug, parent),
            "categories": POST_CATEGORIES.get(import_id, []),
        })
        report["items"].append(result)
        parts.extend([
            "<item>",
            tag("title", title, True),
            tag("link", BASE_URL + public_path(kind, slug, parent)),
            tag("dc:creator", "admin", True),
            f'<guid isPermaLink="false">{BASE_URL}/?p={import_id}</guid>',
            tag("description", ""),
            tag("content:encoded", markup, True),
            tag("excerpt:encoded", "[[komentarz]]" if import_id in (301, 302) else "", True),
            tag("wp:post_id", import_id),
            tag("wp:import_id", import_id),
            tag("wp:post_date", TECHNICAL_DATE, True),
            tag("wp:post_date_gmt", TECHNICAL_DATE, True),
            tag("wp:post_modified", TECHNICAL_DATE, True),
            tag("wp:post_modified_gmt", TECHNICAL_DATE, True),
            tag("wp:comment_status", "closed", True),
            tag("wp:ping_status", "closed", True),
            tag("wp:post_name", slug, True),
            tag("wp:status", "publish", True),
            tag("wp:post_parent", parent),
            tag("wp:menu_order", 0),
            tag("wp:post_type", kind, True),
            tag("wp:post_password", "", True),
            tag("wp:is_sticky", 0),
            postmeta("_gdp_import_id", str(import_id)),
            postmeta("_gdp_source_file", str(path.relative_to(ROOT))),
        ])
        if kind in {"page", "post"}:
            parts.append(postmeta("ct_page_title", "no"))
        if kind == "post":
            category_names = {slug: name for _, slug, name in CATEGORIES}
            for category in POST_CATEGORIES[import_id]:
                parts.append(f'<category domain="category" nicename="{category}">'
                             + cdata(category_names[category]) + "</category>")
        # wp_block without wp_pattern_sync_status=unsynced is a synced pattern.
        parts.append("</item>")
    parts.extend(["</channel>", "</rss>"])
    xml = "\n".join(parts) + "\n"
    tree = ET.fromstring(xml)
    if len(tree.findall("./channel/item")) != len(ITEMS):
        raise ValueError("Unexpected WXR item count")
    # Ensure the generated XML is parseable by both common stdlib parsers.
    minidom.parseString(xml.encode("utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(xml, encoding="utf-8")
    report["wxr_sha256"] = hashlib.sha256(xml.encode("utf-8")).hexdigest()
    report["item_counts"] = dict(Counter(item[1] for item in ITEMS))
    report["css_classes"] = sorted({
        name
        for item in report["items"]
        for classes in re.findall(
            r'class="([^"]*)"', (ROOT / item["file"]).read_text(encoding="utf-8")
        )
        for name in classes.split()
        if name.startswith("gdp-")
    })
    report["result"] = "PASS (structural source checks)"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "stage": "P1.2", "direction": "C", "schema_version": 1,
        "items": [{"source_id": i[0], "import_id": i[0], "kind": i[1],
                   "slug": i[2], "title": i[3], "parent": i[4],
                   "parent_import_id": i[4], "path": public_path(i[1], i[2], i[4]),
                   "public_path": public_path(i[1], i[2], i[4]),
                   "source_file": str(source_path(i[1], i[2]).relative_to(ROOT)),
                   "categories": POST_CATEGORIES.get(i[0], [])} for i in ITEMS],
        "map_paths": sorted(p for p in all_paths if not p.startswith("/?")),
        "categories": [{"source_id": tid, "slug": slug, "name": name,
                        "route": CATEGORY_ROUTES[slug]} for tid, slug, name in CATEGORIES],
        "category_routes": CATEGORY_ROUTES,
        "front_page": {"source_id": 201, "slug": "start"},
        "posts_page": {"source_id": 205, "slug": "wiedza", "render_post_content": True},
        "not_found": {"source_id": 224, "slug": "blad-404", "http_status": 404,
                      "note": "Render this source page content from 404.php; source page itself has normal import path."},
        "category_archive_template": {"source_id": 225, "slug": "archiwum-kategorii",
                                      "dynamic_h1": "core/query-title level 1", "query_inherit": True},
        "market_archive": {"source_id": 220, "slug": "komentarz-rynkowy",
                           "category_source_id": 50, "route": "/komentarz-rynkowy/",
                           "note": "Actual category archive; use page 220 post_content as body. Remap query.taxQuery.category IDs."},
        "post_permalink": "/wiedza/%postname%/",
        "query_term_remapping": "Remap every nested core/query attrs.query.taxQuery.category source term ID after import, including home and archive body.",
        "article_editing_exception": {"group_metadata_name": "Treść artykułu",
                                      "templateLock": False, "post_source_ids": [303,304,305,306,307],
                                      "reason": "Required editing test 14: Editor inserts paragraph and 3×3 table under second body heading. Article layout/header/sources/CTA remain contentOnly."},
        "overrides": {"faq_answers": "core/paragraph bindings.__default core/pattern-overrides",
                       "faq_questions": "Pytanie FAQ 1..6: native core/details summary bound via __default core/pattern-overrides. Requires main theme block_bindings_supported_attributes_core/details ['summary']; verify in WordPress 7.1 edit/reload.",
                       "cta": ["Tytuł CTA", "Podtytuł CTA"],
                       "pricing": ["Data aktualizacji cen"],
                       "segment_trust": "Named heading/paragraph bindings in pattern sources."},
        "technical_dates": "WXR 2000-01-01 is import bookkeeping, never visible; content uses [[data]] and [[autor]].",
        "legal_validation": "Article 307 target date/law/scope/consequences not verified. Explicit [[do weryfikacji prawnej]] retained; not legal advice.",
        "inactive_slots": "Only core blocks; actions /kontakt/; no upload, calculator, newsletter, CRM, endpoint or PDF download is active.",
        "preserved": ["C homepage core structure/content", "cena-stala core structure/content"],
    }
    (CONTENT / "p12-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {args.output} ({len(ITEMS)} items)")
    print(f"Saved structural validation and import map: {args.report}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        raise SystemExit(1)
