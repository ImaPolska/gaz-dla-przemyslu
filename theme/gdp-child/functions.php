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
});

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
    if (!$admin && isset($context->post) && $context->post->post_type === 'page') {
        $settings['templateLock'] = 'all';
    }
    return $settings;
}, 10, 2);

// Enforce the same layout policy over the existing core REST save route.
// Do not mistake UI locks for authorization.
add_filter('rest_pre_insert_page', function ($prepared, $request) {
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
                    $walk($block['innerBlocks']),
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
}, 10, 2);
