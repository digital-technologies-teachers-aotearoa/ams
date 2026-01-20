/**
 * Translation Widget JavaScript
 * Handles form submission for translation widgets
 */

(function () {
  'use strict';

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTranslationWidgets);
  } else {
    initTranslationWidgets();
  }

  function initTranslationWidgets() {
    // Find all translation widgets
    const widgets = document.querySelectorAll('.translation-widget');
    if (widgets.length === 0) return;

    // Find the form containing the widgets
    const form = document.querySelector('form');
    if (!form) return;

    // Add submit handler
    form.addEventListener('submit', function (e) {
      widgets.forEach(function (widget) {
        serializeTranslationWidget(widget);
      });
    });
  }

  function serializeTranslationWidget(widget) {
    const hiddenInput = widget.querySelector('.translation-hidden-input');
    const inputs = widget.querySelectorAll('.translation-input');
    const result = {};

    inputs.forEach(function (input) {
      const lang = input.dataset.lang;
      const value = input.value.trim();
      if (value) {
        result[lang] = value;
      }
    });

    hiddenInput.value = JSON.stringify(result);
  }
})();
