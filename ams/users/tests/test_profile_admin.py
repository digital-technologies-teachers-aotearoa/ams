import csv
import datetime
from io import StringIO

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.utils import timezone

from ams.memberships.models import MembershipStatus
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory
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


def _parse_streaming_csv(response):
    """Parse a StreamingHttpResponse containing CSV data into rows."""
    content = b"".join(response.streaming_content).decode("utf-8")
    return list(csv.reader(StringIO(content)))


@pytest.mark.django_db
class TestExportUsersCsv:
    """Tests for the export_users_csv admin action."""

    def test_has_export_users_action(self, admin_site):
        admin = UserAdmin(User, admin_site)
        assert "export_users_csv" in admin.actions

    def test_streaming_response_content_type(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        admin = UserAdmin(User, admin_site)
        request = request_factory.get("/")
        request.user = admin_user
        response = admin.export_users_csv(request, User.objects.none())
        assert response["Content-Type"] == "text/csv"

    def test_filename_format(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        admin = UserAdmin(User, admin_site)
        request = request_factory.get("/")
        request.user = admin_user
        response = admin.export_users_csv(request, User.objects.none())
        assert "users_export_" in response["Content-Disposition"]
        assert ".csv" in response["Content-Disposition"]

    def test_export_basic_with_all_data(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test export with a user that has profile, membership, and org data."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory(
            email="full@example.com",
            first_name="Full",
            last_name="User",
            username="fulluser",
        )

        # Profile response
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=profile_field,
            value="My Response",
        )

        # Individual membership (active, approved)
        option = MembershipOptionFactory(name="Gold Plan")
        IndividualMembershipFactory(
            user=user,
            membership_option=option,
            approved=True,
        )

        # Organisation membership
        org = OrganisationFactory(name="Test Corp")
        OrganisationMemberFactory(
            user=user,
            organisation=org,
            accepted=True,
            role="ADMIN",
        )
        OrganisationMembershipFactory(
            organisation=org,
            approved=True,
        )

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        # Check header has all sections
        header = rows[0]
        assert "Email" in header
        assert "Active Member" in header
        assert "test_field" in header
        assert "Individual Membership Status" in header
        assert "Organisation Name" in header

        # Check data row
        data_row = rows[1]
        email_idx = header.index("Email")
        assert data_row[email_idx] == "full@example.com"

        first_name_idx = header.index("First Name")
        assert data_row[first_name_idx] == "Full"

        active_member_idx = header.index("Active Member")
        assert data_row[active_member_idx] == "True"

        profile_idx = header.index("test_field")
        assert data_row[profile_idx] == "My Response"

        status_idx = header.index("Individual Membership Status")
        assert data_row[status_idx] == MembershipStatus.ACTIVE

        option_idx = header.index("Membership Option")
        assert data_row[option_idx] == "Gold Plan"

        org_name_idx = header.index("Organisation Name")
        assert data_row[org_name_idx] == "Test Corp"

        org_role_idx = header.index("Organisation Role")
        assert data_row[org_role_idx] == "Admin"

    def test_export_user_no_memberships_no_org(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test export for user with no memberships or org."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory(email="bare@example.com")

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        status_idx = header.index("Individual Membership Status")
        assert data_row[status_idx] == MembershipStatus.NONE

        option_idx = header.index("Membership Option")
        assert data_row[option_idx] == ""

        org_name_idx = header.index("Organisation Name")
        assert data_row[org_name_idx] == ""

    def test_export_multiple_memberships_picks_most_recent(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test that the most recent membership is used when user has multiple."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory(email="multi@example.com")

        old_option = MembershipOptionFactory(name="Old Plan")
        new_option = MembershipOptionFactory(name="New Plan")

        # Older membership
        IndividualMembershipFactory(
            user=user,
            membership_option=old_option,
            approved=True,
            created_datetime=timezone.now() - timezone.timedelta(days=365),
        )
        # Newer membership
        IndividualMembershipFactory(
            user=user,
            membership_option=new_option,
            approved=True,
        )

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        option_idx = header.index("Membership Option")
        assert data_row[option_idx] == "New Plan"

    def test_export_checkbox_profile_field(
        self,
        admin_site,
        profile_group,
        request_factory,
        admin_user,
    ):
        """Test checkbox profile fields render as comma-separated strings."""
        admin = UserAdmin(User, admin_site)

        checkbox_field = ProfileField.objects.create(
            field_key="interests",
            field_type=ProfileField.FieldType.CHECKBOX,
            label_translations={"en": "Interests"},
            options={
                "choices": [
                    {"value": "art", "label_translations": {"en": "Art"}},
                    {"value": "music", "label_translations": {"en": "Music"}},
                ],
            },
            group=profile_group,
        )

        user = UserFactory()
        resp = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=checkbox_field,
        )
        resp.set_value(["art", "music"])
        resp.save()

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        interests_idx = header.index("interests")
        assert data_row[interests_idx] == "art, music"

    def test_export_only_includes_active_fields(
        self,
        admin_site,
        profile_group,
        request_factory,
        admin_user,
    ):
        """Test export only includes active profile fields in columns."""
        admin = UserAdmin(User, admin_site)

        ProfileField.objects.create(
            field_key="active_field",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Active"},
            group=profile_group,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="inactive_field",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive"},
            group=profile_group,
            is_active=False,
        )

        user = UserFactory()

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        assert "active_field" in header
        assert "inactive_field" not in header

    def test_export_user_no_profile_responses(
        self,
        admin_site,
        profile_field,
        request_factory,
        admin_user,
    ):
        """Test export for user with no profile responses shows empty columns."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory()

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        profile_idx = header.index("test_field")
        assert data_row[profile_idx] == ""

    def test_export_user_with_null_last_login(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test export for user who has never logged in shows empty Last Login."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory(last_login=None)

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        last_login_idx = header.index("Last Login")
        assert data_row[last_login_idx] == ""

    def test_export_individual_membership_expired_status(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test export shows EXPIRED for membership with past expiry date."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory()
        IndividualMembershipFactory(user=user, approved=True, expired=True)

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        status_idx = header.index("Individual Membership Status")
        assert data_row[status_idx] == MembershipStatus.EXPIRED

    def test_export_individual_membership_cancelled_status(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test export shows CANCELLED for membership with cancelled_datetime set."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory()
        IndividualMembershipFactory(user=user, approved=True, cancelled=True)

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        status_idx = header.index("Individual Membership Status")
        assert data_row[status_idx] == MembershipStatus.CANCELLED

    def test_export_organisation_with_no_active_membership(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test org member whose organisation has no active membership."""
        admin = UserAdmin(User, admin_site)

        user = UserFactory()
        org = OrganisationFactory(name="Expired Corp")
        OrganisationMemberFactory(
            user=user,
            organisation=org,
            accepted=True,
            role="ADMIN",
        )
        # Create an expired org membership so get_active_membership() returns None
        OrganisationMembershipFactory(
            organisation=org,
            approved=True,
            expired=True,
        )

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        org_name_idx = header.index("Organisation Name")
        assert data_row[org_name_idx] == "Expired Corp"

        org_role_idx = header.index("Organisation Role")
        assert data_row[org_role_idx] == "Admin"

        org_status_idx = header.index("Organisation Membership Status")
        assert data_row[org_status_idx] == MembershipStatus.NONE

    def test_export_csv_special_characters(
        self,
        admin_site,
        profile_group,
        request_factory,
        admin_user,
    ):
        """Test CSV properly escapes special characters in field values."""
        admin = UserAdmin(User, admin_site)

        special_field = ProfileField.objects.create(
            field_key="bio",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Bio"},
            group=profile_group,
            order=1,
            is_active=True,
        )

        user = UserFactory(first_name='Jane "the great"', last_name="O'Brien")
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=special_field,
            value='Hello, "world"\ntest',
        )

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        first_name_idx = header.index("First Name")
        assert data_row[first_name_idx] == 'Jane "the great"'

        bio_idx = header.index("bio")
        assert data_row[bio_idx] == 'Hello, "world"\ntest'

    def test_export_multiple_users(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test export with multiple users produces correct rows."""
        admin = UserAdmin(User, admin_site)

        user1 = UserFactory(email="alice@example.com", first_name="Alice")
        user2 = UserFactory(email="bob@example.com", first_name="Bob")
        user3 = UserFactory(email="carol@example.com", first_name="Carol")

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk__in=[user1.pk, user2.pk, user3.pk])
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        # 1 header + 3 data rows
        expected_rows = 4
        assert len(rows) == expected_rows

        header = rows[0]
        email_idx = header.index("Email")
        emails = {rows[i][email_idx] for i in range(1, 4)}
        assert emails == {"alice@example.com", "bob@example.com", "carol@example.com"}

    def test_export_date_format(
        self,
        admin_site,
        request_factory,
        admin_user,
    ):
        """Test date_joined and last_login use expected format."""
        admin = UserAdmin(User, admin_site)

        known_date = datetime.datetime(2025, 3, 15, 10, 30, 45, tzinfo=datetime.UTC)
        user = UserFactory(date_joined=known_date, last_login=known_date)

        request = request_factory.get("/")
        request.user = admin_user
        queryset = User.objects.filter(pk=user.pk)
        response = admin.export_users_csv(request, queryset)
        rows = _parse_streaming_csv(response)

        header = rows[0]
        data_row = rows[1]

        date_joined_idx = header.index("Date Joined")
        assert data_row[date_joined_idx] == "2025-03-15 10:30:45"

        last_login_idx = header.index("Last Login")
        assert data_row[last_login_idx] == "2025-03-15 10:30:45"
