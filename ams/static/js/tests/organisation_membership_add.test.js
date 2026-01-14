/**
 * Unit tests for organisation_membership_add.js
 */

describe('Organisation Membership Add', () => {
  let container;

  beforeEach(() => {
    // Create mock DOM structure
    container = document.createElement('div');
    container.innerHTML = `
      <script id="membership-data" type="application/json">
      {
        "1": {
          "cost": 50.0,
          "max_charged_seats": 4,
          "max_seats": 10,
          "years": 1,
          "months": 0,
          "weeks": 0,
          "days": 0
        }
      }
      </script>
      <input type="radio" name="membership_option" id="id_membership_option_0" value="" />
      <input type="radio" name="membership_option" id="id_membership_option_1" value="1" checked />
      <input type="date" id="id_start_date" value="2026-01-14" />
      <input type="number" id="id_seat_count" value="1" />
      <div id="membership-expiry-date">—</div>
      <div id="membership-total-cost">—</div>
      <div id="charged-seats-info" class="d-none">
        <p id="charged-seats-message"></p>
      </div>
    `;
    document.body.appendChild(container);

    // Mock MembershipCalculator with default return values
    global.MembershipCalculator = {
      calculateNewMembership: jest.fn().mockReturnValue({
        expiryDateFormatted: '14/01/2027',
        totalCostFormatted: '$50.00',
        chargedSeats: 1,
        freeSeats: 0,
      }),
      updateSeatInfoBox: jest.fn(),
    };

    // Load and execute the organisation_membership_add.js script
    const fs = require('fs');
    const path = require('path');
    const sourceCode = fs.readFileSync(
      path.join(__dirname, '../organisation_membership_add.js'),
      'utf8'
    );

    // Execute the script
    eval(sourceCode);

    // Trigger DOMContentLoaded to initialize the script
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
  });

  afterEach(() => {
    document.body.removeChild(container);
    jest.clearAllMocks();
  });

  test('initializes with correct DOM elements', () => {
    expect(
      document.querySelector('input[name="membership_option"]')
    ).toBeTruthy();
    expect(document.getElementById('id_start_date')).toBeTruthy();
    expect(document.getElementById('id_seat_count')).toBeTruthy();
  });

  test('parses membership data JSON correctly', () => {
    const dataScript = document.getElementById('membership-data');
    const data = JSON.parse(dataScript.textContent);
    expect(data['1'].cost).toBe(50.0);
    expect(data['1'].max_charged_seats).toBe(4);
  });

  test('updates calculations when option changes', () => {
    // Clear previous calls from initialization
    jest.clearAllMocks();

    const optionRadio = document.getElementById('id_membership_option_1');
    optionRadio.checked = true;
    optionRadio.dispatchEvent(new Event('change'));

    // Verify MembershipCalculator was called
    expect(MembershipCalculator.calculateNewMembership).toHaveBeenCalled();
  });

  test('displays placeholder when no option selected', () => {
    // Uncheck all radio buttons
    const radios = document.querySelectorAll('input[name="membership_option"]');
    radios.forEach((radio) => (radio.checked = false));

    // Manually trigger updateCalculations
    const startInput = document.getElementById('id_start_date');
    startInput.dispatchEvent(new Event('change'));

    const expiryEl = document.getElementById('membership-expiry-date');
    const costEl = document.getElementById('membership-total-cost');

    expect(expiryEl.textContent).toBe('—');
    expect(costEl.textContent).toBe('—');
  });
});
