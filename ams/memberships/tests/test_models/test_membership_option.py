from decimal import Decimal

import pytest
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError

from ams.memberships.models import MembershipOption
from ams.memberships.models import MembershipOptionType
from ams.memberships.tests.factories import IndividualMembershipFactory
from ams.memberships.tests.factories import MembershipOptionFactory
from ams.memberships.tests.factories import OrganisationMembershipFactory

pytestmark = pytest.mark.django_db


class TestMembershipOption:
    def test_str(self):
        # Arrange
        option = MembershipOptionFactory(
            name="Gold",
            individual=True,
            duration={"months": 1},
            cost=49.99,
        )
        # Act
        result_str = str(option)
        # Assert
        assert "Gold" in result_str
        assert "Individual" in result_str
        assert "1 month" in result_str
        assert "$49.99" in result_str

    def test_max_seats_optional(self):
        # Arrange & Act
        option = MembershipOptionFactory(
            individual=True,
            max_seats=None,
        )
        # Assert
        assert option.max_seats is None

    def test_max_seats_with_value(self):
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=20,
        )
        # Assert
        expected_seats = 20
        assert option.max_seats == expected_seats

    def test_archived_defaults_false(self):
        # Arrange & Act
        option = MembershipOptionFactory()
        # Assert
        assert option.archived is False

    def test_archived_can_be_set_true(self):
        # Arrange & Act
        option = MembershipOptionFactory(archived=True)
        # Assert
        assert option.archived is True

    def test_delete_with_no_memberships_succeeds(self):
        # Arrange
        option = MembershipOptionFactory()
        option_id = option.id
        # Act
        option.delete()
        # Assert

        assert not MembershipOption.objects.filter(id=option_id).exists()

    def test_delete_with_individual_memberships_raises(self):
        # Arrange
        option = MembershipOptionFactory(individual=True)
        IndividualMembershipFactory(membership_option=option)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option.delete()
        assert "Cannot delete membership option with existing memberships" in str(
            exc.value,
        )
        assert "Archive it instead" in str(exc.value)

    def test_delete_with_organisation_memberships_raises(self):
        # Arrange
        option = MembershipOptionFactory(organisation=True)
        OrganisationMembershipFactory(membership_option=option)
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option.delete()
        assert "Cannot delete membership option with existing memberships" in str(
            exc.value,
        )
        assert "Archive it instead" in str(exc.value)

    def test_invoice_due_days_defaults_to_60(self):
        """Test that invoice_due_days defaults to 60 days."""
        # Arrange & Act
        option = MembershipOptionFactory()
        # Assert
        expected_days = 60
        assert option.invoice_due_days == expected_days

    def test_invoice_due_days_can_be_customized(self):
        """Test that invoice_due_days can be set to custom value."""
        # Arrange & Act
        option = MembershipOptionFactory(invoice_due_days=30)
        # Assert
        expected_days = 30
        assert option.invoice_due_days == expected_days

    def test_invoice_due_days_is_not_immutable(self):
        """Test that invoice_due_days can be changed after creation."""
        # Arrange
        option = MembershipOptionFactory(invoice_due_days=60)
        # Act - change the value
        option.invoice_due_days = 90
        option.save()
        option.refresh_from_db()
        # Assert
        expected_days = 90
        assert option.invoice_due_days == expected_days

    def test_unique_name_type_constraint_on_create(self):
        """Test that creating duplicate name+type raises ValidationError."""
        # Arrange
        MembershipOptionFactory(
            name="Duplicate Test",
            type=MembershipOptionType.INDIVIDUAL,
        )

        # Act & Assert
        duplicate = MembershipOption(
            name="Duplicate Test",
            type=MembershipOptionType.INDIVIDUAL,
            duration=relativedelta(years=1),
            cost=Decimal("100.00"),
        )
        with pytest.raises(ValidationError) as exc:
            duplicate.full_clean()

        # Verify the error is about uniqueness
        assert "__all__" in exc.value.error_dict or "name" in exc.value.error_dict

    def test_unique_name_type_constraint_on_update(self):
        """Test that updating to duplicate name+type raises ValidationError."""
        # Arrange
        MembershipOptionFactory(
            name="Original",
            type=MembershipOptionType.INDIVIDUAL,
        )
        option_to_update = MembershipOptionFactory(
            name="Different",
            type=MembershipOptionType.INDIVIDUAL,
        )

        # Act - Try to change name to create duplicate
        option_to_update.name = "Original"

        # Assert
        with pytest.raises(ValidationError) as exc:
            option_to_update.full_clean()

        assert "__all__" in exc.value.error_dict or "name" in exc.value.error_dict

    def test_same_name_different_type_allowed(self):
        """Test that same name with different type is allowed."""
        # Arrange
        MembershipOptionFactory(
            name="Gold",
            type=MembershipOptionType.INDIVIDUAL,
        )

        # Act & Assert - should not raise
        option = MembershipOption(
            name="Gold",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=Decimal("100.00"),
        )
        option.full_clean()  # Should pass validation
        option.save()  # Should save successfully


class TestMembershipOptionMaxChargedSeats:
    """Tests for max_charged_seats field on MembershipOption."""

    def test_max_charged_seats_can_be_null(self):
        """Test that max_charged_seats can be null (optional field)."""
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_charged_seats=None,
        )
        # Assert
        assert option.max_charged_seats is None

    def test_max_charged_seats_with_valid_value(self):
        """Test setting a valid max_charged_seats value."""
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=10,
            max_charged_seats=5,
        )
        # Assert
        expected_seats = 5
        assert option.max_charged_seats == expected_seats

    def test_max_charged_seats_cannot_exceed_max_seats(self):
        """Test validation prevents max_charged_seats > max_seats."""
        # Arrange - Create a membership option with invalid max_charged_seats
        option_invalid = MembershipOption(
            name="Test Option",
            type=MembershipOptionType.ORGANISATION,
            duration=relativedelta(years=1),
            cost=Decimal("1000.00"),
            max_seats=5,
            max_charged_seats=10,  # Invalid: greater than max_seats
        )
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option_invalid.full_clean()
        assert "max_charged_seats" in exc.value.error_dict
        assert "cannot exceed max seats" in str(exc.value).lower()

    def test_max_charged_seats_only_for_organisation_type(self):
        """Test validation prevents max_charged_seats on INDIVIDUAL memberships."""
        # Arrange
        option = MembershipOption(
            name="Individual Test",
            type=MembershipOptionType.INDIVIDUAL,
            duration=relativedelta(years=1),
            cost=Decimal("100.00"),
            max_charged_seats=5,  # Invalid for individual
        )
        # Act & Assert
        with pytest.raises(ValidationError) as exc:
            option.full_clean()
        assert "max_charged_seats" in exc.value.error_dict
        assert "only applies to organisation" in str(exc.value).lower()

    def test_max_charged_seats_is_immutable_after_creation(self):
        """Test that max_charged_seats cannot be changed after creation."""
        # Arrange - Create option with max_charged_seats
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=10,
            max_charged_seats=5,
        )
        # Act - Try to change it
        option.max_charged_seats = 7
        # Assert
        with pytest.raises(ValidationError) as exc:
            option.full_clean()
        assert "max_charged_seats" in exc.value.error_dict
        assert "cannot be changed" in str(exc.value).lower()

    def test_max_charged_seats_without_max_seats(self):
        """Test that max_charged_seats can be set even without max_seats."""
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=None,  # No overall limit
            max_charged_seats=10,  # But limit on charged seats
        )
        # Assert
        expected_charged_seats = 10
        assert option.max_seats is None
        assert option.max_charged_seats == expected_charged_seats

    def test_max_charged_seats_equal_to_max_seats(self):
        """Test that max_charged_seats can equal max_seats (edge case)."""
        # Arrange & Act
        option = MembershipOptionFactory(
            organisation=True,
            max_seats=10,
            max_charged_seats=10,
        )
        # Assert
        assert option.max_charged_seats == option.max_seats
