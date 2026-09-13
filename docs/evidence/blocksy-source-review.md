# Blocksy free: source-level findings for gdp-child

Inspected 2026-09-13: **Blocksy 2.1.57**, downloaded, not installed, from [the WordPress.org theme package](https://downloads.wordpress.org/theme/blocksy.latest-stable.zip); local source: `/home/user/workspace/vendor/blocksy/` (`style.css:7`).
Also downloaded **Companion 2.1.57 for source inspection only**, not installed, from [the WordPress.org Companion package](https://downloads.wordpress.org/plugin/blocksy-companion.latest-stable.zip); local source: `/home/user/workspace/vendor/blocksy-companion/`.
Read the entire supplied stage-1 specification and `vendor/agent-skills/skills/{wp-playground,blueprint}/SKILL.md`, plus Playground CLI reference.

## Critical conclusions

1. Header/Footer Builder, menus, CTA button, text logo, six footer widget areas and four-column rows **work in theme alone**; native sticky functionality **does not**—Companion supplies its options and runtime hooks. [Theme builder](vendor/blocksy/inc/components/customizer-builder.php), [Companion header feature](vendor/blocksy-companion/framework/features/header.php)
2. With `gdp-child` active, write **`theme_mods_gdp-child`**, not only `theme_mods_blocksy`; `set_theme_mod()` after child activation is the robust route because Blocksy reads ordinary `get_theme_mods()`. [Database reader, lines 8–28](vendor/blocksy/inc/classes/database.php)
3. Google Fonts can be disabled in child `functions.php` without any plugin using `add_filter('blocksy:typography:google:use-remote', '__return_false');`; this gates both frontend and editor Google CSS loading. [Fonts manager, lines 115–151](vendor/blocksy/inc/css/fonts-manager.php)
4. Installed `@wp-playground/blueprints` **3.1.53** unconditionally inserts `installPlugin: wordpress-importer` before `importWxr`; `importer: "data-liberation"` does **not** evade this and is ignored by its current handler. Therefore do not put `importWxr` in a strict zero-plugin blueprint; use the parent's controlled WXR `runPHP` importer and document the deviation. [Extracted compiler, lines 344–359](vendor/blueprints-source/compile-v1.ts), [extracted importer, lines 89–122](vendor/blueprints-source/import-wxr.ts)

## 1. Exact builder data structure

`header_placements` and `footer_placements` are **top-level theme mods**, each containing `{current_section, sections:[...]}`; the section's `items` is an **array of `{id, values}`**, not an object keyed by component IDs. [Header structure, lines 9–241](vendor/blocksy/inc/components/builder/header-logic.php), [footer structure, lines 170–224](vendor/blocksy/inc/components/builder/footer-logic.php)

Canonical header section:

```json
{
  "id": "type-1",
  "mode": "placements",
  "items": [
    {"id":"logo","values":{"has_site_title":"yes","has_tagline":"no","custom_logo":""}},
    {"id":"menu","values":{"menu":"blocksy_location"}},
    {"id":"mobile-menu","values":{"menu":"blocksy_location"}},
    {"id":"button","values":{"header_button_text":"Wgraj fakturę","header_button_link":"/wgraj-fakture/","header_button_size":"small"}},
    {"id":"middle-row","values":{"headerRowHeight":{"desktop":88,"tablet":72,"mobile":72}}}
  ],
  "settings": {},
  "desktop": [],
  "mobile": []
}
```

The two empty device arrays above are **shape illustration only**; populate both with four row objects: `top-row`, `middle-row`, `bottom-row`, `offcanvas`. Ordinary row shape is `{"id":"middle-row","placements":[{"id":"start","items":["logo"]},{"id":"middle","items":["menu"]},{"id":"end","items":["button"]},{"id":"start-middle","items":[]},{"id":"end-middle","items":[]}]}`; offcanvas has only `{"id":"offcanvas","placements":[{"id":"start","items":["mobile-menu"]}]}`. Mobile middle row uses `start:["logo"]`, `middle:[]`, `end:["button","trigger"]`; desktop offcanvas is empty. [Canonical row factory, lines 92–241](vendor/blocksy/inc/components/builder/header-logic.php)

**Complete, non-truncated, machine-readable minimal configuration** is generated at `/home/user/workspace/vendor/blocksy-minimal-theme-mods.json` by `/home/user/workspace/vendor/make-blocksy-minimal.py`; use this file rather than the illustrative section above.

Use `type-1` for the default frontend section: `current_section` alone does not choose the frontend header/footer; each frontend selector defaults to `type-1` through its filter. [Header selector, lines 372–385](vendor/blocksy/inc/components/builder/header-logic.php), [footer selector, lines 257–270](vendor/blocksy/inc/components/builder/footer-logic.php)

The safest way to obtain canonical empty rows in a runtime setup script is to call `$header = blocksy_manager()->header_builder->get_default_value();` and then alter placements and item values; footer has an analogous `footer_builder->get_default_value()`. **Do not put item values under the row object**: the renderer searches the section-wide `items` array for the matching `id`. [Item lookup, lines 174–196](vendor/blocksy/inc/components/builder/builder-renderer.php)

## 2. Apply mods only after activating the child; resolve menu IDs late

Recommended one-time setup, after child activation and menu creation/import:

```php
require '/wordpress/wp-load.php';
if (get_stylesheet() !== 'gdp-child' || get_template() !== 'blocksy') {
    throw new RuntimeException('Unexpected active theme');
}
$mods = json_decode(file_get_contents('/tmp/theme_mods.json'), true, 512, JSON_THROW_ON_ERROR);
foreach ($mods as $key => $value) {
    set_theme_mod($key, $value);
}
// Resolve imported menu terms by stable slug, never hard-code numeric WXR IDs.
$main = wp_get_nav_menu_object('gdp-main');
$legal = wp_get_nav_menu_object('gdp-legal');
if (!$main || !$legal) {
    throw new RuntimeException('Required menus missing');
}
set_theme_mod('nav_menu_locations', [
    'menu_1' => (int) $main->term_id,
    'menu_mobile' => (int) $main->term_id,
    'footer' => (int) $legal->term_id,
]);
blocksy_manager()->db->wipe_cache();
// Export from the ACTIVE child; optionally keep a parent copy for parent-only testing.
file_put_contents('/tmp/exported-mods.json', wp_json_encode(get_theme_mods(), JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE));
```

Blocksy's registered menu locations are **`menu_1`, `menu_2`, `menu_mobile`, `footer`**; the main menu item defaults to `menu_1`, mobile-menu to `menu_mobile`; an item `values.menu` of `"blocksy_location"` uses this mapping, otherwise it accepts a menu term/slug via `wp_get_nav_menu_object()`. [Menu registration, lines 422–440](vendor/blocksy/inc/init.php), [desktop menu, lines 3–87](vendor/blocksy/inc/panel-builder/header/menu/view.php), [mobile menu](vendor/blocksy/inc/panel-builder/header/mobile-menu/view.php)

The source reads text and URL specifically from **`header_button_text`** and **`header_button_link`**, not `button_text`/`button_url`; ordinary links are free, while popup behavior is gated by `base_pro`. [CTA view, lines 30–87](vendor/blocksy/inc/panel-builder/header/button/view.php), [CTA options, lines 44–131](vendor/blocksy/inc/panel-builder/header/button/options.php)

Set blogname as the WordPress site option; the logo item renders the title by default as a `span`, not an extra H1, and can use an empty custom-logo value. This is Blocksy's site-title component, **not literally a `core/site-title` block**, so record the minor hybrid-theme interpretation of the spec. [Logo rendering, lines 373–455](vendor/blocksy/inc/panel-builder/header/logo/view.php)

### Different desktop/mobile labels without duplicating paid components

`header_button_text` is a scalar setting shared across desktop/mobile placements; it is not declared responsive. [CTA options, lines 44–51](vendor/blocksy/inc/panel-builder/header/button/options.php)

Safe child extension proposal: add a Customizer theme_mod setting/control `gdp_mobile_cta_label` (default empty, `sanitize_text_field`, capability `edit_theme_options`), export `"gdp_mobile_cta_label":"Oferta w 24 h"` in JSON, and use the following hook; no visible text is hard-coded in PHP and the same free Button stays in both layouts. The hook receives `device`, `item_id` and `atts`. [Header renderer, lines 468–485](vendor/blocksy/inc/components/builder/builder-header-renderer.php)

```php
add_filter('blocksy:header:item-template-args', function ($args) {
    if ($args['item_id'] === 'button' && $args['device'] === 'mobile') {
        $label = get_theme_mod('gdp_mobile_cta_label', '');
        if ($label !== '') {
            $args['atts']['header_button_text'] = esc_html($label);
            $args['atts']['button_aria_label'] = $label;
        }
    }
    return $args;
});
```

Do not claim a second independent native free button UI was verified: renderer supports `button~uniqueid` clones, but this investigation has not established end-to-end Customizer support without Pro. The single-button filter above avoids that dependency. [Clone parsing, lines 55–57 and 146–162](vendor/blocksy/inc/components/builder/builder-renderer.php)

## 3. Footer: exact 4-column configuration and core block widgets

Canonical footer section (this is complete):

```json
{
  "id": "type-1",
  "mode": "columns",
  "rows": [
    {"id":"top-row","columns":[["widget-area-1"],["widget-area-2"],["widget-area-3"],["widget-area-4"]]},
    {"id":"middle-row","columns":[["widget-area-5"]]},
    {"id":"bottom-row","columns":[["widget-area-6","copyright"]]}
  ],
  "items": [
    {"id":"top-row","values":{"items_per_row":"4","4_columns_layout":{"desktop":"repeat(4, 1fr)","tablet":"repeat(2, 1fr)","mobile":"initial"}}},
    {"id":"middle-row","values":{"items_per_row":"1"}},
    {"id":"bottom-row","values":{"items_per_row":"1"}},
    {"id":"copyright","values":{"copyright_text":"© {current_year} Gaz dla Przemysłu"}}
  ],
  "settings":{}
}
```

The renderer derives column count from `count(row.columns)`; CSS reads `4_columns_layout` using that count, and the UI uses `items_per_row`. **Set both count/array shape and the UI field consistently.** Mobile `initial` means stacked; tablet `repeat(2, 1fr)` is an allowed choice. [Row renderer, lines 69–95](vendor/blocksy/inc/components/builder/builder-footer-renderer.php), [column CSS, lines 375–430](vendor/blocksy/inc/panel-builder/footer/middle-row/dynamic-styles.php), [column options, lines 27–42 and 175–232](vendor/blocksy/inc/panel-builder/footer/middle-row/options.php)

`widget-area-N` renders the sidebar **`ct-footer-sidebar-N`** (N=1…6); all six are registered in the free theme, and removal of `widgets-block-editor` support is only commented out. [Sidebar registration, lines 522–535](vendor/blocksy/inc/init.php), [block editor support, line 411](vendor/blocksy/inc/init.php), [widget view](vendor/blocksy/inc/panel-builder/footer/widget-area-1/view.php)

One-time widget option setup uses normal WP core block widgets—not plugins, Custom HTML widgets or shortcodes:

```php
// $footer_columns[1..6] are validated core block markup, supplied as data files.
$widget_blocks = get_option('widget_block', []);
$sidebars = wp_get_sidebars_widgets();
$next = 1;
foreach (array_keys($widget_blocks) as $key) {
    if (is_numeric($key)) $next = max($next, (int) $key + 1);
}
for ($area = 1; $area <= 6; $area++) {
    $id = $next++;
    $widget_blocks[$id] = ['content' => $footer_columns[$area]];
    $sidebars['ct-footer-sidebar-' . $area] = ['block-' . $id];
}
$widget_blocks['_multiwidget'] = 1;
update_option('widget_block', $widget_blocks);
wp_set_sidebars_widgets($sidebars);
```

Keep the widget payload and sidebars mapping reproducible in repository configuration **in addition to** theme_mods; WXR/theme_mods alone do not represent these widget options. Suggested payloads: columns 1–4 heading+core/list of links; 5 registered-entity placeholder paragraphs; 6 core/list legal links followed by `<!-- wp:block {"ref":RESOLVED_WP_BLOCK_ID} /-->` referencing the synchronized price disclaimer. Resolve that `wp_block` ID after WXR import. This preserves propagation and editing rather than copying disclaimer text into PHP.

Blocksy replaces `{current_year}` itself inside `copyright_text`; this is not a shortcode. [Copyright view, lines 18–39](vendor/blocksy/inc/panel-builder/footer/copyright/view.php)

## 4. Sticky/shrink: exact free boundary

Theme-only `inc/panel-builder/header/options.php:3–4` is an **empty options array passed through `blocksy:header:settings`**; theme renderer normally just concatenates rows unless `blocksy:header:rows-render` overrides them. Companion supplies the setting and hooks. [Empty theme settings](vendor/blocksy/inc/panel-builder/header/options.php), [theme renderer, lines 233–244](vendor/blocksy/inc/components/builder/builder-header-renderer.php), [Companion registration, lines 233–241](vendor/blocksy-companion/framework/features/header.php)

**If a future approved Companion exception is used**, section settings are:

```json
{"has_sticky_header":"yes","sticky_rows":"middle","sticky_effect":"shrink","sticky_behaviour":{"desktop":true,"mobile":true}}
```

Then the `middle-row` item's values are:

```json
{"headerRowHeight":{"desktop":88,"tablet":72,"mobile":72},"has_sticky_shrink":"yes","stickyHeaderRowShrink":{"desktop":75,"tablet":85,"mobile":85}}
```

`stickyHeaderRowShrink` is **percentage of normal row height**, not px; native effect name `shrink` alone does not set the row-height reduction. [Companion options, lines 14–139](vendor/blocksy-companion/framework/features/header/header-options.php), [theme shrink controls, lines 68–97](vendor/blocksy/inc/panel-builder/header/middle-row/options.php), [height calculation, lines 64–78](vendor/blocksy/inc/components/builder/builder-header-renderer.php)

Under the parent's hard no-plugin decision: **do not imply this JSON activates native sticky by itself**. Implement a small child-theme JS/CSS sticky/shrink behavior, keeping all CSS in `style.css`, or mark native sticky pending. Any request to use the Companion exception still needs the **actual P1.1 screenshot required by the specification**; source evidence here is not that screenshot.

## 5. No Google Fonts and palette boundary

Child `functions.php`, early:

```php
add_filter('blocksy:typography:google:use-remote', '__return_false');
```

The minimal file selects `rootTypography.family = "System Default"` and all other typography can inherit; for self-hosted fonts register local WOFF2 with `@font-face` in child `style.css` / local `theme.json` `fontFace`, and set local families or override Blocksy font CSS variables consistently for front/editor. The filter is the hard remote-loader kill switch; no guessed `disable_google_fonts` theme_mod is needed. [System font selection and exclusion, lines 59–97](vendor/blocksy/inc/css/fonts-manager.php), [remote gate, lines 115–151](vendor/blocksy/inc/css/fonts-manager.php)

Blocksy's top-level palette shape is `"colorPalette":{"color1":{"color":"#..."},"color2":{"color":"#..."},...,"color8":{"color":"#..."}}`; it generates `--theme-palette-color-N` and editor slugs `palette-color-N`, not the requested `base/contrast/primary/...` slugs. The theme offers `blocksy:editor-color-palette` to replace its editor palette while retaining Blocksy variables in the header/footer. [Color reader, lines 486–560](vendor/blocksy/inc/classes/colors.php), [editor palette hook, lines 40–59](vendor/blocksy/inc/init.php)

Recommendation: keep one token source in the repo generator; generate semantic `theme.json` palette plus Blocksy's numeric colorPalette from the same values, and filter Blocksy's editor palette to the semantic palette to prevent duplicate competing palettes. Do not claim runtime `theme.json` merge precedence has been verified in this source-only task.

## 6. Importer evidence and verification limits

`vendor/blueprints-source/{compile-v1.ts,import-wxr.ts}` are extracted verbatim from the installed package's `index.js.map`; the compiler inserts the importer plugin unconditionally, and handler constructs `new WP_Import()` and no longer branches on `importer`. [Compiler, lines 344–359](vendor/blueprints-source/compile-v1.ts), [handler](vendor/blueprints-source/import-wxr.ts)

These are static source findings, not screenshots or a live Playground smoke test. The minimal JSON is a structural seed, not a completed design or complete stage-1 content: menu IDs, six block widgets, child CSS/fonts, mobile-label control and custom sticky behavior must be applied/tested separately. No user infrastructure was accessed and no plugin was installed.
