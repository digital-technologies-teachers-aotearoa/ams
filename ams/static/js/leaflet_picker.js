document.addEventListener('DOMContentLoaded', function () {
  var mapEl = document.getElementById('leaflet-picker-map');
  var inputs = mapEl.parentElement.querySelectorAll('input[type="number"]');
  var latInput = inputs[0];
  var lngInput = inputs[1];

  var defaultLat = parseFloat(latInput.value) || -41.2865;
  var defaultLng = parseFloat(lngInput.value) || 174.7762;
  var defaultZoom = latInput.value && lngInput.value ? 13 : 5;

  var map = L.map('leaflet-picker-map').setView(
    [defaultLat, defaultLng],
    defaultZoom
  );
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin',
  }).addTo(map);
  setTimeout(function () {
    map.invalidateSize();
  }, 0);

  var marker = null;
  if (latInput.value && lngInput.value) {
    marker = L.marker([defaultLat, defaultLng]).addTo(map);
  }

  map.on('click', function (e) {
    var lat = e.latlng.lat.toFixed(6);
    var lng = e.latlng.lng.toFixed(6);
    latInput.value = lat;
    lngInput.value = lng;
    if (marker) {
      marker.setLatLng(e.latlng);
    } else {
      marker = L.marker(e.latlng).addTo(map);
    }
  });
});
