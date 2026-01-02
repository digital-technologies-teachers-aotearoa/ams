from datetime import timedelta

import pytest
from django.utils import timezone

from ams.memberships.forms import CreateOrganisationMembershipForm
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestCreateOrganisationMembershipForm:
    """Tests for the CreateOrganisationMembershipForm."""

    def test_form_valid_with_organisation_option(self):
        """Test form is valid with organisation membership option and seat count."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=100,
        )

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 5,
            },
        )

        assert form.is_valid(), form.errors

    def test_form_invalid_seat_count_exceeds_max(self):
        """Test form is invalid when seat count exceeds max_seats."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 15,  # Exceeds max_seats
            },
        )

        assert not form.is_valid()
        assert "seat_count" in form.errors
        assert "cannot exceed the maximum seats" in str(form.errors["seat_count"])

    def test_form_valid_seat_count_without_max_seats(self):
        """Test form is valid when option has no max_seats limit."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=None,  # No limit
        )

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 100,  # Any number is OK
            },
        )

        assert form.is_valid(), form.errors

    def test_form_invalid_overlapping_membership(self):
        """Test form is invalid when start_date overlaps with existing membership."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create existing membership
        start_date = timezone.localdate()
        expiry_date = start_date + timedelta(days=365)
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=option,
            start_date=start_date,
            expiry_date=expiry_date,
            cancelled_datetime=None,
        )

        # Try to create overlapping membership
        overlap_date = start_date + timedelta(days=100)
        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": overlap_date,
                "seat_count": 5,
            },
        )

        assert not form.is_valid()
        assert "start_date" in form.errors
        assert "overlaps" in str(form.errors["start_date"])

    def test_form_valid_after_existing_membership_expires(self):
        """Test form is valid when start_date is after existing membership expires."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create existing membership
        start_date = timezone.localdate()
        expiry_date = start_date + timedelta(days=365)
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=option,
            start_date=start_date,
            expiry_date=expiry_date,
            cancelled_datetime=None,
        )

        # Create new membership after expiry
        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": expiry_date,  # Starts when current expires
                "seat_count": 5,
            },
        )

        assert form.is_valid(), form.errors

    def test_form_valid_when_existing_membership_cancelled(self):
        """Test form is valid when overlapping membership is cancelled."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create cancelled membership
        start_date = timezone.localdate()
        expiry_date = start_date + timedelta(days=365)
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=option,
            start_date=start_date,
            expiry_date=expiry_date,
            cancelled_datetime=timezone.now(),  # Cancelled
        )

        # Try to create membership on same date (should be OK since prev is cancelled)
        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": start_date,
                "seat_count": 5,
            },
        )

        assert form.is_valid(), form.errors

    def test_form_default_start_date_no_existing_membership(self):
        """Test form defaults start_date to today when no existing membership."""
        org = OrganisationFactory()

        form = CreateOrganisationMembershipForm(organisation=org)

        assert form.fields["start_date"].initial == timezone.localdate()

    def test_form_default_start_date_with_existing_membership(self):
        """Test form defaults start_date to latest expiry when membership exists."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create existing membership
        start_date = timezone.localdate()
        expiry_date = start_date + timedelta(days=365)
        OrganisationMembershipFactory(
            organisation=org,
            membership_option=option,
            start_date=start_date,
            expiry_date=expiry_date,
            cancelled_datetime=None,
        )

        form = CreateOrganisationMembershipForm(organisation=org)

        assert form.fields["start_date"].initial == expiry_date

    def test_form_save_creates_membership_with_correct_values(self):
        """Test saving form creates membership with correct values."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
            cost=0,  # Use zero cost to avoid billing setup
        )

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 5,
            },
        )

        assert form.is_valid()
        membership = form.save()

        assert membership.organisation == org
        assert membership.membership_option == option
        assert membership.start_date == timezone.localdate()
        assert membership.max_seats == 5  # noqa: PLR2004
        assert membership.expiry_date == membership.calculate_expiry_date()
        assert membership.created_datetime is not None

    def test_form_requires_organisation_parameter(self):
        """Test form raises error when organisation is not provided."""
        with pytest.raises(ValueError, match="organisation is required"):
            CreateOrganisationMembershipForm(organisation=None)

    def test_form_requires_organisation_instance(self):
        """Test form raises error when organisation is not an Organisation instance."""
        with pytest.raises(TypeError, match="must be an instance of Organisation"):
            CreateOrganisationMembershipForm(organisation="not an organisation")
