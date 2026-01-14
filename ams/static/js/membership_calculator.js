/**
 * Membership Calculator Module
 * Shared utilities for membership seat calculations, date handling, and UI updates
 */
const MembershipCalculator = (function () {
  'use strict';

  // ============================================================================
  // DATE UTILITIES
  // ============================================================================

  /**
   * Parse ISO date string (yyyy-mm-dd) to Date object
   */
  function parseDate(str) {
    const [y, m, d] = str.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  /**
   * Format Date object as DD/MM/YYYY
   */
  function formatDate(date) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  }

  /**
   * Add duration to date
   * @param {Date} date - Starting date
   * @param {Object} duration - Duration object {years, months, weeks, days}
   */
  function addDuration(date, duration) {
    let newDate = new Date(date.getTime());
    if (duration.years)
      newDate.setFullYear(newDate.getFullYear() + duration.years);
    if (duration.months) newDate.setMonth(newDate.getMonth() + duration.months);
    if (duration.weeks) newDate.setDate(newDate.getDate() + 7 * duration.weeks);
    if (duration.days) newDate.setDate(newDate.getDate() + duration.days);
    return newDate;
  }

  // ============================================================================
  // SEAT CALCULATION
  // ============================================================================

  /**
   * Calculate chargeable and free seats
   * @param {Object} config
   * @param {number} config.totalSeats - Total seats requested/being added
   * @param {number} [config.maxChargedSeats] - Maximum seats that can be charged
   * @param {number} [config.currentChargeableSeats=0] - Already charged seats (for add-seats scenario)
   * @returns {Object} {chargedSeats, freeSeats}
   */
  function calculateSeatBreakdown(config) {
    const { totalSeats, maxChargedSeats, currentChargeableSeats = 0 } = config;

    if (!maxChargedSeats) {
      return {
        chargedSeats: totalSeats,
        freeSeats: 0,
      };
    }

    // Calculate how many more seats can be charged
    const remainingChargeable = Math.max(
      0,
      maxChargedSeats - currentChargeableSeats
    );
    const chargedSeats = Math.min(totalSeats, remainingChargeable);
    const freeSeats = totalSeats - chargedSeats;

    return { chargedSeats, freeSeats };
  }

  // ============================================================================
  // COST CALCULATION
  // ============================================================================

  /**
   * Calculate total cost for new membership
   * @param {Object} config
   * @param {number} config.costPerSeat - Cost per seat
   * @param {number} config.chargedSeats - Number of charged seats
   * @returns {number} Total cost
   */
  function calculateTotalCost(config) {
    const { costPerSeat, chargedSeats } = config;
    return costPerSeat * chargedSeats;
  }

  /**
   * Calculate pro-rata cost for adding seats
   * @param {Object} config
   * @param {number} config.prorataCostPerSeat - Server-calculated pro-rata cost per seat
   * @param {number} config.chargedSeats - Number of charged seats
   * @returns {number} Total pro-rata cost
   */
  function calculateProrataCost(config) {
    const { prorataCostPerSeat, chargedSeats } = config;
    return prorataCostPerSeat * chargedSeats;
  }

  // ============================================================================
  // UI UPDATES
  // ============================================================================

  /**
   * Format currency value
   */
  function formatCurrency(amount) {
    return `$${amount.toFixed(2)}`;
  }

  /**
   * Update seat breakdown info box
   * @param {Object} config
   * @param {HTMLElement} config.infoBox - Container element
   * @param {HTMLElement} config.messageElement - Message element
   * @param {number} config.chargedSeats - Number of charged seats
   * @param {number} config.freeSeats - Number of free seats
   * @param {number} config.costPerSeat - Cost per seat
   * @param {number} config.maxChargedSeats - Max charged seats limit
   */
  function updateSeatInfoBox(config) {
    const {
      infoBox,
      messageElement,
      chargedSeats,
      freeSeats,
      costPerSeat,
      maxChargedSeats,
    } = config;

    if (!infoBox || !messageElement) return;

    if (maxChargedSeats && freeSeats > 0) {
      const costFormatted = formatCurrency(costPerSeat);
      messageElement.innerHTML =
        `<strong>Note:</strong> First ${chargedSeats} seat(s) are charged at ${costFormatted} each. ` +
        `Additional ${freeSeats} seat(s) are free.`;
      infoBox.classList.remove('d-none');
    } else if (maxChargedSeats) {
      const costFormatted = formatCurrency(costPerSeat);
      messageElement.innerHTML =
        `<strong>Pricing:</strong> First ${maxChargedSeats} seat(s) are charged at ${costFormatted} each. ` +
        `Additional seats are free.`;
      infoBox.classList.remove('d-none');
    } else {
      infoBox.classList.add('d-none');
    }
  }

  /**
   * Update seat breakdown display (for add-seats view)
   * @param {Object} config
   * @param {HTMLElement} config.breakdownBox - Container element
   * @param {HTMLElement} config.totalElement - Total seats element
   * @param {HTMLElement} config.chargeableElement - Chargeable seats element
   * @param {HTMLElement} config.freeElement - Free seats element
   * @param {number} config.totalSeats - Total seats being added
   * @param {number} config.chargedSeats - Charged seats
   * @param {number} config.freeSeats - Free seats
   * @param {boolean} config.hasMaxChargedSeats - Whether max_charged_seats is set
   */
  function updateSeatBreakdownDisplay(config) {
    const {
      breakdownBox,
      totalElement,
      chargeableElement,
      freeElement,
      totalSeats,
      chargedSeats,
      freeSeats,
      hasMaxChargedSeats,
    } = config;

    if (!breakdownBox) return;

    if (hasMaxChargedSeats && totalSeats > 0) {
      if (totalElement) totalElement.textContent = totalSeats;
      if (chargeableElement) chargeableElement.textContent = chargedSeats;
      if (freeElement) freeElement.textContent = freeSeats;
      breakdownBox.classList.remove('d-none');
    } else {
      breakdownBox.classList.add('d-none');
    }
  }

  // ============================================================================
  // HIGH-LEVEL CALCULATORS
  // ============================================================================

  /**
   * Calculate membership details for new membership creation
   * @param {Object} config
   * @param {Object} config.membershipOption - Option data {cost, duration, max_charged_seats}
   * @param {string} config.startDate - ISO date string
   * @param {number} config.seatCount - Number of seats
   * @returns {Object} Calculation results
   */
  function calculateNewMembership(config) {
    const { membershipOption, startDate, seatCount } = config;

    const start = parseDate(startDate);
    const expiry = addDuration(start, membershipOption.duration);

    const seatBreakdown = calculateSeatBreakdown({
      totalSeats: seatCount,
      maxChargedSeats: membershipOption.max_charged_seats,
    });

    const totalCost = calculateTotalCost({
      costPerSeat: membershipOption.cost,
      chargedSeats: seatBreakdown.chargedSeats,
    });

    return {
      expiryDate: expiry,
      expiryDateFormatted: formatDate(expiry),
      totalCost,
      totalCostFormatted: formatCurrency(totalCost),
      chargedSeats: seatBreakdown.chargedSeats,
      freeSeats: seatBreakdown.freeSeats,
    };
  }

  /**
   * Calculate membership details for adding seats to existing membership
   * @param {Object} config
   * @param {number} config.seatsToAdd - Number of seats to add
   * @param {number} config.prorataCostPerSeat - Server-calculated pro-rata cost per seat
   * @param {number} [config.maxChargedSeats] - Maximum seats that can be charged
   * @param {number} [config.currentChargeableSeats=0] - Already charged seats
   * @returns {Object} Calculation results
   */
  function calculateAddSeats(config) {
    const {
      seatsToAdd,
      prorataCostPerSeat,
      maxChargedSeats,
      currentChargeableSeats = 0,
    } = config;

    const seatBreakdown = calculateSeatBreakdown({
      totalSeats: seatsToAdd,
      maxChargedSeats,
      currentChargeableSeats,
    });

    const prorataCost = calculateProrataCost({
      prorataCostPerSeat,
      chargedSeats: seatBreakdown.chargedSeats,
    });

    return {
      prorataCost,
      prorataCostFormatted: formatCurrency(prorataCost),
      chargedSeats: seatBreakdown.chargedSeats,
      freeSeats: seatBreakdown.freeSeats,
      totalSeats: seatsToAdd,
    };
  }

  // ============================================================================
  // PUBLIC API
  // ============================================================================

  return {
    // Date utilities
    parseDate,
    formatDate,
    addDuration,

    // Calculation functions
    calculateSeatBreakdown,
    calculateTotalCost,
    calculateProrataCost,

    // UI helpers
    formatCurrency,
    updateSeatInfoBox,
    updateSeatBreakdownDisplay,

    // High-level calculators
    calculateNewMembership,
    calculateAddSeats,
  };
})();
