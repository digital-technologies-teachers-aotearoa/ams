/* Project specific Javascript goes here. */

document.addEventListener('DOMContentLoaded', function () {
  document
    .querySelectorAll('[data-bs-toggle="tooltip"]')
    .forEach(function (element) {
      new bootstrap.Tooltip(element);
    });
});
