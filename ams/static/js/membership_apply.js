// membership_apply.js

document.addEventListener('DOMContentLoaded', function () {
  // Load durations from JSON script block
  let membershipDurations = {};
  const durationsScript = document.getElementById('membership-durations-data');
  if (durationsScript) {
    try {
      membershipDurations = JSON.parse(durationsScript.textContent);
    } catch (e) {
      console.error('Failed to parse membership durations data:', e);
    }
  }

  const select = document.getElementById('id_membership_option');
  const startInput = document.getElementById('id_start_date');
  const endEl = document.getElementById('membership-end-date');

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

  function updateEnd() {
    if (!select || !startInput) return;
    const val = select.value;
    const startVal = startInput.value;
    if (val && startVal && membershipDurations && membershipDurations[val]) {
      const duration = membershipDurations[val];
      const startDate = parseDate(startVal);
      const endDate = addDuration(startDate, duration);
      endEl.textContent = formatDate(endDate);
    } else {
      endEl.textContent = '—';
    }
  }

  if (select) {
    select.addEventListener('change', updateEnd);
  }
  if (startInput) {
    startInput.addEventListener('change', updateEnd);
  }
  updateEnd();
});
