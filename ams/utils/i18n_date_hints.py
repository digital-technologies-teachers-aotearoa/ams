from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

# This file exists so that makemessages extracts month and weekday name
# translations into our catalog. Django renders these names in the |date:
# template filter by calling gettext/pgettext against its own source file
# (django.utils.dates), which is not scanned by makemessages. Declaring
# the same calls here causes makemessages to include them in every language
# catalog automatically, so no manual .po maintenance is needed.
#
# Format code → dict used:
#   F  → MONTHS       (full month names, plain gettext)
#   M  → MONTHS_3     (3-letter lowercase, plain gettext, .title() applied on output)
#   N  → MONTHS_AP    (AP-style, pgettext "abbrev. month")
#   E  → MONTHS_ALT   (alt. nominative form, pgettext "alt. month")
#   l  → WEEKDAYS     (full weekday names, plain gettext)
#   D  → WEEKDAYS_ABBR (3-letter weekday, plain gettext)

_month_names = [
    _("January"),
    _("February"),
    _("March"),
    _("April"),
    _("May"),
    _("June"),
    _("July"),
    _("August"),
    _("September"),
    _("October"),
    _("November"),
    _("December"),
]

_month_abbr = [
    _("jan"),
    _("feb"),
    _("mar"),
    _("apr"),
    _("may"),
    _("jun"),
    _("jul"),
    _("aug"),
    _("sep"),
    _("oct"),
    _("nov"),
    _("dec"),
]

_month_ap = [
    pgettext_lazy("abbrev. month", "Jan."),
    pgettext_lazy("abbrev. month", "Feb."),
    pgettext_lazy("abbrev. month", "March"),
    pgettext_lazy("abbrev. month", "April"),
    pgettext_lazy("abbrev. month", "May"),
    pgettext_lazy("abbrev. month", "June"),
    pgettext_lazy("abbrev. month", "July"),
    pgettext_lazy("abbrev. month", "Aug."),
    pgettext_lazy("abbrev. month", "Sept."),
    pgettext_lazy("abbrev. month", "Oct."),
    pgettext_lazy("abbrev. month", "Nov."),
    pgettext_lazy("abbrev. month", "Dec."),
]

_month_alt = [
    pgettext_lazy("alt. month", "January"),
    pgettext_lazy("alt. month", "February"),
    pgettext_lazy("alt. month", "March"),
    pgettext_lazy("alt. month", "April"),
    pgettext_lazy("alt. month", "May"),
    pgettext_lazy("alt. month", "June"),
    pgettext_lazy("alt. month", "July"),
    pgettext_lazy("alt. month", "August"),
    pgettext_lazy("alt. month", "September"),
    pgettext_lazy("alt. month", "October"),
    pgettext_lazy("alt. month", "November"),
    pgettext_lazy("alt. month", "December"),
]

_weekday_names = [
    _("Monday"),
    _("Tuesday"),
    _("Wednesday"),
    _("Thursday"),
    _("Friday"),
    _("Saturday"),
    _("Sunday"),
]

_weekday_abbr = [
    _("Mon"),
    _("Tue"),
    _("Wed"),
    _("Thu"),
    _("Fri"),
    _("Sat"),
    _("Sun"),
]
