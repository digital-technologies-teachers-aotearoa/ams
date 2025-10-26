"""Module for all Form Tests."""

import pytest
from django.utils.translation import gettext_lazy as _

from ams.users.forms import UserAdminCreationForm
from ams.users.forms import UserSignupForm
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
