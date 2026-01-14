/**
 * Unit tests for membership_calculator.js
 */

// Mock the global MembershipCalculator (it's defined as IIFE in the source)
// We'll need to import or execute the source file first
const fs = require('fs');
const path = require('path');

// Load the source file and make MembershipCalculator globally available
let sourceCode = fs.readFileSync(
  path.join(__dirname, '../membership_calculator.js'),
  'utf8'
);

// Replace const declaration with global assignment to make it available
sourceCode = sourceCode.replace(
  'const MembershipCalculator =',
  'global.MembershipCalculator ='
);

// Execute the code
eval(sourceCode);

// Now MembershipCalculator is available
const calculator = global.MembershipCalculator;

describe('MembershipCalculator', () => {
  describe('Date Utilities', () => {
    describe('parseDate', () => {
      test('parses ISO date string correctly', () => {
        const result = calculator.parseDate('2026-01-14');
        expect(result).toBeInstanceOf(Date);
        expect(result.getFullYear()).toBe(2026);
        expect(result.getMonth()).toBe(0); // January = 0
        expect(result.getDate()).toBe(14);
      });

      test('handles different months correctly', () => {
        const march = calculator.parseDate('2026-03-15');
        expect(march.getMonth()).toBe(2); // March = 2
      });
    });

    describe('formatDate', () => {
      test('formats date as DD/MM/YYYY', () => {
        const date = new Date(2026, 0, 14); // Jan 14, 2026
        expect(calculator.formatDate(date)).toBe('14/01/2026');
      });

      test('pads single digit days and months', () => {
        const date = new Date(2026, 8, 5); // Sep 5, 2026
        expect(calculator.formatDate(date)).toBe('05/09/2026');
      });

      test('handles end of year', () => {
        const date = new Date(2026, 11, 31); // Dec 31, 2026
        expect(calculator.formatDate(date)).toBe('31/12/2026');
      });
    });

    describe('addDuration', () => {
      test('adds years correctly', () => {
        const start = new Date(2026, 0, 14);
        const result = calculator.addDuration(start, { years: 1 });
        expect(result.getFullYear()).toBe(2027);
        expect(result.getMonth()).toBe(0);
        expect(result.getDate()).toBe(14);
      });

      test('adds months correctly', () => {
        const start = new Date(2026, 0, 14);
        const result = calculator.addDuration(start, { months: 3 });
        expect(result.getMonth()).toBe(3); // April
      });

      test('adds weeks correctly', () => {
        const start = new Date(2026, 0, 14);
        const result = calculator.addDuration(start, { weeks: 2 });
        expect(result.getDate()).toBe(28);
      });

      test('adds days correctly', () => {
        const start = new Date(2026, 0, 14);
        const result = calculator.addDuration(start, { days: 10 });
        expect(result.getDate()).toBe(24);
      });

      test('adds combined duration correctly', () => {
        const start = new Date(2026, 0, 1);
        const result = calculator.addDuration(start, {
          years: 1,
          months: 2,
          weeks: 1,
          days: 3,
        });
        expect(result.getFullYear()).toBe(2027);
        expect(result.getMonth()).toBe(2); // March
        expect(result.getDate()).toBe(11); // 1 + 7(week) + 3(days)
      });

      test('does not mutate original date', () => {
        const start = new Date(2026, 0, 14);
        const original = start.getTime();
        calculator.addDuration(start, { days: 10 });
        expect(start.getTime()).toBe(original);
      });
    });
  });

  describe('Seat Calculation', () => {
    describe('calculateSeatBreakdown', () => {
      test('all seats charged when no max limit', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 5,
          maxChargedSeats: null,
        });
        expect(result.chargedSeats).toBe(5);
        expect(result.freeSeats).toBe(0);
      });

      test('all seats charged when under limit', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 3,
          maxChargedSeats: 5,
        });
        expect(result.chargedSeats).toBe(3);
        expect(result.freeSeats).toBe(0);
      });

      test('splits charged and free seats when over limit', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 7,
          maxChargedSeats: 5,
        });
        expect(result.chargedSeats).toBe(5);
        expect(result.freeSeats).toBe(2);
      });

      test('accounts for current chargeable seats (add seats scenario)', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 3,
          maxChargedSeats: 4,
          currentChargeableSeats: 2,
        });
        expect(result.chargedSeats).toBe(2); // Can only charge 2 more (4 - 2 = 2)
        expect(result.freeSeats).toBe(1);
      });

      test('all free when current seats at max', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 3,
          maxChargedSeats: 4,
          currentChargeableSeats: 4,
        });
        expect(result.chargedSeats).toBe(0);
        expect(result.freeSeats).toBe(3);
      });

      test('handles exact limit match', () => {
        const result = calculator.calculateSeatBreakdown({
          totalSeats: 5,
          maxChargedSeats: 5,
        });
        expect(result.chargedSeats).toBe(5);
        expect(result.freeSeats).toBe(0);
      });
    });
  });

  describe('Cost Calculation', () => {
    describe('calculateTotalCost', () => {
      test('calculates cost correctly', () => {
        const result = calculator.calculateTotalCost({
          costPerSeat: 50.0,
          chargedSeats: 3,
        });
        expect(result).toBe(150.0);
      });

      test('handles zero seats', () => {
        const result = calculator.calculateTotalCost({
          costPerSeat: 50.0,
          chargedSeats: 0,
        });
        expect(result).toBe(0);
      });

      test('handles decimal costs', () => {
        const result = calculator.calculateTotalCost({
          costPerSeat: 99.99,
          chargedSeats: 2,
        });
        expect(result).toBe(199.98);
      });
    });

    describe('calculateProrataCost', () => {
      test('calculates pro-rata cost correctly', () => {
        const result = calculator.calculateProrataCost({
          prorataCostPerSeat: 45.5,
          chargedSeats: 2,
        });
        expect(result).toBe(91.0);
      });
    });
  });

  describe('UI Helpers', () => {
    describe('formatCurrency', () => {
      test('formats as $XX.XX', () => {
        expect(calculator.formatCurrency(50)).toBe('$50.00');
        expect(calculator.formatCurrency(99.99)).toBe('$99.99');
        expect(calculator.formatCurrency(100.5)).toBe('$100.50');
      });

      test('handles zero', () => {
        expect(calculator.formatCurrency(0)).toBe('$0.00');
      });
    });

    describe('updateSeatInfoBox', () => {
      let mockInfoBox, mockMessageElement;

      beforeEach(() => {
        // Create mock DOM elements
        mockInfoBox = {
          classList: {
            add: jest.fn(),
            remove: jest.fn(),
          },
        };
        mockMessageElement = {
          innerHTML: '',
        };
      });

      test('shows message when free seats exist', () => {
        calculator.updateSeatInfoBox({
          infoBox: mockInfoBox,
          messageElement: mockMessageElement,
          chargedSeats: 4,
          freeSeats: 2,
          costPerSeat: 50.0,
          maxChargedSeats: 4,
        });

        expect(mockMessageElement.innerHTML).toContain('First 4 seat(s)');
        expect(mockMessageElement.innerHTML).toContain('$50.00');
        expect(mockMessageElement.innerHTML).toContain(
          'Additional 2 seat(s) are free'
        );
        expect(mockInfoBox.classList.remove).toHaveBeenCalledWith('d-none');
      });

      test('shows pricing info when at limit but no free seats yet', () => {
        calculator.updateSeatInfoBox({
          infoBox: mockInfoBox,
          messageElement: mockMessageElement,
          chargedSeats: 3,
          freeSeats: 0,
          costPerSeat: 50.0,
          maxChargedSeats: 4,
        });

        expect(mockMessageElement.innerHTML).toContain('Pricing:');
        expect(mockMessageElement.innerHTML).toContain('First 4 seat(s)');
        expect(mockInfoBox.classList.remove).toHaveBeenCalledWith('d-none');
      });

      test('hides box when no max charged seats', () => {
        calculator.updateSeatInfoBox({
          infoBox: mockInfoBox,
          messageElement: mockMessageElement,
          chargedSeats: 5,
          freeSeats: 0,
          costPerSeat: 50.0,
          maxChargedSeats: null,
        });

        expect(mockInfoBox.classList.add).toHaveBeenCalledWith('d-none');
      });
    });
  });

  describe('High-Level Calculators', () => {
    describe('calculateNewMembership', () => {
      test('calculates all membership details correctly', () => {
        const result = calculator.calculateNewMembership({
          membershipOption: {
            cost: 50.0,
            max_charged_seats: 4,
            duration: { years: 1 },
          },
          startDate: '2026-01-14',
          seatCount: 5,
        });

        expect(result.expiryDateFormatted).toBe('14/01/2027');
        expect(result.totalCost).toBe(200.0); // 4 seats × $50
        expect(result.totalCostFormatted).toBe('$200.00');
        expect(result.chargedSeats).toBe(4);
        expect(result.freeSeats).toBe(1);
        expect(result.expiryDate).toBeInstanceOf(Date);
      });

      test('handles membership with no max seats limit', () => {
        const result = calculator.calculateNewMembership({
          membershipOption: {
            cost: 99.99,
            max_charged_seats: null,
            duration: { months: 1 },
          },
          startDate: '2026-01-14',
          seatCount: 3,
        });

        expect(result.chargedSeats).toBe(3);
        expect(result.freeSeats).toBe(0);
        expect(result.totalCost).toBeCloseTo(299.97, 2);
      });
    });

    describe('calculateAddSeats', () => {
      test('calculates pro-rata for additional seats', () => {
        const result = calculator.calculateAddSeats({
          seatsToAdd: 3,
          prorataCostPerSeat: 45.5,
          maxChargedSeats: 4,
          currentChargeableSeats: 2,
        });

        expect(result.chargedSeats).toBe(2); // Can charge 2 more
        expect(result.freeSeats).toBe(1);
        expect(result.prorataCost).toBe(91.0); // 2 × 45.5
        expect(result.prorataCostFormatted).toBe('$91.00');
        expect(result.totalSeats).toBe(3);
      });

      test('handles all free seats when at capacity', () => {
        const result = calculator.calculateAddSeats({
          seatsToAdd: 5,
          prorataCostPerSeat: 50.0,
          maxChargedSeats: 4,
          currentChargeableSeats: 4,
        });

        expect(result.chargedSeats).toBe(0);
        expect(result.freeSeats).toBe(5);
        expect(result.prorataCost).toBe(0);
      });
    });
  });
});
