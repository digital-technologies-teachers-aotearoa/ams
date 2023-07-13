from django.contrib.auth.models import User
from django_tables2 import Column, Table, TemplateColumn


class AdminUserTable(Table):
    full_name = Column(accessor="first_name", order_by=("first_name", "last_name"), verbose_name="Full Name")
    email = Column(verbose_name="Email")
    actions = TemplateColumn(verbose_name="Actions", template_name="admin_user_actions.html", orderable=False)

    def render_full_name(self, value: str, record: User) -> str:
        return f"{value} {record.last_name}"

    class Meta:
        fields = ("full_name", "email")
        order_by = ("full_name", "email")
        model = User
