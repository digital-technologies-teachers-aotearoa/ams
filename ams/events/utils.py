from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Field
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django.utils.timezone import localdate
from django.utils.timezone import localtime

FILTER_HELPER_RESET_HTML_TEMPLATE = (
    '<a href="{{% url "{}" %}}" class="btn btn-outline-secondary">Reset</a>'
)


class Day:
    def __init__(self, datetime):
        self.date = localdate(datetime)
        self.time_slots = []


class TimeSlot:
    def __init__(self, start_datetime, end_datetime):
        self.start = localtime(start_datetime)
        self.end = localtime(end_datetime)
        self.sessions = []


def organise_schedule_data(sessions):
    """Organise sessions into Day > TimeSlot > Session hierarchy for schedule."""
    schedule_data = []
    for session in sessions:
        session_day = Day(session.start)
        if not schedule_data or session_day.date != schedule_data[-1].date:
            schedule_data.append(session_day)

        session_time_slot = TimeSlot(session.start, session.end)
        previous_time_slot = None
        if schedule_data[-1].time_slots:
            previous_time_slot = schedule_data[-1].time_slots[-1]

        if not previous_time_slot or not (
            session_time_slot.start == previous_time_slot.start
            and session_time_slot.end == previous_time_slot.end
        ):
            session_time_slot.sessions.append(session)
            schedule_data[-1].time_slots.append(session_time_slot)
        else:
            previous_time_slot.sessions.append(session)
    return schedule_data


def create_filter_helper(reset_url_pattern):
    filter_formatter = FormHelper()
    filter_formatter.form_method = "get"
    filter_formatter.layout = Layout(
        Row(
            Column(
                Field(
                    "locations__region",
                    css_class="form-control form-control-sm",
                ),
                css_class="col-sm-12 col-md-4 mb-0",
            ),
            Column(
                Field(
                    "accessible_online",
                    css_class="form-control form-control-sm",
                ),
                css_class="form-group col-sm-12 col-md-4 mb-0",
            ),
            Column(
                Field(
                    "organisers",
                    css_class="form-control form-control-sm",
                ),
                css_class="form-group col-sm-12 col-md-4 mb-0",
            ),
        ),
        Div(
            HTML(FILTER_HELPER_RESET_HTML_TEMPLATE.format(reset_url_pattern)),
            Submit("submit", "Filter events", css_class="btn-success"),
            css_class="d-flex justify-content-between",
        ),
    )
    return filter_formatter
