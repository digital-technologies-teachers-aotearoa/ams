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
  if (path.startsWith('/cms/settings/cms/themesettings/')) {
    addThemeSettingsImportExport();
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

function addThemeSettingsImportExport() {
  const footer = document.querySelector(
    'nav.actions.actions--primary.footer__container',
  );
  if (!footer) return;

  // Create export button
  const exportButton = document.createElement('button');
  exportButton.type = 'button';
  exportButton.className = 'button';
  exportButton.innerHTML = `
    <svg class="icon icon-download" aria-hidden="true"><use href="#icon-download"></use></svg>
    <em>Export Settings</em>
  `;
  exportButton.addEventListener('click', exportThemeSettings);

  // Create import button
  const importButton = document.createElement('button');
  importButton.type = 'button';
  importButton.className = 'button';
  importButton.innerHTML = `
    <svg class="icon icon-upload" aria-hidden="true"><use href="#icon-upload"></use></svg>
    <em>Import Settings</em>
  `;
  importButton.addEventListener('click', () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'application/json';
    fileInput.addEventListener('change', importThemeSettings);
    fileInput.click();
  });

  // Insert buttons after the Save button
  const saveButton = footer.querySelector('button[type="submit"]');
  if (saveButton) {
    saveButton.after(exportButton);
    exportButton.after(importButton);
  }
}

function exportThemeSettings() {
  const settings = {};
  const form = document.getElementById('w-editor-form');
  if (!form) {
    alert('Form not found.');
    return;
  }

  // Collect all text inputs and textareas with IDs within the form
  const inputs = form.querySelectorAll('input[type="text"][id], textarea[id]');

  inputs.forEach((input) => {
    if (input.id) {
      settings[input.id] = input.value;
    }
  });

  // Create and download JSON file
  const blob = new Blob([JSON.stringify(settings, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `theme-settings-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function importThemeSettings(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (e) {
    try {
      const settings = JSON.parse(e.target.result);

      if (typeof settings !== 'object' || settings === null) {
        throw new Error('Invalid settings file format');
      }

      const confirmed = confirm(
        'This will overwrite your current settings. Continue?',
      );

      if (!confirmed) return;

      const form = document.getElementById('w-editor-form');
      if (!form) {
        alert('Form not found.');
        return;
      }

      // Apply settings to matching inputs within the form
      let appliedCount = 0;
      for (const [id, value] of Object.entries(settings)) {
        const input = document.getElementById(id);
        if (
          input &&
          form.contains(input) &&
          ((input.tagName === 'INPUT' && input.type === 'text') ||
            input.tagName === 'TEXTAREA')
        ) {
          input.value = value;
          // Trigger change and input events
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
          appliedCount++;
        }
      }

      alert(`Successfully imported ${appliedCount} setting(s).`);
    } catch (error) {
      alert(`Error importing settings: ${error.message}`);
    }
  };

  reader.onerror = function () {
    alert('Error reading file. Please try again.');
  };

  reader.readAsText(file);
}
