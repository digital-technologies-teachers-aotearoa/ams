/**
 * Unit tests for organisation_add_seats.js
 */

describe('Organisation Add Seats', () => {
  let container;

  beforeEach(() => {
    // Create mock DOM with data attributes
    container = document.createElement('div');
    container.className = 'container';
    container.setAttribute('data-prorata-cost-per-seat', '45.50');
    container.setAttribute('data-max-charged-seats', '4');
    container.setAttribute('data-current-chargeable-seats', '2');
    container.innerHTML = `
      <input type="number" id="id_seats_to_add" value="0" />
      <p id="prorata-preview">Enter number of seats to see the cost.</p>
      <div id="seats-breakdown" class="d-none">
        <span id="breakdown-total">0</span>
        <span id="breakdown-chargeable">0</span>
        <span id="breakdown-free">0</span>
      </div>
    `;
    document.body.appendChild(container);

    // Mock MembershipCalculator
    global.MembershipCalculator = {
      calculateAddSeats: jest.fn(),
      updateSeatBreakdownDisplay: jest.fn(),
    };

    // Load the source file
    const fs = require('fs');
    const path = require('path');
    const sourceCode = fs.readFileSync(
      path.join(__dirname, '../organisation_add_seats.js'),
      'utf8'
    );

    // Execute the script
    eval(sourceCode);

    // Trigger DOMContentLoaded
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
  });

  afterEach(() => {
    document.body.removeChild(container);
    jest.clearAllMocks();
  });

  test('reads data attributes correctly', () => {
    const dataContainer = document.querySelector(
      '.container[data-prorata-cost-per-seat]'
    );
    expect(parseFloat(dataContainer.dataset.prorataCostPerSeat)).toBe(45.5);
    expect(parseInt(dataContainer.dataset.maxChargedSeats)).toBe(4);
    expect(parseInt(dataContainer.dataset.currentChargeableSeats)).toBe(2);
  });

  test('shows default message when no seats entered', () => {
    const preview = document.getElementById('prorata-preview');
    const input = document.getElementById('id_seats_to_add');

    // Initial state (0 seats)
    input.value = '0';
    input.dispatchEvent(new Event('input'));

    expect(preview.textContent).toBe('Enter number of seats to see the cost.');
  });

  test('updates preview when seats entered with all charged', () => {
    MembershipCalculator.calculateAddSeats.mockReturnValue({
      chargedSeats: 2,
      freeSeats: 0,
      prorataCostFormatted: '$91.00',
      totalSeats: 2,
    });

    const input = document.getElementById('id_seats_to_add');
    const preview = document.getElementById('prorata-preview');

    input.value = '2';
    input.dispatchEvent(new Event('input'));

    expect(MembershipCalculator.calculateAddSeats).toHaveBeenCalledWith({
      seatsToAdd: 2,
      prorataCostPerSeat: 45.5,
      maxChargedSeats: 4,
      currentChargeableSeats: 2,
    });

    expect(preview.textContent).toBe('Estimated cost: $91.00 for 2 seat(s)');
  });

  test('updates preview when seats entered with free seats', () => {
    MembershipCalculator.calculateAddSeats.mockReturnValue({
      chargedSeats: 2,
      freeSeats: 1,
      prorataCostFormatted: '$91.00',
      totalSeats: 3,
    });

    const input = document.getElementById('id_seats_to_add');
    const preview = document.getElementById('prorata-preview');

    input.value = '3';
    input.dispatchEvent(new Event('input'));

    expect(preview.textContent).toBe(
      'Estimated cost: $91.00 for 2 charged seat(s) (1 free)'
    );
  });

  test('calls updateSeatBreakdownDisplay with correct parameters', () => {
    MembershipCalculator.calculateAddSeats.mockReturnValue({
      chargedSeats: 2,
      freeSeats: 1,
      prorataCostFormatted: '$91.00',
      totalSeats: 3,
    });

    const input = document.getElementById('id_seats_to_add');
    input.value = '3';
    input.dispatchEvent(new Event('input'));

    const breakdownBox = document.getElementById('seats-breakdown');
    const breakdownTotal = document.getElementById('breakdown-total');
    const breakdownChargeable = document.getElementById('breakdown-chargeable');
    const breakdownFree = document.getElementById('breakdown-free');

    expect(
      MembershipCalculator.updateSeatBreakdownDisplay
    ).toHaveBeenCalledWith({
      breakdownBox,
      totalElement: breakdownTotal,
      chargeableElement: breakdownChargeable,
      freeElement: breakdownFree,
      totalSeats: 3,
      chargedSeats: 2,
      freeSeats: 1,
      hasMaxChargedSeats: true,
    });
  });

  test('hides breakdown box when seats is zero', () => {
    const input = document.getElementById('id_seats_to_add');
    const breakdownBox = document.getElementById('seats-breakdown');

    // Remove d-none class first
    breakdownBox.classList.remove('d-none');

    input.value = '0';
    input.dispatchEvent(new Event('input'));

    expect(breakdownBox.classList.contains('d-none')).toBe(true);
  });

  test('handles missing max charged seats', () => {
    // Remove max charged seats attribute
    container.removeAttribute('data-max-charged-seats');

    // Reload the script
    const fs = require('fs');
    const path = require('path');
    const sourceCode = fs.readFileSync(
      path.join(__dirname, '../organisation_add_seats.js'),
      'utf8'
    );
    eval(sourceCode);

    // Trigger DOMContentLoaded
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);

    MembershipCalculator.calculateAddSeats.mockReturnValue({
      chargedSeats: 3,
      freeSeats: 0,
      prorataCostFormatted: '$136.50',
      totalSeats: 3,
    });

    const input = document.getElementById('id_seats_to_add');
    input.value = '3';
    input.dispatchEvent(new Event('input'));

    expect(MembershipCalculator.calculateAddSeats).toHaveBeenCalledWith({
      seatsToAdd: 3,
      prorataCostPerSeat: 45.5,
      maxChargedSeats: null,
      currentChargeableSeats: 2,
    });
  });

  test('handles invalid input gracefully', () => {
    const input = document.getElementById('id_seats_to_add');
    const preview = document.getElementById('prorata-preview');

    input.value = 'abc';
    input.dispatchEvent(new Event('input'));

    expect(preview.textContent).toBe('Enter number of seats to see the cost.');
  });

  test('handles negative input gracefully', () => {
    const input = document.getElementById('id_seats_to_add');
    const preview = document.getElementById('prorata-preview');

    input.value = '-5';
    input.dispatchEvent(new Event('input'));

    expect(preview.textContent).toBe('Enter number of seats to see the cost.');
  });
});
