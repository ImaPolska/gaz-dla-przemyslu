<?php
/**
 * Narrow importer for THIS repository's controlled WXR 1.2.
 * A setup script executed once, not a plugin. No arbitrary third-party WXR support.
 * Media import is deliberately refused in P1.1 rather than silently omitted.
 */
require_once '/wordpress/wp-load.php';
if (!defined('GDP_PROTOTYPE') || GDP_PROTOTYPE !== true) {
    throw new RuntimeException('Disposable GDP Playground required');
}
if (get_option('gdp_import_done')) { throw new RuntimeException('Fresh Playground required'); }
$xml = simplexml_load_file('/tmp/site.wxr', 'SimpleXMLElement', LIBXML_NONET | LIBXML_NOCDATA);
if (!$xml) { throw new RuntimeException('WXR parse failed'); }
$wp_ns = 'http://wordpress.org/export/1.2/';
$content_ns = 'http://purl.org/rss/1.0/modules/content/';
$map = [];
$pending = [];
foreach (get_posts(['post_type' => ['post', 'page'], 'numberposts' => -1, 'post_status' => 'any']) as $post) {
    wp_delete_post($post->ID, true);
}
foreach ($xml->channel->item as $item) {
    $wp = $item->children($wp_ns);
    $type = (string) $wp->post_type;
    if (!in_array($type, ['page', 'post', 'wp_block'], true)) {
        throw new RuntimeException('Unsupported WXR type: ' . $type);
    }
    $content = (string) $item->children($content_ns)->encoded;
    $id = wp_insert_post(wp_slash([
        'post_title' => (string) $item->title,
        'post_name' => (string) $wp->post_name,
        'post_content' => $content,
        'post_excerpt' => '',
        'post_type' => $type,
        'post_status' => 'publish',
        'post_author' => 1,
        'comment_status' => 'closed',
        'ping_status' => 'closed',
    ]), true);
    if (is_wp_error($id)) { throw new RuntimeException($id->get_error_message()); }
    $map[(int) $wp->post_id] = $id;
    $pending[$id] = ['parent' => (int) $wp->post_parent, 'content' => $content];
    foreach ($wp->postmeta as $meta) {
        $key = (string) $meta->meta_key;
        // Generated WXR is project-owned; metadata remains WordPress data.
        update_post_meta($id, $key, maybe_unserialize((string) $meta->meta_value));
    }
    if ($type === 'post') {
        foreach ($item->category as $category) {
            if ((string) $category['domain'] !== 'category') { continue; }
            $slug = (string) $category['nicename'];
            $term = get_term_by('slug', $slug, 'category');
            if (!$term) {
                $new = wp_insert_term((string) $category, 'category', ['slug' => $slug]);
                if (is_wp_error($new)) { throw new RuntimeException($new->get_error_message()); }
                $term_id = $new['term_id'];
            } else { $term_id = $term->term_id; }
            wp_set_post_categories($id, [(int) $term_id], true);
        }
    }
}
foreach ($pending as $id => $data) {
    $content = preg_replace_callback('/<!-- wp:block (\{.*?\}) \/-->/s', function ($match) use ($map) {
        $attrs = json_decode($match[1], true, 512, JSON_THROW_ON_ERROR);
        if (isset($attrs['ref'])) {
            if (!isset($map[$attrs['ref']])) { throw new RuntimeException('Unresolved synced pattern reference'); }
            $attrs['ref'] = $map[$attrs['ref']];
        }
        return '<!-- wp:block ' . wp_json_encode($attrs, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . ' /-->';
    }, $data['content']);
    $result = wp_update_post(wp_slash(['ID' => $id, 'post_content' => $content, 'post_parent' => $map[$data['parent']] ?? 0]), true);
    if (is_wp_error($result)) { throw new RuntimeException($result->get_error_message()); }
}
update_option('gdp_import_map', $map);
update_option('gdp_import_done', true);
echo wp_json_encode(['imported' => count($map), 'id_map' => $map]);
