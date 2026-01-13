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

  const optionSelect = document.getElementById('id_membership_option');
  const startInput = document.getElementById('id_start_date');
  const seatInput = document.getElementById('id_seat_count');
  const expiryEl = document.getElementById('membership-expiry-date');
  const costEl = document.getElementById('membership-total-cost');

  function parseDate(str) {
    // yyyy-mm-dd
    const [y, m, d] = str.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function formatDate(date) {
    // Format as DD/MM/YYYY
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  }

  function addDuration(date, duration) {
    let newDate = new Date(date.getTime());
    if (duration.years)
      newDate.setFullYear(newDate.getFullYear() + duration.years);
    if (duration.months) newDate.setMonth(newDate.getMonth() + duration.months);
    if (duration.weeks) newDate.setDate(newDate.getDate() + 7 * duration.weeks);
    if (duration.days) newDate.setDate(newDate.getDate() + duration.days);
    return newDate;
  }

  function updateCalculations() {
    if (!optionSelect || !startInput) return;

    const optionId = optionSelect.value;
    const startVal = startInput.value;
    const seatCount = parseInt(seatInput ? seatInput.value : 1, 10) || 1;

    if (optionId && startVal && membershipData && membershipData[optionId]) {
      const option = membershipData[optionId];
      const duration = {
        years: option.years,
        months: option.months,
        weeks: option.weeks,
        days: option.days,
      };

      // Calculate expiry date
      const startDate = parseDate(startVal);
      const expiryDate = addDuration(startDate, duration);
      expiryEl.textContent = formatDate(expiryDate);

      // Calculate chargeable seats
      const maxCharged = option.max_charged_seats;
      let chargedSeats = seatCount;
      let freeSeats = 0;

      if (maxCharged && seatCount > maxCharged) {
        chargedSeats = maxCharged;
        freeSeats = seatCount - maxCharged;
      }

      // Calculate total cost (only for charged seats)
      const totalCost = option.cost * chargedSeats;
      costEl.textContent = `$${totalCost.toFixed(2)}`;

      // Show charged/free seats info if applicable
      const infoBox = document.getElementById('charged-seats-info');
      const infoMessage = document.getElementById('charged-seats-message');

      if (infoBox && infoMessage) {
        if (maxCharged && seatCount > maxCharged) {
          infoMessage.innerHTML = `<strong>Note:</strong> First ${chargedSeats} seat(s) are charged at $${option.cost.toFixed(
            2,
          )} each. Additional ${freeSeats} seat(s) are free.`;
          infoBox.classList.remove('d-none');
        } else if (maxCharged) {
          infoMessage.innerHTML = `<strong>Pricing:</strong> First ${maxCharged} seat(s) are charged at $${option.cost.toFixed(
            2,
          )} each. Additional seats are free.`;
          infoBox.classList.remove('d-none');
        } else {
          infoBox.classList.add('d-none');
        }
      }

      // Update max seats on input if applicable
      if (seatInput && option.max_seats) {
        seatInput.setAttribute('max', option.max_seats);
      }
    } else {
      expiryEl.textContent = '—';
      costEl.textContent = '—';

      const infoBox = document.getElementById('charged-seats-info');
      if (infoBox) {
        infoBox.classList.add('d-none');
      }
    }
  }

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
