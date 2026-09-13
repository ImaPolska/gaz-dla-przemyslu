<?php
/** Posts page remains /wiedza/; its editable core blocks supply the hub. */
defined('ABSPATH') || exit;
get_header();
$hub = get_post((int) get_option('page_for_posts'));
if ($hub) {
    echo '<div class="gdp-template entry-content">';
    echo apply_filters('the_content', $hub->post_content);
    echo '</div>';
}
get_footer();
