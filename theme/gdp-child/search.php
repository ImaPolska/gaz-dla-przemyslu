<?php
/** Search copy and core Query Loop remain editable WordPress content. */
defined('ABSPATH') || exit;
get_header();
$template = get_page_by_path('wyniki-wyszukiwania');
if ($template) {
    echo '<div class="gdp-template entry-content">';
    echo apply_filters('the_content', $template->post_content);
    echo '</div>';
}
get_footer();
