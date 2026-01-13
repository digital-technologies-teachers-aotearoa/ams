from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from ams.memberships.forms import CreateOrganisationMembershipForm
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory
from ams.organisations.tests.factories import OrganisationFactory
from ams.organisations.tests.factories import OrganisationMemberFactory

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
        expected_seats = 5
        assert membership.seats == expected_seats
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

    def test_form_invalid_seat_count_less_than_active_members(self):
        """Test form is invalid when seat count is less than active member count."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create 3 active organisation members
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 2,  # Less than 3 active members
            },
        )

        assert not form.is_valid()
        assert "seat_count" in form.errors
        assert "must be at least 3" in str(form.errors["seat_count"])

    def test_form_valid_seat_count_equals_active_members(self):
        """Test form is valid when seat count equals active member count."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create 3 active organisation members
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 3,  # Exactly 3 seats for 3 members
            },
        )

        assert form.is_valid(), form.errors

    def test_form_valid_seat_count_exceeds_active_members(self):
        """Test form is valid when seat count exceeds active member count."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create 3 active organisation members
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())

        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 5,  # More than 3 active members
            },
        )

        assert form.is_valid(), form.errors

    def test_form_ignores_declined_and_revoked_members_in_count(self):
        """Test form only counts active members, ignoring declined and revoked."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            max_seats=10,
        )

        # Create 2 active members
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())
        OrganisationMemberFactory(organisation=org, accepted_datetime=timezone.now())

        # Create 1 declined member
        OrganisationMemberFactory(
            organisation=org,
            declined_datetime=timezone.now(),
        )

        # Create 1 revoked member
        OrganisationMemberFactory(
            organisation=org,
            revoked_datetime=timezone.now(),
        )

        # Form should require only 2 seats (for 2 active members)
        form = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 2,
            },
        )

        assert form.is_valid(), form.errors

        # Form should be invalid with only 1 seat
        form_invalid = CreateOrganisationMembershipForm(
            organisation=org,
            data={
                "membership_option": option.id,
                "start_date": timezone.localdate(),
                "seat_count": 1,
            },
        )

        assert not form_invalid.is_valid()
        assert "seat_count" in form_invalid.errors

    @override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=True)
    def test_free_membership_requires_approval_when_enabled(self):
        """Test that free org memberships require approval when feature is enabled."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            cost=0,
            max_seats=10,
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

        # Should NOT be auto-approved
        assert membership.approved_datetime is None
        assert membership.status().name == "PENDING"
        assert not membership.invoices.exists()

    @override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=False)
    def test_free_membership_auto_approved_when_disabled(self):
        """Test that free org memberships are auto-approved when feature is disabled."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            cost=0,
            max_seats=10,
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

        # Should be auto-approved (NEW behavior - previously wasn't auto-approved)
        assert membership.approved_datetime is not None
        assert membership.status().name == "ACTIVE"
        assert not membership.invoices.exists()

    @override_settings(REQUIRE_FREE_MEMBERSHIP_APPROVAL=True)
    def test_paid_membership_unchanged_when_approval_required(self):
        """Test that paid org memberships are unaffected by approval setting."""
        org = OrganisationFactory()
        option = MembershipOptionFactory(
            type=MembershipOptionType.ORGANISATION,
            cost=99.99,
            max_seats=10,
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

        # Paid memberships should still not be auto-approved (pending payment)
        assert membership.approved_datetime is None
        assert membership.status().name == "PENDING"

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_form_charges_only_max_charged_seats(self, mock_billing_service_class):
        """Test that form charges only up to max_charged_seats, not all seats."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=4,
        )

        form = CreateOrganisationMembershipForm(
            organisation=organisation,
            data={
                "membership_option": membership_option.id,
                "start_date": timezone.localdate().isoformat(),
                "seat_count": 10,  # Requesting 10 seats
            },
        )

        # Act
        assert form.is_valid(), form.errors
        membership = form.save()

        # Assert
        # Verify invoice was created with only 4 chargeable seats, not 10
        mock_billing_service.create_membership_invoice.assert_called_once()
        call_args = mock_billing_service.create_membership_invoice.call_args
        seats_argument = call_args[0][2]  # 3rd positional arg is seat_count
        expected_seats = 4
        assert seats_argument == expected_seats

        # Verify membership has all 10 seats allocated
        membership.refresh_from_db()
        expected_seats = 10
        assert membership.seats == expected_seats

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_form_charges_all_seats_without_limit(self, mock_billing_service_class):
        """Test that form charges for all seats when no max_charged_seats."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=None,  # No limit
        )

        form = CreateOrganisationMembershipForm(
            organisation=organisation,
            data={
                "membership_option": membership_option.id,
                "start_date": timezone.localdate().isoformat(),
                "seat_count": 10,
            },
        )

        # Act
        assert form.is_valid(), form.errors
        form.save()

        # Assert
        # Verify invoice was created with all 10 seats
        mock_billing_service.create_membership_invoice.assert_called_once()
        call_args = mock_billing_service.create_membership_invoice.call_args
        seats_argument = call_args[0][2]
        expected_seats = 10
        assert seats_argument == expected_seats

    @patch("ams.memberships.forms.MembershipBillingService")
    def test_form_charges_partial_when_below_limit(self, mock_billing_service_class):
        """Test form charges actual seats when below max_charged_seats limit."""
        # Arrange
        mock_billing_service = Mock()
        mock_billing_service.create_membership_invoice.return_value = None
        mock_billing_service_class.return_value = mock_billing_service

        organisation = OrganisationFactory()
        membership_option = MembershipOptionFactory(
            organisation=True,
            cost=Decimal("1000.00"),
            duration={"years": 1},
            max_charged_seats=10,
        )

        form = CreateOrganisationMembershipForm(
            organisation=organisation,
            data={
                "membership_option": membership_option.id,
                "start_date": timezone.localdate().isoformat(),
                "seat_count": 3,  # Below limit
            },
        )

        # Act
        assert form.is_valid(), form.errors
        form.save()

        # Assert
        # Verify invoice was created with 3 seats (actual count)
        call_args = mock_billing_service.create_membership_invoice.call_args
        seats_argument = call_args[0][2]
        expected_seats = 3
        assert seats_argument == expected_seats
