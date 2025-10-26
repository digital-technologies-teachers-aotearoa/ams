import pytest
from django.core.exceptions import ValidationError

from ams.users.models import User
from ams.users.models import username_validator


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.username}/"


class TestUsernameValidator:
    """Test class for username validation rules."""

    @pytest.mark.parametrize(
        "username",
        [
            "user123",
            "john.doe",
            "test_user",
            "user-name",
            "a1b2c3",
            "user",
            "123",
            "user.test_name-123",
        ],
    )
    def test_valid_basic_usernames(self, username):
        """Test that basic valid usernames pass validation."""
        # Should not raise any exception
        username_validator(username)

    @pytest.mark.parametrize(
        "username",
        [
            "māori_user",
            "Kōrero",
            "tāne.wāhine",
            "user_ā",
            "MĀORI_USER",
            "testā",
            "testē",
            "testī",
            "testō",
            "testū",
            "testĀ",
            "testĒ",
            "testĪ",
            "testŌ",
            "testŪ",
            "ā.ē_ī-ō.ū",
            "ĀĒĪŌŪ",
        ],
    )
    def test_valid_macron_usernames(self, username):
        """Test that usernames with macrons pass validation."""
        # Should not raise any exception
        username_validator(username)

    @pytest.mark.parametrize(
        "username",
        [
            "user@name",
            "user name",  # space
            "user#123",
            "user!",
            "user+test",
            "user$money",
            "user%test",
            "user^test",
            "user&test",
            "user*test",
            "user(test)",
            "user[test]",
            "user{test}",
            "user|test",
            "user\\test",
            "user/test",
            "user?test",
            "user<test>",
            "user,test",
            "user;test",
            "user:test",
            'user"test',
            "user'test",
            "user=test",
        ],
    )
    def test_invalid_usernames_with_special_characters(self, username):
        """Test that usernames with invalid special characters fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            username_validator(username)
        assert "Username must only include numbers, letters (including macrons)" in str(
            exc_info.value,
        )

    def test_empty_username(self):
        """Test that empty username fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            username_validator("")
        assert "Username must only include numbers, letters (including macrons)" in str(
            exc_info.value,
        )

    @pytest.mark.parametrize(
        "username",
        [
            "userñ",  # Spanish ñ
            "userç",  # cedilla
            "userß",  # German ß
            "userπ",  # Greek pi
            "user中",  # Chinese character
            "useré",  # acute accent
            "userè",  # grave accent
            "userô",  # circumflex
            "user™",  # trademark symbol
            "user©",  # copyright symbol
        ],
    )
    def test_unicode_characters_other_than_macrons(self, username):
        """Test that other unicode characters (not macrons) fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            username_validator(username)
        assert "Username must only include numbers, letters (including macrons)" in str(
            exc_info.value,
        )

    @pytest.mark.parametrize("char", ["a", "A", "1", "_", "-", ".", "ā", "Ā"])
    def test_boundary_cases_single_chars(self, char):
        """Test single character valid cases."""
        username_validator(char)

    def test_boundary_cases_complex(self):
        """Test mixed case with all allowed character types."""
        # Mixed case with all allowed character types
        complex_valid_username = "Aā1._-zZ9ūŪ"
        username_validator(complex_valid_username)


class TestUserModelUsernameField:
    """Test the User model's username field validation integration."""

    @pytest.mark.django_db
    def test_user_creation_with_valid_username(self):
        """Test creating a user with a valid username including macrons."""
        user = User(
            email="test@example.com",
            username="māori_user",
            first_name="Test",
            last_name="User",
        )
        # Should not raise any validation errors (excluding password field)
        user.full_clean(exclude=["password"])

    @pytest.mark.django_db
    def test_user_creation_with_invalid_username(self):
        """Test that creating a user with invalid username raises ValidationError."""
        user = User(
            email="test@example.com",
            username="user@invalid",
            first_name="Test",
            last_name="User",
        )

        with pytest.raises(ValidationError) as exc_info:
            user.full_clean(exclude=["password"])

        # Check that the error is on the username field
        assert "username" in exc_info.value.error_dict
        username_errors = exc_info.value.error_dict["username"]
        assert any(
            "Username must only include numbers, letters (including macrons)"
            in str(error)
            for error in username_errors
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "username",
        [
            "tāne",
            "wāhine",
            "kōrero",
            "māori",
            "ĀĒĪŌŪ",
            "test.ā_user-123",
        ],
    )
    def test_user_creation_with_macron_usernames(self, username):
        """Test creating users with various macron combinations."""
        user = User(
            email="test@example.com",
            username=username,
            first_name="Test",
            last_name="User",
        )
        # Should not raise any validation errors (excluding password field)
        user.full_clean(exclude=["password"])
