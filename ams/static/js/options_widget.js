/**
 * Options Widget JavaScript
 * Handles dynamic table rows for options widgets
 */

(function () {
  'use strict';

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOptionsWidgets);
  } else {
    initOptionsWidgets();
  }

  let rowCounter = 0;

  function initOptionsWidgets() {
    const widgets = document.querySelectorAll('.options-widget');
    if (widgets.length === 0) return;

    widgets.forEach(function (widget) {
      initWidget(widget);
    });

    // Find the form and add submit handler
    const form = document.querySelector('form');
    if (form) {
      form.addEventListener('submit', function (e) {
        widgets.forEach(function (widget) {
          serializeOptionsWidget(widget);
        });
      });
    }
  }

  function initWidget(widget) {
    const addButton = widget.querySelector('.add-option-row');
    const tbody = widget.querySelector('.options-table-body');
    const dataScript = widget.querySelector('.options-initial-data');

    // Get language codes from table headers
    const langCodes = [];
    const langHeaders = widget.querySelectorAll('thead th[data-lang-code]');
    langHeaders.forEach(function (th) {
      langCodes.push(th.dataset.langCode);
    });

    // Parse initial data
    let initialData = {};
    if (dataScript && dataScript.textContent.trim()) {
      try {
        initialData = JSON.parse(dataScript.textContent);
      } catch (e) {
        console.error('Failed to parse initial data:', e);
      }
    }

    // Populate existing rows
    const choices = initialData.choices || [];
    choices.forEach(function (choice) {
      addRow(tbody, langCodes, choice.value, choice.label_translations || {});
    });

    // If no rows, add one empty row
    if (choices.length === 0) {
      addRow(tbody, langCodes, '', {});
    }

    // Add click handler for add button
    addButton.addEventListener('click', function () {
      addRow(tbody, langCodes, '', {});
    });

    // Initialize hidden input with current table data
    serializeOptionsWidget(widget);

    // Add event delegation for input changes
    tbody.addEventListener('input', function (e) {
      if (e.target.matches('.option-value, .option-label')) {
        serializeOptionsWidget(widget);
      }
    });
  }

  function addRow(tbody, langCodes, value, labelTranslations) {
    const row = document.createElement('tr');
    row.dataset.rowId = rowCounter++;

    // Value column
    const valueCell = document.createElement('td');
    const valueInput = document.createElement('input');
    valueInput.type = 'text';
    valueInput.className = 'option-value';
    valueInput.value = value || '';
    valueCell.appendChild(valueInput);
    row.appendChild(valueCell);

    // Language columns
    langCodes.forEach(function (langCode) {
      const langCell = document.createElement('td');
      const langInput = document.createElement('input');
      langInput.type = 'text';
      langInput.className = 'option-label';
      langInput.dataset.lang = langCode;
      langInput.value = labelTranslations[langCode] || '';
      langCell.appendChild(langInput);
      row.appendChild(langCell);
    });

    // Actions column
    const actionsCell = document.createElement('td');
    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'button btn-remove-row';
    removeButton.textContent = 'Remove';
    removeButton.addEventListener('click', function () {
      row.remove();
      // Find the widget container and serialize
      const widget = tbody.closest('.options-widget');
      if (widget) {
        serializeOptionsWidget(widget);
      }
    });
    actionsCell.appendChild(removeButton);
    row.appendChild(actionsCell);

    tbody.appendChild(row);
  }

  function serializeOptionsWidget(widget) {
    const hiddenInput = widget.querySelector('.options-hidden-input');
    const tbody = widget.querySelector('.options-table-body');
    const rows = tbody.querySelectorAll('tr');

    const choices = [];

    rows.forEach(function (row) {
      const valueInput = row.querySelector('.option-value');
      const value = valueInput.value.trim();

      // Skip rows with empty values
      if (!value) {
        return;
      }

      const labelInputs = row.querySelectorAll('.option-label');
      const labelTranslations = {};

      labelInputs.forEach(function (input) {
        const lang = input.dataset.lang;
        const labelValue = input.value.trim();
        if (labelValue) {
          labelTranslations[lang] = labelValue;
        }
      });

      choices.push({
        value: value,
        label_translations: labelTranslations,
      });
    });

    const result = {
      choices: choices,
    };

    hiddenInput.value = JSON.stringify(result);
  }
})();
