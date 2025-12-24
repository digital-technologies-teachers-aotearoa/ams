import uuid as uuid_lib
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from imagekit.models import ImageSpecField

from ams.users.models import OrganisationMember
from ams.users.models import User
from ams.users.models import user_profile_picture_path
from ams.users.models import username_validator
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/en/users/{user.username}/"


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


class TestUserProfilePicturePath:
    """Test the user_profile_picture_path function."""

    @patch("ams.users.models.time.time")
    def test_profile_picture_path_format(self, mock_time):
        """Test that the upload path uses the correct format with UUID and timestamp."""
        mock_time.return_value = 1234567890.5

        user = Mock()
        user.uuid = "550e8400-e29b-41d4-a716-446655440000"

        path = user_profile_picture_path(user, "photo.jpg")

        expected_path = (
            "profile_pictures/550e8400-e29b-41d4-a716-446655440000/1234567890.jpg"
        )
        assert path == expected_path

    @patch("ams.users.models.time.time")
    @pytest.mark.parametrize(
        ("filename", "expected_extension"),
        [
            ("photo.png", "png"),
            ("image.jpeg", "jpeg"),
            ("pic.gif", "gif"),
            ("avatar.webp", "webp"),
        ],
    )
    def test_profile_picture_path_with_different_extensions(
        self,
        mock_time,
        filename,
        expected_extension,
    ):
        """Test that different file extensions are preserved."""
        mock_time.return_value = 1234567890

        user = Mock()
        user.uuid = "550e8400-e29b-41d4-a716-446655440000"

        path = user_profile_picture_path(user, filename)

        expected_path = f"profile_pictures/550e8400-e29b-41d4-a716-446655440000/1234567890.{expected_extension}"  # noqa: E501
        assert path == expected_path

    @patch("ams.users.models.time.time")
    def test_profile_picture_path_no_extension(self, mock_time):
        """Test that files without extensions default to .jpg."""
        mock_time.return_value = 1234567890

        user = Mock()
        user.uuid = "550e8400-e29b-41d4-a716-446655440000"

        path = user_profile_picture_path(user, "photo")

        expected_path = (
            "profile_pictures/550e8400-e29b-41d4-a716-446655440000/1234567890.jpg"
        )
        assert path == expected_path

    @patch("ams.users.models.time.time")
    def test_profile_picture_path_uses_timestamp(self, mock_time):
        """Test that the path includes an integer timestamp."""
        mock_time.return_value = 1702888888.99  # Float timestamp

        user = Mock()
        user.uuid = "550e8400-e29b-41d4-a716-446655440000"

        path = user_profile_picture_path(user, "photo.jpg")

        # Ensure timestamp is converted to int
        expected_path = (
            "profile_pictures/550e8400-e29b-41d4-a716-446655440000/1702888888.jpg"
        )
        assert path == expected_path

    def test_profile_picture_path_different_uuids(self):
        """Test that different users get different paths."""
        user1 = Mock()
        user1.uuid = "550e8400-e29b-41d4-a716-446655440000"

        user2 = Mock()
        user2.uuid = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

        path1 = user_profile_picture_path(user1, "photo.jpg")
        path2 = user_profile_picture_path(user2, "photo.jpg")

        # Paths should differ because UUIDs are different
        assert path1 != path2
        assert "550e8400-e29b-41d4-a716-446655440000" in path1
        assert "6ba7b810-9dad-11d1-80b4-00c04fd430c8" in path2


class TestUserProfilePictureField:
    """Test the User model's profile_picture field."""

    @pytest.mark.django_db
    def test_user_profile_picture_is_optional(self):
        """Test that profile_picture is optional (blank=True)."""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
        )
        # Should not raise validation error without profile_picture
        user.full_clean(exclude=["password"])

    @pytest.mark.django_db
    def test_user_profile_picture_upload(self):
        """Test uploading a profile picture to a user."""

        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password="testpass123",  # noqa: S106
        )

        # Create a simple image file
        image_content = b"fake image content"
        image = SimpleUploadedFile(
            "test_profile.jpg",
            image_content,
            content_type="image/jpeg",
        )

        # Mock the storage save method
        with patch.object(storages["default"], "save") as mock_save:
            mock_save.return_value = f"profile_pictures/{user.uuid}/1234567890.jpg"

            user.profile_picture = image
            user.save()

            # Verify the storage save was called
            assert mock_save.called

    @pytest.mark.django_db
    def test_user_profile_picture_uses_public_storage(self):
        """Test that profile_picture uses the default (public) storage."""

        profile_picture_field = User._meta.get_field("profile_picture")  # noqa: SLF001
        # The storage should be a callable that returns the default storage
        storage_instance = (
            profile_picture_field.storage()
            if callable(profile_picture_field.storage)
            else profile_picture_field.storage
        )
        # Verify it's the same as the default storage
        assert storage_instance == storages["default"]

    @pytest.mark.django_db
    def test_profile_picture_thumbnail_field_exists(self):
        """Test that the profile_picture_thumbnail ImageSpecField exists."""

        # Check that the field exists
        assert hasattr(User, "profile_picture_thumbnail")
        # Verify it's an ImageSpecField
        field = User.profile_picture_thumbnail
        assert isinstance(field, ImageSpecField)

    @pytest.mark.django_db
    def test_user_uuid_is_unique(self):
        """Test that each user gets a unique UUID."""
        user1 = User.objects.create_user(
            email="test1@example.com",
            username="testuser1",
            first_name="Test1",
            last_name="User1",
            password="testpass123",  # noqa: S106
        )

        user2 = User.objects.create_user(
            email="test2@example.com",
            username="testuser2",
            first_name="Test2",
            last_name="User2",
            password="testpass123",  # noqa: S106
        )

        assert user1.uuid != user2.uuid
        assert user1.uuid is not None
        assert user2.uuid is not None

    @pytest.mark.django_db
    def test_user_uuid_persists_on_username_change(self):
        """Test that UUID remains the same when username changes."""
        user = User.objects.create_user(
            email="test@example.com",
            username="original_username",
            first_name="Test",
            last_name="User",
            password="testpass123",  # noqa: S106
        )

        original_uuid = user.uuid

        # Change username
        user.username = "new_username"
        user.save()

        # UUID should remain the same
        user.refresh_from_db()
        assert user.uuid == original_uuid


@pytest.mark.django_db
class TestOrganisationMember:
    """Test class for OrganisationMember model."""

    def test_role_can_be_admin(self):
        """Test that role field can be set to ADMIN."""
        member = OrganisationMemberFactory(admin=True)
        assert member.role == OrganisationMember.Role.ADMIN

    def test_is_active_accepted_and_user_active(self):
        """Test is_active returns True for accepted members with active users."""
        member = OrganisationMemberFactory(
            accepted_datetime=timezone.now(),
            user__is_active=True,
        )
        assert member.is_active() is True

    def test_is_active_not_accepted(self):
        """Test is_active returns False for members who haven't accepted."""
        member = OrganisationMemberFactory(accepted_datetime=None)
        assert member.is_active() is False

    def test_is_active_user_inactive(self):
        """Test is_active returns False for accepted members with inactive users."""
        member = OrganisationMemberFactory(
            accepted_datetime=timezone.now(),
            user__is_active=False,
        )
        assert member.is_active() is False

    def test_str_with_user(self):
        """Test string representation with a user shows user's full name."""
        member = OrganisationMemberFactory(
            user__first_name="John",
            user__last_name="Doe",
        )
        assert str(member) == "John Doe"

    def test_str_with_invite_only(self):
        """Test string representation with invite shows email and org name."""
        member = OrganisationMemberFactory(
            user=None,
            invite_email="test@example.com",
            organisation__name="Test Corp",
        )
        result = str(member)
        assert "test@example.com" in result
        assert "Test Corp" in result
        assert "Invite Pending" in result


@pytest.mark.django_db
class TestOrganisation:
    """Test class for Organisation model."""

    def test_uuid_auto_generated(self):
        """Test that UUID is automatically generated on creation."""
        org = OrganisationFactory(name="Test Organisation")
        assert org.uuid is not None
        assert isinstance(org.uuid, uuid_lib.UUID)

    def test_uuid_unique(self):
        """Test that each organisation gets a unique UUID."""
        org1 = OrganisationFactory()
        org2 = OrganisationFactory()
        assert org1.uuid != org2.uuid

    def test_str_returns_name(self):
        """Test that string representation returns organisation name."""
        org = OrganisationFactory(name="Test Company")
        assert str(org) == "Test Company"
