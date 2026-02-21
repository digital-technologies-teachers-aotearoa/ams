document.addEventListener('DOMContentLoaded', function () {
  const path = window.location.pathname;
  if (path.startsWith('/cms/images/')) {
    insertBanner(
      '⚠️ All images uploaded are public. Private content should be uploaded as documents.'
    );
  }
  if (path.startsWith('/cms/documents/')) {
    insertBanner(
      '🔒 All documents uploaded are private to users with an active membership.'
    );
  }
  if (path.startsWith('/cms/pages/')) {
    hidePagePrivacyControls();
  }
  if (path.startsWith('/cms/settings/cms/themesettings/')) {
    addThemeSettingsImportExport();
    addWcagContrastBadges();
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
    'section[aria-labelledby="status-sidebar-visible-to-all"]'
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
    'nav.actions.actions--primary.footer__container'
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
        'This will overwrite your current settings. Continue?'
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

// ==== WCAG Contrast Badge Helpers ====

function wcagRelativeLuminance(hex) {
  hex = hex.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;
  const toLinear = (c) =>
    c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  return 0.2126 * toLinear(r) + 0.7152 * toLinear(g) + 0.0722 * toLinear(b);
}

function wcagContrastRatio(color1, color2) {
  const l1 = wcagRelativeLuminance(color1);
  const l2 = wcagRelativeLuminance(color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function wcagRating(ratio) {
  if (ratio >= 7.0) return 'AAA';
  if (ratio >= 4.5) return 'AA';
  return 'Fail';
}

function createWcagBadge(ratio, rating) {
  const badge = document.createElement('span');
  badge.className = 'wcag-badge wcag-badge--' + rating.toLowerCase();
  badge.textContent = rating + ' ' + ratio.toFixed(1) + ':1';
  badge.title = 'WCAG contrast ratio against white / dark backgrounds';
  return badge;
}

function updateWcagBadge(input) {
  const color = input.value;
  if (!color || color.length < 7) return;

  // Remove existing badges for this input
  const container = input.closest('.w-field__wrapper') || input.parentElement;
  container.querySelectorAll('.wcag-badge-group').forEach((el) => el.remove());

  const ratioWhite = wcagContrastRatio(color, '#ffffff');
  const ratingWhite = wcagRating(ratioWhite);
  const ratioDark = wcagContrastRatio(color, '#212529');
  const ratingDark = wcagRating(ratioDark);

  const group = document.createElement('span');
  group.className = 'wcag-badge-group';

  const whiteLabel = document.createElement('span');
  whiteLabel.className = 'wcag-badge-label';
  whiteLabel.textContent = 'on white:';

  const darkLabel = document.createElement('span');
  darkLabel.className = 'wcag-badge-label';
  darkLabel.textContent = 'on dark:';

  group.appendChild(whiteLabel);
  group.appendChild(createWcagBadge(ratioWhite, ratingWhite));
  group.appendChild(darkLabel);
  group.appendChild(createWcagBadge(ratioDark, ratingDark));

  // Insert after the help text or input wrapper
  const helpText = container.querySelector('.w-field__help');
  if (helpText) {
    helpText.after(group);
  } else {
    container.appendChild(group);
  }
}

function addWcagContrastBadges() {
  const colorInputs = document.querySelectorAll('input[type="color"]');
  colorInputs.forEach((input) => {
    // Initial badge
    updateWcagBadge(input);

    // Update on change
    input.addEventListener('input', () => updateWcagBadge(input));
    input.addEventListener('change', () => updateWcagBadge(input));

    // Also watch the associated text input (wagtail-color-panel uses a text input)
    const textInput = input
      .closest('.w-field__wrapper')
      ?.querySelector('input[type="text"]');
    if (textInput) {
      textInput.addEventListener('input', () => {
        // Small delay to let the color input sync
        setTimeout(() => updateWcagBadge(input), 50);
      });
    }
  });
}
