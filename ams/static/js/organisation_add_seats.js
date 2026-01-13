// organisation_add_seats.js

document.addEventListener('DOMContentLoaded', function () {
  // Get pre-calculated pro-rata cost for 1 seat from server via data attributes
  const container = document.querySelector(
    '.container[data-prorata-cost-per-seat]',
  );
  if (!container) return;

  const prorataCostPerSeat = parseFloat(
    container.dataset.prorataCostPerSeat || '0',
  );
  const maxChargedSeats = container.dataset.maxChargedSeats
    ? parseInt(container.dataset.maxChargedSeats)
    : null;
  const currentChargeableSeats = parseInt(
    container.dataset.currentChargeableSeats || '0',
  );

  // Get form elements
  const seatsInput = document.getElementById('id_seats_to_add');
  const previewElement = document.getElementById('prorata-preview');
  const breakdownBox = document.getElementById('seats-breakdown');
  const breakdownTotal = document.getElementById('breakdown-total');
  const breakdownChargeable = document.getElementById('breakdown-chargeable');
  const breakdownFree = document.getElementById('breakdown-free');

  if (!seatsInput || !previewElement) {
    return;
  }

  function updateProrataPreview() {
    const seats = parseInt(seatsInput.value) || 0;

    if (seats <= 0) {
      previewElement.textContent = 'Enter number of seats to see the cost.';
      if (breakdownBox) {
        breakdownBox.classList.add('d-none');
      }
      return;
    }

    // Use shared calculator
    const result = MembershipCalculator.calculateAddSeats({
      seatsToAdd: seats,
      prorataCostPerSeat,
      maxChargedSeats,
      currentChargeableSeats,
    });

    // Update preview message
    if (result.chargedSeats === seats) {
      previewElement.textContent = `Estimated cost: ${result.prorataCostFormatted} for ${seats} seat(s)`;
    } else {
      previewElement.textContent =
        `Estimated cost: ${result.prorataCostFormatted} for ${result.chargedSeats} charged seat(s) ` +
        `(${result.freeSeats} free)`;
    }

    // Update breakdown display
    MembershipCalculator.updateSeatBreakdownDisplay({
      breakdownBox,
      totalElement: breakdownTotal,
      chargeableElement: breakdownChargeable,
      freeElement: breakdownFree,
      totalSeats: seats,
      chargedSeats: result.chargedSeats,
      freeSeats: result.freeSeats,
      hasMaxChargedSeats: !!maxChargedSeats,
    });
  }

  // Event listener
  seatsInput.addEventListener('input', updateProrataPreview);

  // Initial calculation
  updateProrataPreview();
});
