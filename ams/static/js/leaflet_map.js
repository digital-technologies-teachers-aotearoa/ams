(function () {
  var markersEl = document.getElementById('event-markers-data');
  var zoomEl = document.getElementById('map-zoom-data');
  var markers = markersEl ? JSON.parse(markersEl.textContent) : [];
  var mapZoom = zoomEl ? JSON.parse(zoomEl.textContent) : 5;
  var mapId = document.querySelector('[data-leaflet-map]');
  if (!mapId) return;
  var mapIdStr = mapId.id;

  var map = L.map(mapIdStr).setView([-41.2865, 174.7762], mapZoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin',
  }).addTo(map);

  if (markers.length === 0) return;

  var markerCluster = L.markerClusterGroup();
  var bounds = L.latLngBounds();

  markers.forEach(function (m) {
    var latlng = L.latLng(m.coords.lat, m.coords.lng);
    var popupContent = '<strong>' + m.title + '</strong>';
    if (m.events) {
      m.events.forEach(function (evt) {
        popupContent +=
          '<p class="mb-0"><a href="' +
          evt.url +
          '">' +
          evt.date +
          ' - ' +
          evt.name +
          '</a></p>';
      });
    } else if (m.text) {
      popupContent += m.text;
    }
    var marker = L.marker(latlng).bindPopup(popupContent);
    markerCluster.addLayer(marker);
    bounds.extend(latlng);
  });

  map.addLayer(markerCluster);

  if (markers.length === 1) {
    map.setView(bounds.getCenter(), mapZoom);
  } else {
    map.fitBounds(bounds, {
      padding: [30, 30],
    });
  }
})();
