/* Lock the outer layout after the first save; new drafts can receive GDP starters. */
wp.domReady(function () {
  wp.data.subscribe(function () {
    const editor = wp.data.select('core/editor');
    const blocks = wp.data.select('core/block-editor');
    if (!editor || !blocks) return;
    const settings = blocks.getSettings();
    const status = editor.getCurrentPostAttribute('status');
    const type = editor.getCurrentPostType();
    if (settings.canLockBlocks === false && ['page', 'post'].includes(type) &&
        status && status !== 'auto-draft' && settings.templateLock !== 'all') {
      wp.data.dispatch('core/block-editor').updateSettings({ templateLock: 'all' });
    }
  });
});
