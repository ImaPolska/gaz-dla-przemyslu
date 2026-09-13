<?php
require_once '/wordpress/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
$report = [
    'counts' => ['core/html' => 0, 'core/freeform' => 0, 'core/shortcode' => 0, 'shortcode' => 0, 'non_core' => 0],
    'pages' => [], 'issues' => [], 'objects' => [], 'documented_exceptions' => [],
    'wp' => get_bloginfo('version'), 'php' => PHP_VERSION,
    'stylesheet' => get_stylesheet(), 'parent' => get_template(),
    'parent_version' => wp_get_theme('blocksy')->get('Version'),
    'debug' => ['enabled' => WP_DEBUG, 'log' => WP_DEBUG_LOG, 'display' => WP_DEBUG_DISPLAY],
    'plugins' => array_keys(get_plugins()),
    'mu_runtime' => array_keys(get_mu_plugins()),
];
$walk = function ($blocks, $location) use (&$walk, &$report) {
    foreach ($blocks as $block) {
        $name = $block['blockName'] ?? null;
        if ($name === null && trim($block['innerHTML'] ?? '') === '') { continue; }
        if (!$name) { $report['counts']['core/freeform']++; }
        elseif (isset($report['counts'][$name])) { $report['counts'][$name]++; }
        elseif (!str_starts_with($name, 'core/')) { $report['counts']['non_core']++; }
        $walk($block['innerBlocks'] ?? [], $location);
    }
};
$expand = function ($blocks, $seen = []) use (&$expand) {
    $html = '';
    foreach ($blocks as $block) {
        if ($block['blockName'] === 'core/block' && isset($block['attrs']['ref'])) {
            $id = $block['attrs']['ref'];
            if (in_array($id, $seen, true)) { throw new RuntimeException('Pattern recursion'); }
            $post = get_post($id);
            if (!$post) { throw new RuntimeException('Pattern missing'); }
            $html .= $expand(parse_blocks($post->post_content), [...$seen, $id]);
        } else {
            $html .= $block['innerHTML'] ?? '';
            $html .= $expand($block['innerBlocks'] ?? [], $seen);
        }
    }
    return $html;
};
foreach (get_posts(['post_type' => ['page','post','wp_block'], 'numberposts' => -1, 'post_status' => 'any']) as $post) {
    $blocks = parse_blocks($post->post_content);
    $walk($blocks, $post->post_name);
    $clean = preg_replace('/\[\[.*?\]\]/s', '', $post->post_content);
    preg_match_all('/(?<!\[)\[\/?[a-z_][a-z0-9_-]*(?:\s[^\]]*)?\/?\](?!\])/i', $clean, $shortcodes);
    $report['counts']['shortcode'] += count($shortcodes[0]);
    $report['objects'][] = ['id'=>$post->ID,'source_id'=>get_post_meta($post->ID,'_gdp_import_id',true),'type'=>$post->post_type,'slug'=>$post->post_name];
    if (in_array($post->post_type, ['page','post'], true)) {
        $h1 = preg_match_all('/<h1(?:\s|>)/i', $expand($blocks));
        if ($post->post_name === 'archiwum-kategorii' && str_contains($post->post_content, 'wp:query-title')) { $h1++; }
        $locks = true;
        foreach ($blocks as $block) {
            if (!$block['blockName'] && trim($block['innerHTML'] ?? '') === '') { continue; }
            if ($post->post_type === 'post' && ($block['attrs']['metadata']['name'] ?? '') === 'Treść artykułu' && ($block['attrs']['templateLock'] ?? null) === false) {
                $report['documented_exceptions'][] = $post->post_name . ': editable article prose required by section 14';
                continue;
            }
            if ($block['blockName'] !== 'core/group' || ($block['attrs']['templateLock'] ?? '') !== 'contentOnly' || empty($block['attrs']['metadata']['name'])) {
                $locks = false;
            }
        }
        $report['pages'][] = ['slug' => $post->post_name, 'id' => $post->ID, 'h1' => $h1, 'sections_locked_named' => $locks];
        if ($h1 !== 1 || !$locks) { $report['issues'][] = $post->post_name; }
    }
}
$theme = json_decode(file_get_contents(get_stylesheet_directory() . '/theme.json'), true);
$mods = get_theme_mod('colorPalette');
$mapping = ['primary','secondary','contrast','contrast','line','surface','base','base'];
$colors = array_column($theme['settings']['color']['palette'], 'color', 'slug');
$report['palette_matches'] = true;
foreach ($mapping as $i => $key) {
    if (($mods['color' . ($i + 1)]['color'] ?? '') !== $colors[$key]) { $report['palette_matches'] = false; }
}
$report['pass'] = !array_sum($report['counts']) && !$report['issues'] && !$report['plugins'] && $report['palette_matches'];
echo wp_json_encode($report, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
