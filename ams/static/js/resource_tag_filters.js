document.addEventListener('DOMContentLoaded', function () {
  const toggles = document.querySelectorAll('[data-category-toggle]');
  if (!toggles.length) return;

  function checkboxesFor(categoryId) {
    return document.querySelectorAll(
      '[data-tag-category="' + categoryId + '"]'
    );
  }

  function syncToggle(toggle) {
    const categoryId = toggle.dataset.categoryToggle;
    const checkboxes = checkboxesFor(categoryId);
    const allChecked =
      checkboxes.length > 0 &&
      Array.prototype.every.call(checkboxes, function (checkbox) {
        return checkbox.checked;
      });
    toggle.setAttribute('aria-pressed', allChecked ? 'true' : 'false');
  }

  toggles.forEach(function (toggle) {
    const categoryId = toggle.dataset.categoryToggle;
    const checkboxes = checkboxesFor(categoryId);

    // Initialise from the server-rendered checked state.
    syncToggle(toggle);

    toggle.addEventListener('click', function () {
      const shouldCheckAll = toggle.getAttribute('aria-pressed') !== 'true';
      checkboxes.forEach(function (checkbox) {
        checkbox.checked = shouldCheckAll;
      });
      syncToggle(toggle);
    });

    checkboxes.forEach(function (checkbox) {
      checkbox.addEventListener('change', function () {
        syncToggle(toggle);
      });
    });
  });
});
