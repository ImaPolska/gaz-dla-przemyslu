<?php
/**
 * Gaz dla Przemysłu. Presentation and editor guardrails only.
 * No business copy, endpoints, shortcodes, or plugins.
 */
defined('ABSPATH') || exit;

add_action('after_setup_theme', function () {
    add_theme_support('editor-styles');
    add_theme_support('wp-block-styles');
    add_theme_support('align-wide');
    add_editor_style('style.css');
});

add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('gdp-child', get_stylesheet_uri(), [], wp_get_theme()->get('Version'));
    wp_enqueue_script('gdp-header', get_stylesheet_directory_uri() . '/assets/header.js', [], wp_get_theme()->get('Version'), true);
}, 50);

add_action('init', function () {
    register_block_pattern_category('gdp', ['label' => 'Gaz dla Przemysłu']);
    add_rewrite_rule('^wiedza/([^/]+)/?$', 'index.php?name=$matches[1]', 'top');
    add_rewrite_rule('^komentarz-rynkowy/page/([0-9]+)/?$', 'index.php?category_name=komentarz-rynkowy&paged=$matches[1]', 'top');
    add_rewrite_rule('^komentarz-rynkowy/?$', 'index.php?category_name=komentarz-rynkowy', 'top');
});

add_filter('post_link', function ($link, $post) {
    return $post->post_type === 'post' ? home_url('/wiedza/' . $post->post_name . '/') : $link;
}, 10, 2);
add_filter('term_link', function ($link, $term, $taxonomy) {
    return $taxonomy === 'category' && $term->slug === 'komentarz-rynkowy' ? home_url('/komentarz-rynkowy/') : $link;
}, 10, 3);
add_filter('blocksy:404:custom-output', function ($output) {
    $page = get_page_by_path('blad-404');
    return $page ? '<div class="gdp-template entry-content">' . apply_filters('the_content', $page->post_content) . '</div>' : $output;
});

// Source-owned query selectors use a category slug, never an environment-specific ID.
add_filter('query_loop_block_query_vars', function ($query, $block) {
    $slug = $block->context['query']['gdpCategory'] ?? '';
    if ($slug) { $query['category_name'] = sanitize_title($slug); }
    return $query;
}, 10, 2);

// Patterns containing a synced ref resolve source IDs after every clean import.
add_action('init', function () {
    $registry = WP_Block_Patterns_Registry::get_instance();
    $map = get_option('gdp_import_map', []);
    foreach ($registry->get_all_registered() as $pattern) {
        if (!str_starts_with($pattern['name'], 'gdp/')) { continue; }
        $pattern['content'] = preg_replace_callback('/"ref":(\d+)/', fn($m) => '"ref":' . ($map[(int) $m[1]] ?? $m[1]), $pattern['content']);
        unregister_block_pattern($pattern['name']);
        register_block_pattern($pattern['name'], $pattern);
    }
}, 100);

// Blocksy free has a supported filter; no Companion or remote font loader needed.
add_filter('blocksy:typography:google:use-remote', '__return_false');
add_filter('blocksy:editor-color-palette', function () {
    $json = json_decode(file_get_contents(get_stylesheet_directory() . '/theme.json'), true);
    return $json['settings']['color']['palette'];
});
add_action('customize_register', function ($customizer) {
    $customizer->add_setting('gdp_mobile_cta_label', ['default' => '', 'sanitize_callback' => 'sanitize_text_field', 'capability' => 'edit_theme_options']);
    $customizer->add_control('gdp_mobile_cta_label', ['label' => 'Tekst przycisku mobilnego GDP', 'section' => 'title_tagline', 'type' => 'text']);
});
add_filter('blocksy:header:item-template-args', function ($args) {
    if (($args['item_id'] ?? '') === 'button' && ($args['device'] ?? '') === 'mobile') {
        $label = get_theme_mod('gdp_mobile_cta_label', '');
        if ($label !== '') {
            $args['atts']['header_button_text'] = esc_html($label);
            $args['atts']['button_aria_label'] = $label;
        }
    }
    return $args;
});
add_filter('show_admin_bar', '__return_false');
add_filter('get_avatar_url', function ($url) { return ''; });
add_filter('option_show_avatars', '__return_false');

add_filter('allowed_block_types_all', function ($allowed) {
    $names = array_keys(WP_Block_Type_Registry::get_instance()->get_all_registered());
    return array_values(array_filter($names, function ($name) {
        return str_starts_with($name, 'core/') &&
            !in_array($name, ['core/html', 'core/freeform', 'core/shortcode'], true);
    }));
});

add_filter('block_editor_settings_all', function ($settings, $context) {
    $admin = current_user_can('manage_options');
    $settings['canLockBlocks'] = $admin;
    $settings['codeEditingEnabled'] = $admin;
    // Top-level movement is forbidden to Editor; inner contentOnly remains editable.
    if (!$admin && isset($context->post) && in_array($context->post->post_type, ['page','post'], true)) {
        $settings['templateLock'] = 'all';
    }
    return $settings;
}, 10, 2);

// Enforce the same layout policy over the existing core REST save route.
// Do not mistake UI locks for authorization.
function gdp_guard_layout($prepared, $request) {
    if (current_user_can('manage_options') || empty($request['id']) || !isset($prepared->post_content)) {
        return $prepared;
    }
    $signature = function ($content) {
        $walk = function ($blocks) use (&$walk) {
            $out = [];
            foreach ($blocks as $block) {
                if (empty($block['blockName'])) {
                    if (trim($block['innerHTML'] ?? '') !== '') { $out[] = ['freeform']; }
                    continue;
                }
                $attrs = $block['attrs'];
                $out[] = [
                    $block['blockName'],
                    $attrs['metadata']['name'] ?? '',
                    $attrs['className'] ?? '',
                    $attrs['templateLock'] ?? null,
                    $attrs['lock'] ?? null,
                    $attrs['ref'] ?? null,
                    // Only the prose group in articles is intentionally extensible.
                    ($block['blockName'] === 'core/group' && ($attrs['metadata']['name'] ?? '') === 'Treść artykułu' && ($attrs['templateLock'] ?? null) === false)
                        ? ['editable-article-body'] : $walk($block['innerBlocks']),
                ];
            }
            return $out;
        };
        return $walk(parse_blocks($content));
    };
    $old = get_post((int) $request['id']);
    if ($old && $signature($old->post_content) !== $signature($prepared->post_content)) {
        return new WP_Error('gdp_layout_locked', 'Układ strony jest zablokowany dla tej roli.', ['status' => 403]);
    }
    return $prepared;
}
add_filter('rest_pre_insert_page', 'gdp_guard_layout', 10, 2);
add_filter('rest_pre_insert_post', 'gdp_guard_layout', 10, 2);
