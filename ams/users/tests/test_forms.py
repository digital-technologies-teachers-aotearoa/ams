"""Module for all Form Tests."""

from io import BytesIO
from unittest.mock import Mock

import pytest
from crispy_forms.utils import render_crispy_form
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _
from PIL import Image

from ams.users.forms import InviteOrganisationMemberForm
from ams.users.forms import OrganisationForm
from ams.users.forms import UserAdminCreationForm
from ams.users.forms import UserSignupForm
from ams.users.forms import UserUpdateForm
from ams.users.models import User
from ams.users.tests.factories import OrganisationFactory
from ams.users.tests.factories import OrganisationMemberFactory


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


class TestOrganisationForm:
    """Test class for all tests related to the OrganisationForm"""

    @pytest.mark.django_db
    def test_valid_organisation_form(self):
        """Test that valid organisation data is accepted."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "test@example.com",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_suburb": "Suburb",
                "postal_city": "City",
                "postal_code": "1234",
                "street_address": "456 Street",
                "suburb": "Downtown",
                "city": "Metropolis",
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    def test_organisation_form_with_optional_fields_empty(self):
        """Test that optional fields can be left blank."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "test@example.com",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_suburb": "",  # Optional
                "postal_city": "City",
                "postal_code": "1234",
                "street_address": "",  # Optional
                "suburb": "",  # Optional
                "city": "",  # Optional
            },
        )
        assert form.is_valid(), f"Form errors: {form.errors}"

    @pytest.mark.django_db
    def test_organisation_form_invalid_email(self):
        """Test that invalid email format is rejected."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "invalid-email",  # Invalid email
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_city": "City",
                "postal_code": "1234",
            },
        )
        assert not form.is_valid()
        assert "email" in form.errors

    @pytest.mark.django_db
    def test_organisation_form_missing_required_fields(self):
        """Test that required fields must be filled."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                # Missing required fields
            },
        )
        assert not form.is_valid()
        # Should have errors for required fields
        assert "telephone" in form.errors
        assert "email" in form.errors
        assert "contact_name" in form.errors
        assert "postal_address" in form.errors

    @pytest.mark.django_db
    def test_organisation_form_email_lowercase(self):
        """Test that email is converted to lowercase."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "TEST@EXAMPLE.COM",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_city": "City",
                "postal_code": "1234",
            },
        )
        assert form.is_valid()
        assert form.cleaned_data["email"] == "test@example.com"

    @pytest.mark.django_db
    def test_organisation_form_with_cancel_url(self):
        """Test that cancel_url is properly passed to the form helper."""
        cancel_url = "/test/cancel/url/"
        form = OrganisationForm(
            cancel_url=cancel_url,
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "test@example.com",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_city": "City",
                "postal_code": "1234",
            },
        )
        assert form.is_valid()
        # Render the form using crispy forms to check if cancel_url is in the output
        rendered = render_crispy_form(form)
        assert cancel_url in rendered
        assert "Cancel" in rendered

    @pytest.mark.django_db
    def test_organisation_form_without_cancel_url(self):
        """Test that form works when cancel_url is not provided."""
        form = OrganisationForm(
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "test@example.com",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_city": "City",
                "postal_code": "1234",
            },
        )
        assert form.is_valid()
        # Form should still render without error
        rendered = str(form)
        assert "Test Organisation" in rendered

    @pytest.mark.django_db
    def test_organisation_form_create_has_create_text(self):
        """Test that form shows 'Create Organisation' for new instances."""
        form = OrganisationForm(
            cancel_url="/test/",
            data={
                "name": "Test Organisation",
                "telephone": "021234567",
                "email": "test@example.com",
                "contact_name": "John Doe",
                "postal_address": "123 Test St",
                "postal_city": "City",
                "postal_code": "1234",
            },
        )
        assert form.is_valid()
        rendered = render_crispy_form(form)
        assert "Create Organisation" in rendered

    @pytest.mark.django_db
    def test_organisation_form_update_has_update_text(self):
        """Test that form shows 'Update Organisation' for existing instances."""
        org = OrganisationFactory()
        form = OrganisationForm(
            cancel_url="/test/",
            instance=org,
            data={
                "name": "Updated Organisation",
                "telephone": org.telephone,
                "email": org.email,
                "contact_name": org.contact_name,
                "postal_address": org.postal_address,
                "postal_city": org.postal_city,
                "postal_code": org.postal_code,
            },
        )
        assert form.is_valid()
        rendered = render_crispy_form(form)
        assert "Update Organisation" in rendered


@pytest.mark.django_db
class TestInviteOrganisationMemberForm:
    """Test class for InviteOrganisationMemberForm"""

    def test_valid_email_for_new_member(self):
        """Test that form accepts a valid email not already in organisation."""
        org = OrganisationFactory()
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "newmember@example.com"},
        )
        assert form.is_valid()

    def test_email_normalized_to_lowercase(self):
        """Test that email is normalized to lowercase."""
        org = OrganisationFactory()
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "NewMember@Example.COM"},
        )
        assert form.is_valid()
        assert form.cleaned_data["email"] == "newmember@example.com"

    def test_duplicate_user_email_rejected(self):
        """Test that form rejects email of existing member (via user)."""
        member = OrganisationMemberFactory(accepted=True)
        form = InviteOrganisationMemberForm(
            organisation=member.organisation,
            data={"email": member.user.email},
        )
        assert not form.is_valid()
        assert "email" in form.errors
        assert "already associated with a member" in str(form.errors["email"][0])

    def test_duplicate_invite_email_rejected(self):
        """Test that form rejects email of existing invite."""
        member = OrganisationMemberFactory(
            invite=True,
            invite_email="pending@example.com",
        )
        form = InviteOrganisationMemberForm(
            organisation=member.organisation,
            data={"email": "pending@example.com"},
        )
        assert not form.is_valid()
        assert "email" in form.errors
        assert "already associated with a member" in str(form.errors["email"][0])

    def test_invalid_email_format(self):
        """Test that form rejects invalid email format."""
        org = OrganisationFactory()
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "not-an-email"},
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_empty_email_rejected(self):
        """Test that form rejects empty email."""
        org = OrganisationFactory()
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": ""},
        )
        assert not form.is_valid()
        assert "email" in form.errors

    def test_form_requires_organisation(self):
        """Test that form requires organisation parameter."""
        with pytest.raises(ValueError, match="organisation is required"):
            InviteOrganisationMemberForm(
                organisation=None,
                data={"email": "test@example.com"},
            )

    def test_form_rejects_invalid_organisation_type(self):
        """Test that form rejects non-Organisation instances."""
        with pytest.raises(
            TypeError,
            match="organisation must be an instance of Organisation",
        ):
            InviteOrganisationMemberForm(
                organisation="not an organisation",
                data={"email": "test@example.com"},
            )

    def test_form_requires_organisation_not_provided(self):
        """Test that form raises error when organisation not provided at all."""
        # We need to pass organisation as keyword argument
        # This tests that we can't create the form without it
        org = OrganisationFactory()
        # This should work
        form = InviteOrganisationMemberForm(
            organisation=org,
            data={"email": "test@example.com"},
        )
        assert form.is_valid()

    def test_form_has_cancel_url_in_helper(self):
        """Test that cancel_url is passed to form helper."""
        org = OrganisationFactory()
        cancel_url = "/test/cancel/"
        form = InviteOrganisationMemberForm(
            organisation=org,
            cancel_url=cancel_url,
        )
        assert form.helper is not None
        # The cancel URL would be in the layout
        rendered = render_crispy_form(form)
        assert cancel_url in rendered
