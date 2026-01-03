document.addEventListener('DOMContentLoaded', function () {
  var actionModal = document.getElementById('actionModal');
  if (!actionModal) return;

  actionModal.addEventListener('show.bs.modal', function (event) {
    var button = event.relatedTarget;
    if (!button) return;

    var actionUrl = button.getAttribute('data-action-url') || '';
    var title = button.getAttribute('data-action-title') || '';
    var message = button.getAttribute('data-action-message') || '';
    var confirmText = button.getAttribute('data-action-confirm') || '';
    var confirmStyle = button.getAttribute('data-action-style') || '';

    var form = actionModal.querySelector('form.action-modal-form');
    var modalTitle = actionModal.querySelector('.modal-title');
    var modalMessage = actionModal.querySelector('.modal-message');
    var modalConfirm = actionModal.querySelector('.modal-confirm');

    if (form) form.action = actionUrl;
    if (modalTitle) modalTitle.textContent = title;
    if (modalMessage) modalMessage.textContent = message;
    if (modalConfirm) modalConfirm.textContent = confirmText;

    // Reset styles, then apply optional style
    if (modalConfirm) {
      modalConfirm.className = 'btn modal-confirm';
      if (confirmStyle) modalConfirm.classList.add(confirmStyle);
      else modalConfirm.classList.add('btn-primary');
    }
  });
});
