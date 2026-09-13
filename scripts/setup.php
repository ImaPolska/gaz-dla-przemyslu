<?php
require_once '/wordpress/wp-load.php';
if (!defined('GDP_PROTOTYPE') || get_stylesheet() !== 'gdp-child' || get_template() !== 'blocksy') {
    throw new RuntimeException('Unexpected setup target');
}
$mods = json_decode(file_get_contents('/tmp/theme_mods.json'), true, 512, JSON_THROW_ON_ERROR);
foreach ($mods as $key => $value) { set_theme_mod($key, $value); }
// Parent mirror required by specification, child option is the live source.
update_option('theme_mods_blocksy', $mods);

$menus = json_decode(file_get_contents('/tmp/menus.json'), true, 512, JSON_THROW_ON_ERROR);
$locations = [];
foreach ($menus as $menu) {
    $id = wp_create_nav_menu($menu['slug']);
    if (is_wp_error($id)) { throw new RuntimeException($id->get_error_message()); }
    $add_item = function ($item, $parent = 0) use (&$add_item, $id) {
        $item_id = wp_update_nav_menu_item($id, 0, [
            'menu-item-title' => $item['title'],
            'menu-item-url' => home_url($item['url']),
            'menu-item-type' => 'custom',
            'menu-item-status' => 'publish',
            'menu-item-parent-id' => $parent,
        ]);
        if (is_wp_error($item_id)) { throw new RuntimeException($item_id->get_error_message()); }
        foreach ($item['children'] ?? [] as $child) { $add_item($child, $item_id); }
    };
    foreach ($menu['items'] as $item) { $add_item($item); }
    foreach ($menu['locations'] as $location) { $locations[$location] = $id; }
}
set_theme_mod('nav_menu_locations', $locations);
$front = get_page_by_path('start');
$blog = get_page_by_path('wiedza');
if (!$front || !$blog) { throw new RuntimeException('Static front or posts page missing'); }
update_option('show_on_front', 'page');
update_option('page_on_front', $front->ID);
update_option('page_for_posts', $blog->ID);
update_option('blogname', 'Gaz dla Przemysłu');
update_option('blogdescription', 'PBM Sp. z o.o., Grupa IMA Polska');
update_option('timezone_string', 'Europe/Warsaw');
update_option('show_avatars', 0);
update_option('permalink_structure', '/%postname%/');
update_option('blog_public', 0);
foreach (get_posts(['post_type' => ['page','post'], 'numberposts' => -1]) as $post) {
    update_post_meta($post->ID, 'blocksy_meta', ['hero_enabled' => 'no', 'page_structure_type' => 'type-4', 'content_style' => 'wide', 'vertical_spacing' => 'top:bottom']);
}
$widgets_data = json_decode(file_get_contents('/tmp/widgets.json'), true, 512, JSON_THROW_ON_ERROR);
$map = get_option('gdp_import_map');
$widgets = ['_multiwidget' => 1];
$sidebars = ['wp_inactive_widgets' => [], 'array_version' => 3];
foreach ($widgets_data as $index => $markup) {
    $number = $index + 1;
    $markup = preg_replace_callback('/"ref":(\d+)/', fn($m) => '"ref":' . $map[(int) $m[1]], $markup);
    $widgets[$number] = ['content' => $markup];
    $sidebars['ct-footer-sidebar-' . $number] = ['block-' . $number];
}
update_option('widget_block', $widgets);
wp_set_sidebars_widgets($sidebars);
blocksy_manager()->db->wipe_cache();
delete_transient('blocksy_dynamic_styles_descriptor');
do_action('blocksy:dynamic-css:refresh-caches');
flush_rewrite_rules(false);
// Remove default application plugins shipped with WordPress, not runtime drop-ins.
require_once ABSPATH . 'wp-admin/includes/plugin.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
foreach (array_keys(get_plugins()) as $plugin) {
    if (is_plugin_active($plugin)) { deactivate_plugins($plugin); }
    $deleted = delete_plugins([$plugin]);
    if (is_wp_error($deleted)) { throw new RuntimeException($deleted->get_error_message()); }
}
echo wp_json_encode(['stylesheet' => get_stylesheet(), 'template' => get_template(), 'plugins' => array_keys(get_plugins()), 'front' => get_permalink($front)]);
