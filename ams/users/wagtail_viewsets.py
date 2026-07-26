from wagtail.users.views.users import UserViewSet as WagtailUserViewSet

from ams.users.forms import WagtailUserCreationForm
from ams.users.forms import WagtailUserEditForm


class UserViewSet(WagtailUserViewSet):
    """Swaps in AMS's user create/edit forms so the CMS Users admin
    collects the separate `username` field. See
    ams.users.forms.WagtailUserCreationForm for why this is needed.
    """

    def get_form_class(self, for_update=False):  # noqa: FBT002
        if for_update:
            return WagtailUserEditForm
        return WagtailUserCreationForm
