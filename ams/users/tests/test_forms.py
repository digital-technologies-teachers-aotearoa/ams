"""Module for all Form Tests."""

from io import BytesIO
from unittest.mock import Mock

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image

from ams.users.forms import UserAdminCreationForm
from ams.users.forms import UserSignupForm
from ams.users.forms import UserUpdateForm
from ams.users.models import User


class TestUserAdminCreationForm:
    """
    Test class for all tests related to the UserAdminCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserAdminCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "email": user.email,
                "password1": user.password,
                "password2": user.password,
            },
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "email" in form.errors
        assert form.errors["email"][0] == _("This email has already been taken.")


class TestUserSignupForm:
    """Test class for all tests related to the UserSignupForm"""

    @pytest.mark.django_db
    def test_valid_username_with_macrons(self):
        """Test that signup form accepts usernames with macrons."""
        form = UserSignupForm(
            {
                "email": "test@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "first_name": "Test",
                "last_name": "User",
                "username": "māori_user",
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    def test_invalid_username_with_special_characters(self):
        """Test that signup form rejects usernames with invalid characters."""
        form = UserSignupForm(
            {
                "email": "test@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "first_name": "Test",
                "last_name": "User",
                "username": "user@invalid",
            },
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert any(
            "Username must only include numbers, letters (including macrons)"
            in str(error)
            for error in form.errors["username"]
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "username",
        [
            "a",  # single letter
            "ā",  # single macron
            "user.name_test-123",  # all allowed characters
            "MĀORI",  # uppercase macrons
            "test_ā.user-123",  # mixed case with macrons
        ],
    )
    def test_valid_username_boundary_cases(self, username):
        """Test boundary cases for valid usernames."""
        form = UserSignupForm(
            {
                "email": "test@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "first_name": "Test",
                "last_name": "User",
                "username": username,
            },
        )
        assert form.is_valid(), (
            f"Username '{username}' should be valid, errors: {form.errors}"
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "invalid_username",
        [
            "user@domain",  # @ symbol
            "user name",  # space
            "user#123",  # hash
            "user!",  # exclamation
            "userñ",  # Spanish ñ
            "user™",  # trademark symbol
        ],
    )
    def test_invalid_usernames_parametrized(self, invalid_username):
        """Test various invalid usernames using parametrized test."""
        form = UserSignupForm(
            {
                "email": "test@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
                "first_name": "Test",
                "last_name": "User",
                "username": invalid_username,
            },
        )
        assert not form.is_valid(), f"Username '{invalid_username}' should be invalid"
        assert "username" in form.errors


class TestUserUpdateForm:
    """Test class for all tests related to the UserUpdateForm."""

    @pytest.mark.django_db
    def test_form_has_correct_fields(self):
        """Test that the form has all expected fields."""
        form = UserUpdateForm()
        assert "first_name" in form.fields
        assert "last_name" in form.fields
        assert "username" in form.fields
        assert "profile_picture" in form.fields

    @pytest.mark.django_db
    def test_valid_form_without_profile_picture(self, user: User):
        """Test that form is valid without a profile picture."""
        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": "Updated",
                "last_name": "Name",
                "username": user.username,
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    def test_valid_form_with_profile_picture(self, user: User):
        """Test that form is valid with a valid profile picture."""
        # Create a small test image
        image = Image.new("RGB", (100, 100), color="red")
        image_file = BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            "test_profile.jpg",
            image_file.read(),
            content_type="image/jpeg",
        )

        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
            files={"profile_picture": uploaded_file},
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        ("format_name", "pil_format"),
        [
            ("jpeg", "JPEG"),
            ("png", "PNG"),
            ("gif", "GIF"),
            ("webp", "WEBP"),
        ],
    )
    def test_valid_image_formats(self, user: User, format_name, pil_format):
        """Test that all supported image formats are accepted."""
        # Create a real image in the specified format
        image = Image.new("RGB", (50, 50), color="blue")
        image_file = BytesIO()
        image.save(image_file, format=pil_format)
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            f"test_image.{format_name}",
            image_file.read(),
            content_type=f"image/{format_name}",
        )

        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
            files={"profile_picture": uploaded_file},
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_type",
        ["image/bmp", "image/svg+xml", "application/pdf", "text/plain"],
    )
    def test_invalid_image_formats(self, user: User, content_type):
        """Test that unsupported file formats are rejected."""
        uploaded_file = SimpleUploadedFile(
            "test_file.bmp",
            b"fake file content",
            content_type=content_type,
        )

        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
            files={"profile_picture": uploaded_file},
        )
        assert not form.is_valid()
        assert "profile_picture" in form.errors
        # Django's built-in validation message for invalid images
        assert "valid image" in str(form.errors["profile_picture"]).lower()

    @pytest.mark.django_db
    def test_file_size_too_large(self, user: User):
        """Test that files larger than 5MB are rejected."""
        # Create a mock file that's larger than 5MB
        large_file = Mock()
        large_file.size = 6 * 1024 * 1024  # 6MB
        large_file.content_type = "image/jpeg"
        large_file.name = "large_image.jpg"

        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
        )
        # Manually set the cleaned data to test validation
        form.cleaned_data = {"profile_picture": large_file}
        with pytest.raises(ValidationError) as exc_info:
            form.clean_profile_picture()
        assert "File size must be no more than 5MB" in str(exc_info.value)

    @pytest.mark.django_db
    def test_file_size_exactly_5mb(self, user: User):
        """Test that files exactly 5MB are accepted."""
        # Create a mock file that's exactly 5MB
        exact_file = Mock()
        exact_file.size = 5 * 1024 * 1024  # Exactly 5MB
        exact_file.content_type = "image/jpeg"
        exact_file.name = "exact_image.jpg"

        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
        )
        form.cleaned_data = {"profile_picture": exact_file}

        # Should not raise an exception
        result = form.clean_profile_picture()
        assert result == exact_file

    @pytest.mark.django_db
    def test_profile_picture_is_optional(self, user: User):
        """Test that profile_picture field is optional."""
        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"
        assert form.cleaned_data["profile_picture"] is None

    @pytest.mark.django_db
    def test_username_validation_in_update_form(self, user: User):
        """Test that username validation works in update form."""
        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": "invalid@username",
            },
        )
        assert not form.is_valid()
        assert "username" in form.errors
        assert any(
            "Username must only include numbers, letters (including macrons)"
            in str(error)
            for error in form.errors["username"]
        )

    @pytest.mark.django_db
    def test_update_with_macron_username(self, user: User):
        """Test updating to a username with macrons."""
        form = UserUpdateForm(
            instance=user,
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": "māori_user",
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"
