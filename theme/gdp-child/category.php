<?php
/** Editable category templates; no business copy in PHP. */
defined('ABSPATH') || exit;
get_header();
$term = get_queried_object();
$template = get_page_by_path($term->slug === 'komentarz-rynkowy' ? 'komentarz-rynkowy' : 'archiwum-kategorii');
if ($template) {
    echo '<div class="gdp-template entry-content">';
    echo apply_filters('the_content', $template->post_content);
    echo '</div>';
} else {
    get_template_part('template-parts/archive');
}
get_footer();
