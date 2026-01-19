import csv
from io import StringIO

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from ams.users.admin import ProfileFieldAdmin
from ams.users.admin import ProfileFieldGroupAdmin
from ams.users.admin import UserAdmin
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.users.models import ProfileFieldResponse
from ams.users.models import User
from ams.users.tests.factories import UserFactory


@pytest.fixture
def admin_site():
    """Create AdminSite instance."""
    return AdminSite()


@pytest.fixture
def profile_group():
    """Create a test ProfileFieldGroup."""
    return ProfileFieldGroup.objects.create(
        name_translations={"en": "Test Group"},
        order=1,
        is_active=True,
    )


@pytest.fixture
def profile_field(profile_group):
    """Create a test ProfileField."""
    return ProfileField.objects.create(
        field_key="test_field",
        field_type=ProfileField.FieldType.TEXT,
        label_translations={"en": "Test Field"},
        group=profile_group,
        order=1,
        is_active=True,
    )


@pytest.fixture
def admin_user():
    """Create an admin user."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def request_factory():
    """Create RequestFactory instance."""
    return RequestFactory()


@pytest.mark.django_db
class TestProfileFieldGroupAdmin:
    """Tests for ProfileFieldGroupAdmin."""

    def test_list_display(self, admin_site, profile_group):
        """Test list_display fields are set correctly."""
        admin = ProfileFieldGroupAdmin(ProfileFieldGroup, admin_site)
        assert "__str__" in admin.list_display
        assert "order" in admin.list_display
        assert "active_field_count" in admin.list_display
        assert "is_active" in admin.list_display

    def test_list_editable(self, admin_site):
        """Test list_editable fields are set correctly."""
        admin = ProfileFieldGroupAdmin(ProfileFieldGroup, admin_site)
        assert "order" in admin.list_editable
        assert "is_active" in admin.list_editable

    def test_active_field_count_method(self, admin_site, profile_group, profile_field):
        """Test active_field_count returns correct count."""
        admin = ProfileFieldGroupAdmin(ProfileFieldGroup, admin_site)

        # Should have 1 active field
        count = admin.active_field_count(profile_group)
        assert count == 1

        # Add inactive field
        ProfileField.objects.create(
            field_key="inactive",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive"},
            group=profile_group,
            is_active=False,
        )

        # Count should still be 1
        count = admin.active_field_count(profile_group)
        assert count == 1


@pytest.mark.django_db
class TestProfileFieldAdmin:
    """Tests for ProfileFieldAdmin."""

    def test_list_display(self, admin_site):
        """Test list_display fields are set correctly."""
        admin = ProfileFieldAdmin(ProfileField, admin_site)
        assert "field_key" in admin.list_display
        assert "__str__" in admin.list_display
        assert "field_type" in admin.list_display
        assert "group" in admin.list_display
        assert "is_read_only" in admin.list_display
        assert "order" in admin.list_display
        assert "is_active" in admin.list_display

    def test_list_filter(self, admin_site):
        """Test list_filter fields are set correctly."""
        admin = ProfileFieldAdmin(ProfileField, admin_site)
        assert "field_type" in admin.list_filter
        assert "group" in admin.list_filter
        assert "is_read_only" in admin.list_filter
        assert "is_active" in admin.list_filter

    def test_list_editable(self, admin_site):
        """Test list_editable fields are set correctly."""
        admin = ProfileFieldAdmin(ProfileField, admin_site)
        assert "order" in admin.list_editable
        assert "is_active" in admin.list_editable

    def test_field_key_readonly_after_creation(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test field_key is readonly after object creation."""
        admin = ProfileFieldAdmin(ProfileField, admin_site)
        request = request_factory.get("/")
        request.user = admin_user

        # For existing object, field_key should be readonly
        readonly_fields = admin.get_readonly_fields(request, obj=profile_field)
        assert "field_key" in readonly_fields

    def test_field_key_editable_on_creation(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test field_key is editable when creating new object."""
        admin = ProfileFieldAdmin(ProfileField, admin_site)
        request = request_factory.get("/")
        request.user = admin_user

        # For new object (obj=None), field_key should not be readonly
        readonly_fields = admin.get_readonly_fields(request, obj=None)
        assert "field_key" not in readonly_fields


@pytest.mark.django_db
class TestUserAdmin:
    """Tests for UserAdmin with profile field extensions."""

    def test_has_export_action(self, admin_site):
        """Test UserAdmin has export_profile_responses_csv action."""
        admin = UserAdmin(User, admin_site)
        assert "export_profile_responses_csv" in admin.actions

    def test_export_profile_responses_csv_basic(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test export_profile_responses_csv creates CSV."""
        admin = UserAdmin(User, admin_site)

        # Create users with responses
        user1 = UserFactory(
            email="user1@example.com",
            first_name="John",
            last_name="Doe",
        )
        user2 = UserFactory(
            email="user2@example.com",
            first_name="Jane",
            last_name="Smith",
        )

        ProfileFieldResponse.objects.create(
            user=user1,
            profile_field=profile_field,
            value="Response 1",
        )
        ProfileFieldResponse.objects.create(
            user=user2,
            profile_field=profile_field,
            value="Response 2",
        )

        # Create request
        request = request_factory.get("/")
        request.user = admin_user

        # Export
        queryset = User.objects.filter(pk__in=[user1.pk, user2.pk])
        response = admin.export_profile_responses_csv(request, queryset)

        # Check response type
        assert response["Content-Type"] == "text/csv"
        assert "attachment" in response["Content-Disposition"]

        # Parse CSV
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        # Check header
        assert rows[0] == ["Email", "First Name", "Last Name", "test_field"]

        # Check data rows
        expected_rows = 3  # Header + 2 users
        assert len(rows) == expected_rows

        # Find user1 row
        user1_row = next(row for row in rows if row[0] == "user1@example.com")
        assert user1_row[1] == "John"
        assert user1_row[2] == "Doe"
        assert user1_row[3] == "Response 1"

        # Find user2 row
        user2_row = next(row for row in rows if row[0] == "user2@example.com")
        assert user2_row[1] == "Jane"
        assert user2_row[2] == "Smith"
        assert user2_row[3] == "Response 2"

    def test_export_handles_missing_responses(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test export handles users without responses."""
        admin = UserAdmin(User, admin_site)

        # Create user without response
        user = UserFactory(email="user@example.com")

        # Create request
        request = request_factory.get("/")
        request.user = admin_user

        # Export
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_profile_responses_csv(request, queryset)

        # Parse CSV
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        # Check data row has empty value for missing response
        assert rows[1][3] == ""

    def test_export_handles_checkbox_lists(
        self,
        admin_site,
        profile_group,
        request_factory,
        admin_user,
    ):
        """Test export converts checkbox lists to comma-separated strings."""
        admin = UserAdmin(User, admin_site)

        # Create checkbox field
        checkbox_field = ProfileField.objects.create(
            field_key="subjects",
            field_type=ProfileField.FieldType.CHECKBOX,
            label_translations={"en": "Subjects"},
            options={
                "choices": [
                    {"value": "math", "label_translations": {"en": "Math"}},
                    {"value": "science", "label_translations": {"en": "Science"}},
                ],
            },
            group=profile_group,
        )

        # Create user with checkbox response
        user = UserFactory()
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=checkbox_field,
        )
        response.set_value(["math", "science"])
        response.save()

        # Create request
        request = request_factory.get("/")
        request.user = admin_user

        # Export
        queryset = User.objects.filter(pk=user.pk)
        response_obj = admin.export_profile_responses_csv(request, queryset)

        # Parse CSV
        content = response_obj.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        # Check checkbox values are comma-separated
        assert rows[1][3] == "math, science"

    def test_export_only_includes_active_fields(
        self,
        admin_site,
        profile_group,
        request_factory,
        admin_user,
    ):
        """Test export only includes active fields in columns."""
        admin = UserAdmin(User, admin_site)

        # Create active field
        ProfileField.objects.create(
            field_key="active",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Active"},
            group=profile_group,
            is_active=True,
        )

        # Create inactive field
        ProfileField.objects.create(
            field_key="inactive",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive"},
            group=profile_group,
            is_active=False,
        )

        # Create user
        user = UserFactory()

        # Create request
        request = request_factory.get("/")
        request.user = admin_user

        # Export
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_profile_responses_csv(request, queryset)

        # Parse CSV
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        # Check header only includes active field
        assert "active" in rows[0]
        assert "inactive" not in rows[0]

    def test_export_filename_format(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test export filename has correct format."""
        admin = UserAdmin(User, admin_site)

        # Create request
        request = request_factory.get("/")
        request.user = admin_user

        # Export
        queryset = User.objects.none()
        response = admin.export_profile_responses_csv(request, queryset)

        # Check filename format
        assert "profile_responses_" in response["Content-Disposition"]
        assert ".csv" in response["Content-Disposition"]
