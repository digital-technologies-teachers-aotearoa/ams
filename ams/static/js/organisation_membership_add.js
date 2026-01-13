// organisation_membership_add.js

document.addEventListener('DOMContentLoaded', function () {
  // Load membership data from JSON script block
  let membershipData = {};
  const dataScript = document.getElementById('membership-data');
  if (dataScript) {
    try {
      membershipData = JSON.parse(dataScript.textContent);
    } catch (e) {
      console.error('Failed to parse membership data:', e);
    }
  }

  // Get DOM elements
  const optionSelect = document.getElementById('id_membership_option');
  const startInput = document.getElementById('id_start_date');
  const seatInput = document.getElementById('id_seat_count');
  const expiryEl = document.getElementById('membership-expiry-date');
  const costEl = document.getElementById('membership-total-cost');
  const infoBox = document.getElementById('charged-seats-info');
  const infoMessage = document.getElementById('charged-seats-message');

  function updateCalculations() {
    if (!optionSelect || !startInput) return;

    const optionId = optionSelect.value;
    const startVal = startInput.value;
    const seatCount = parseInt(seatInput ? seatInput.value : 1, 10) || 1;

    if (optionId && startVal && membershipData && membershipData[optionId]) {
      const option = membershipData[optionId];

      // Use shared calculator
      const result = MembershipCalculator.calculateNewMembership({
        membershipOption: {
          cost: option.cost,
          max_charged_seats: option.max_charged_seats,
          duration: {
            years: option.years,
            months: option.months,
            weeks: option.weeks,
            days: option.days,
          },
        },
        startDate: startVal,
        seatCount: seatCount,
      });

      // Update UI
      expiryEl.textContent = result.expiryDateFormatted;
      costEl.textContent = result.totalCostFormatted;

      MembershipCalculator.updateSeatInfoBox({
        infoBox,
        messageElement: infoMessage,
        chargedSeats: result.chargedSeats,
        freeSeats: result.freeSeats,
        costPerSeat: option.cost,
        maxChargedSeats: option.max_charged_seats,
      });

      // Update max seats on input if applicable
      if (seatInput && option.max_seats) {
        seatInput.setAttribute('max', option.max_seats);
      }
    } else {
      expiryEl.textContent = '—';
      costEl.textContent = '—';
      if (infoBox) {
        infoBox.classList.add('d-none');
      }
    }
  }

  // Event listeners
  if (optionSelect) {
    optionSelect.addEventListener('change', updateCalculations);
  }
  if (startInput) {
    startInput.addEventListener('change', updateCalculations);
  }
  if (seatInput) {
    seatInput.addEventListener('input', updateCalculations);
  }

  // Initial calculation on page load
  updateCalculations();
});
