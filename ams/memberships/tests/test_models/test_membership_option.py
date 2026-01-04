import pytest
from django.core.exceptions import ValidationError

from ams.memberships.models import MembershipOption
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
        assert option.max_seats == 20  # noqa: PLR2004

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
