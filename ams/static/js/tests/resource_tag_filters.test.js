/**
 * Unit tests for resource_tag_filters.js
 */

describe('Resource Tag Filters', () => {
  let container;

  function loadScript() {
    const fs = require('fs');
    const path = require('path');
    const sourceCode = fs.readFileSync(
      path.join(__dirname, '../resource_tag_filters.js'),
      'utf8'
    );
    eval(sourceCode);
    document.dispatchEvent(new Event('DOMContentLoaded'));
  }

  function buildCategory({ toggleId = '1', checked = [] } = {}) {
    const checkbox = (value, isChecked) => `
      <input type="checkbox" name="tag" value="${value}" id="tag_${value}"
             data-tag-category="${toggleId}" ${isChecked ? 'checked' : ''} />
    `;
    return `
      <button type="button" class="resource-tag-category-toggle"
              data-category-toggle="${toggleId}" aria-pressed="false">
        Category ${toggleId}
      </button>
      ${checkbox('a' + toggleId, checked.includes('a' + toggleId))}
      ${checkbox('b' + toggleId, checked.includes('b' + toggleId))}
    `;
  }

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
  });

  afterEach(() => {
    document.body.removeChild(container);
    jest.resetModules();
  });

  test('clicking toggle with none checked checks all tags in the category', () => {
    container.innerHTML = buildCategory({ toggleId: '1' });
    loadScript();

    const toggle = container.querySelector('[data-category-toggle="1"]');
    toggle.click();

    const checkboxes = container.querySelectorAll('[data-tag-category="1"]');
    checkboxes.forEach((checkbox) => expect(checkbox.checked).toBe(true));
    expect(toggle.getAttribute('aria-pressed')).toBe('true');
  });

  test('clicking toggle again with all checked clears them', () => {
    container.innerHTML = buildCategory({ toggleId: '1' });
    loadScript();

    const toggle = container.querySelector('[data-category-toggle="1"]');
    toggle.click();
    toggle.click();

    const checkboxes = container.querySelectorAll('[data-tag-category="1"]');
    checkboxes.forEach((checkbox) => expect(checkbox.checked).toBe(false));
    expect(toggle.getAttribute('aria-pressed')).toBe('false');
  });

  test('clicking toggle with some checked selects all (select-all, not clear)', () => {
    container.innerHTML = buildCategory({ toggleId: '1', checked: ['a1'] });
    loadScript();

    const toggle = container.querySelector('[data-category-toggle="1"]');
    toggle.click();

    const checkboxes = container.querySelectorAll('[data-tag-category="1"]');
    checkboxes.forEach((checkbox) => expect(checkbox.checked).toBe(true));
  });

  test('initialises aria-pressed to true when all tags pre-checked from server render', () => {
    container.innerHTML = buildCategory({
      toggleId: '1',
      checked: ['a1', 'b1'],
    });
    loadScript();

    const toggle = container.querySelector('[data-category-toggle="1"]');
    expect(toggle.getAttribute('aria-pressed')).toBe('true');
  });

  test('toggling an individual checkbox keeps aria-pressed in sync', () => {
    container.innerHTML = buildCategory({
      toggleId: '1',
      checked: ['a1', 'b1'],
    });
    loadScript();

    const toggle = container.querySelector('[data-category-toggle="1"]');
    const checkboxA = container.querySelector('#tag_a1');

    checkboxA.checked = false;
    checkboxA.dispatchEvent(new Event('change'));

    expect(toggle.getAttribute('aria-pressed')).toBe('false');

    checkboxA.checked = true;
    checkboxA.dispatchEvent(new Event('change'));

    expect(toggle.getAttribute('aria-pressed')).toBe('true');
  });

  test('does not affect checkboxes in a different category', () => {
    container.innerHTML =
      buildCategory({ toggleId: '1' }) +
      buildCategory({ toggleId: '2', checked: ['a2'] });
    loadScript();

    const toggle1 = container.querySelector('[data-category-toggle="1"]');
    toggle1.click();

    const category2Checkboxes = container.querySelectorAll(
      '[data-tag-category="2"]'
    );
    expect(category2Checkboxes[0].checked).toBe(true);
    expect(category2Checkboxes[1].checked).toBe(false);
  });
});
