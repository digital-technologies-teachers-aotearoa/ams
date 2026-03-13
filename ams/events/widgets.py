from django.forms import MultiWidget
from django.forms import NumberInput


class LeafletPickerWidget(MultiWidget):
    """Admin widget that renders a Leaflet map for picking lat/lng coordinates."""

    template_name = "events/widgets/leaflet_picker.html"

    def __init__(self, attrs=None):
        widgets = [
            NumberInput(attrs={"step": "0.000001", "placeholder": "Latitude"}),
            NumberInput(attrs={"step": "0.000001", "placeholder": "Longitude"}),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value[0], value[1]]
        return [None, None]

    class Media:
        css = {"all": ("css/leaflet.min.css",)}
        js = ("js/leaflet_vendors.min.js",)
