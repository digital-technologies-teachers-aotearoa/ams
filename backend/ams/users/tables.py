from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django_tables2 import Column, Table, TemplateColumn


class AdminUserTable(Table):
    full_name = Column(accessor="first_name", order_by=("first_name", "last_name"), verbose_name=_("Full Name"))
    email = Column(verbose_name=_("Email"))
    actions = TemplateColumn(verbose_name=_("Actions"), template_name="admin_user_actions.html", orderable=False)

    def render_full_name(self, value: str, record: User) -> str:
        full_name: str = record.get_full_name()
        return full_name

    class Meta:
        fields = ("full_name", "email")
        order_by = ("full_name", "email")
        model = User
