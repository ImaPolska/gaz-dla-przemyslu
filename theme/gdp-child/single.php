<?php
/** The complete article, including title and author, lives in post_content. */
defined('ABSPATH') || exit;
get_header();
while (have_posts()) {
    the_post();
    echo '<article class="gdp-template entry-content">';
    the_content();
    echo '</article>';
}
get_footer();
