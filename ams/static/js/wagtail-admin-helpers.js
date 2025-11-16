document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname;
  if (path.startsWith('/cms/images/')) {
    insertBanner(
      '⚠️ All images uploaded are public. Private content should be uploaded as documents.',
    );
  }
  if (path.startsWith('/cms/documents/')) {
    insertBanner(
      '🔒 All documents uploaded are private to users with an active membership.',
    );
  }
  if (path.startsWith('/cms/pages/')) {
    hidePagePrivacyControls();
  }
});

function insertBanner(message) {
  const banner = document.createElement('div');
  banner.className = 'ams-help-banner';
  banner.innerText = message;
  const header = document.querySelector('header');
  if (header) {
    header.append(banner);
  }
}

function hidePagePrivacyControls() {
  // Find the (public) visibility section.
  const publicSection = document.querySelector(
    'section[aria-labelledby="status-sidebar-visible-to-all"]',
  );
  if (!publicSection) return;

  // Create the message element.
  const notice = document.createElement('div');
  notice.textContent =
    "ℹ️ The privacy value should be set to 'Visible to all', as additional AMS permission checks are performed after this. Only change if you understand the implications.";
  notice.className = 'ams-privacy-banner';

  // Insert the notice as a sibling directly before the section.
  const parent = publicSection.parentNode;
  if (parent) {
    parent.insertBefore(notice, publicSection);
  }
}
