<?php
// wp eval-file scripts/export-theme-mods.php > config/theme_mods_export.json
if (!defined('ABSPATH')) { throw new RuntimeException('Run through WP-CLI'); }
echo wp_json_encode([
    'active_stylesheet' => get_stylesheet(),
    'theme_mods' => get_theme_mods(),
    'widgets' => get_option('widget_block'),
    'sidebars' => wp_get_sidebars_widgets(),
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
