import pytest
from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import ChoiceField
from django.forms import DateField
from django.forms import DateInput
from django.forms import IntegerField
from django.forms import MultipleChoiceField
from django.forms import RadioSelect
from django.forms import Textarea
from django.forms import TextInput
from django.utils.translation import override

from ams.users.forms import UserUpdateForm
from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.users.models import ProfileFieldResponse
from ams.users.tests.factories import UserFactory


@pytest.fixture
def profile_group():
    """Create a minimal valid ProfileFieldGroup."""
    return ProfileFieldGroup.objects.create(
        name_translations={"en": "Test Group"},
        is_active=True,
    )


@pytest.mark.django_db
class TestUserUpdateFormWithProfileFields:
    """Tests for UserUpdateForm with dynamic profile fields."""

    def test_form_includes_active_profile_fields(self, profile_group):
        """Test form includes all active profile fields."""
        user = UserFactory()

        # Create active profile fields
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="years_exp",
            field_type=ProfileField.FieldType.NUMBER,
            label_translations={"en": "Years Experience"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        # Check standard fields exist
        assert "first_name" in form.fields
        assert "last_name" in form.fields
        assert "username" in form.fields
        assert "profile_picture" in form.fields

        # Check profile fields exist
        assert "subject" in form.fields
        assert "years_exp" in form.fields

    def test_form_excludes_inactive_profile_fields(self, profile_group):
        """Test form excludes inactive profile fields."""
        user = UserFactory()

        # Create active field
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        # Create inactive field
        ProfileField.objects.create(
            field_key="inactive_field",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive"},
            group=profile_group,
            is_active=False,
        )

        form = UserUpdateForm(instance=user)

        # Active field should be included
        assert "subject" in form.fields

        # Inactive field should not be included
        assert "inactive_field" not in form.fields

    def test_form_loads_existing_responses(self, profile_group):
        """Test form loads existing responses as initial data."""
        user = UserFactory()

        # Create profile fields
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        number_field = ProfileField.objects.create(
            field_key="years_exp",
            field_type=ProfileField.FieldType.NUMBER,
            label_translations={"en": "Years Experience"},
            group=profile_group,
            is_active=True,
        )

        # Create existing responses
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Mathematics",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=number_field,
            value="5",
        )

        form = UserUpdateForm(instance=user)

        # Check initial values are loaded
        assert form.fields["subject"].initial == "Mathematics"
        assert form.fields["years_exp"].initial == "5"

    def test_form_field_labels_use_correct_language(self, profile_group):
        """Test field labels use correct language."""
        user = UserFactory()

        # Create field with translations
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject", "mi": "Kaupapa"},
            group=profile_group,
            is_active=True,
        )

        # Test English
        with override("en"):
            form = UserUpdateForm(instance=user)
            assert form.fields["subject"].label == "Subject"

        # Test Māori
        with override("mi"):
            form = UserUpdateForm(instance=user)
            assert form.fields["subject"].label == "Kaupapa"

    def test_form_field_help_text_uses_correct_language(self, profile_group):
        """Test field help text uses correct language."""
        user = UserFactory()

        # Create field with help text translations
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            help_text_translations={
                "en": "Your teaching subject",
                "mi": "Tō kaupapa whakaako",
            },
            group=profile_group,
            is_active=True,
        )

        # Test English
        with override("en"):
            form = UserUpdateForm(instance=user)
            assert form.fields["subject"].help_text == "Your teaching subject"

        # Test Māori
        with override("mi"):
            form = UserUpdateForm(instance=user)
            assert form.fields["subject"].help_text == "Tō kaupapa whakaako"

    def test_form_choices_use_correct_language(self, profile_group):
        """Test select field choices use correct language."""
        user = UserFactory()

        # Create select field with translated choices
        ProfileField.objects.create(
            field_key="school_level",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Level"},
            options={
                "choices": [
                    {
                        "value": "primary",
                        "label_translations": {"en": "Primary", "mi": "Tuatahi"},
                    },
                    {
                        "value": "secondary",
                        "label_translations": {"en": "Secondary", "mi": "Tuarua"},
                    },
                ],
            },
            group=profile_group,
            is_active=True,
        )

        # Test English
        with override("en"):
            form = UserUpdateForm(instance=user)
            choices = dict(form.fields["school_level"].choices)
            assert choices["primary"] == "Primary"
            assert choices["secondary"] == "Secondary"

        # Test Māori
        with override("mi"):
            form = UserUpdateForm(instance=user)
            choices = dict(form.fields["school_level"].choices)
            assert choices["primary"] == "Tuatahi"
            assert choices["secondary"] == "Tuarua"

    def test_readonly_field_disabled_for_regular_user(self, profile_group):
        """Test read-only field is disabled for regular users."""
        user = UserFactory(is_staff=False)

        # Create read-only field
        ProfileField.objects.create(
            field_key="admin_notes",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Admin Notes"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert form.fields["admin_notes"].widget.attrs.get("disabled") is True

    def test_readonly_field_enabled_for_staff(self, profile_group):
        """Test read-only field is enabled for staff users."""
        user = UserFactory(is_staff=True)

        # Create read-only field
        ProfileField.objects.create(
            field_key="admin_notes",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Admin Notes"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert form.fields["admin_notes"].widget.attrs.get("disabled") is not True

    def test_form_saves_user_fields(self, profile_group):
        """Test form saves user model fields."""
        user = UserFactory(first_name="Old", last_name="Name")

        # Create profile field
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        data = {
            "first_name": "New",
            "last_name": "Name",
            "username": user.username,
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        saved_user = form.save()

        assert saved_user.first_name == "New"
        assert saved_user.last_name == "Name"

    def test_form_creates_profile_field_response(self, profile_group):
        """Test form submission creates ProfileFieldResponse."""
        user = UserFactory()

        # Create profile field
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "subject": "Science",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        form.save()

        # Check response was created
        response = ProfileFieldResponse.objects.get(user=user, profile_field=text_field)
        assert response.get_value() == "Science"

    def test_form_updates_existing_profile_field_response(self, profile_group):
        """Test form submission updates existing ProfileFieldResponse."""
        user = UserFactory()

        # Create profile field
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        # Create existing response
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Old Value",
        )

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "subject": "New Value",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        form.save()

        # Refresh from database
        response.refresh_from_db()
        assert response.get_value() == "New Value"

    def test_form_deletes_response_when_field_cleared(self, profile_group):
        """Test form deletes response when field is cleared."""
        user = UserFactory()

        # Create profile field
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        # Create existing response
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Initial Value",
        )

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "subject": "",  # Empty value
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        form.save()

        # Check response was deleted
        assert not ProfileFieldResponse.objects.filter(
            user=user,
            profile_field=text_field,
        ).exists()

    def test_form_saves_checkbox_values_as_list(self, profile_group):
        """Test form saves checkbox values as JSON list."""
        user = UserFactory()

        # Create checkbox field with multiple choices
        checkbox_field = ProfileField.objects.create(
            field_key="subjects",
            field_type=ProfileField.FieldType.CHECKBOX,
            label_translations={"en": "Subjects"},
            options={
                "choices": [
                    {"value": "math", "label_translations": {"en": "Math"}},
                    {"value": "science", "label_translations": {"en": "Science"}},
                ],
            },
            group=profile_group,
            is_active=True,
        )

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "subjects": ["math", "science"],
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        form.save()

        # Check response was created with JSON list
        response = ProfileFieldResponse.objects.get(
            user=user,
            profile_field=checkbox_field,
        )
        assert response.get_value() == ["math", "science"]

    def test_form_removes_readonly_values_for_non_staff(self, profile_group):
        """Test form clean() removes read-only values for non-staff users."""
        user = UserFactory(is_staff=False)

        # Create read-only field
        ProfileField.objects.create(
            field_key="admin_notes",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Admin Notes"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        # Try to submit value for readonly field
        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "admin_notes": "Hacked value",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()

        # Readonly field should be removed from cleaned_data
        assert "admin_notes" not in form.cleaned_data

    def test_form_allows_readonly_values_for_staff(self, profile_group):
        """Test form clean() allows read-only values for staff users."""
        user = UserFactory(is_staff=True)

        # Create read-only field
        ProfileField.objects.create(
            field_key="admin_notes",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Admin Notes"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "admin_notes": "Staff value",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()

        # Readonly field should be in cleaned_data for staff
        assert form.cleaned_data.get("admin_notes") == "Staff value"

    def test_text_field_rendering(self, profile_group):
        """Test TEXT field type renders as CharField with TextInput."""
        user = UserFactory()

        # Create text field
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["subject"], CharField)
        assert isinstance(form.fields["subject"].widget, TextInput)

    def test_textarea_field_rendering(self, profile_group):
        """Test TEXTAREA field type renders as CharField with Textarea."""
        user = UserFactory()

        # Create textarea field
        ProfileField.objects.create(
            field_key="bio",
            field_type=ProfileField.FieldType.TEXTAREA,
            label_translations={"en": "Biography"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["bio"], CharField)
        assert isinstance(form.fields["bio"].widget, Textarea)

    def test_date_field_rendering(self, profile_group):
        """Test DATE field type renders as DateField."""
        user = UserFactory()

        # Create date field
        ProfileField.objects.create(
            field_key="start_date",
            field_type=ProfileField.FieldType.DATE,
            label_translations={"en": "Start Date"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["start_date"], DateField)
        assert isinstance(form.fields["start_date"].widget, DateInput)
        assert form.fields["start_date"].widget.input_type == "date"

    def test_month_field_rendering(self, profile_group):
        """Test MONTH field type renders correctly."""
        user = UserFactory()

        # Create month field
        ProfileField.objects.create(
            field_key="registration_month",
            field_type=ProfileField.FieldType.MONTH,
            label_translations={"en": "Registration Month"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["registration_month"], CharField)
        assert isinstance(form.fields["registration_month"].widget, TextInput)
        # Month input type is set in widget attrs during initialization
        # We can't check it directly, so we just verify it's a TextInput

    def test_number_field_rendering(self, profile_group):
        """Test NUMBER field type renders as IntegerField."""
        user = UserFactory()

        # Create number field with min/max constraints
        ProfileField.objects.create(
            field_key="years_exp",
            field_type=ProfileField.FieldType.NUMBER,
            label_translations={"en": "Years Experience"},
            min_value=0,
            max_value=50,
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["years_exp"], IntegerField)
        expected_min_value = 0
        expected_max_value = 50
        assert form.fields["years_exp"].min_value == expected_min_value
        assert form.fields["years_exp"].max_value == expected_max_value

    def test_select_field_rendering(self, profile_group):
        """Test SELECT field type renders as ChoiceField."""
        user = UserFactory()

        # Create select field with 2 choices
        ProfileField.objects.create(
            field_key="school_level",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Level"},
            options={
                "choices": [
                    {"value": "primary", "label_translations": {"en": "Primary"}},
                    {"value": "secondary", "label_translations": {"en": "Secondary"}},
                ],
            },
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["school_level"], ChoiceField)
        # Should have empty choice plus 2 options = 3 total
        expected_choices = 3
        assert len(form.fields["school_level"].choices) == expected_choices

    def test_checkbox_field_rendering(self, profile_group):
        """Test CHECKBOX field type renders as MultipleChoiceField."""
        user = UserFactory()

        # Create checkbox field
        ProfileField.objects.create(
            field_key="subjects",
            field_type=ProfileField.FieldType.CHECKBOX,
            label_translations={"en": "Subjects"},
            options={
                "choices": [
                    {"value": "math", "label_translations": {"en": "Math"}},
                    {"value": "science", "label_translations": {"en": "Science"}},
                ],
            },
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["subjects"], MultipleChoiceField)
        assert isinstance(form.fields["subjects"].widget, CheckboxSelectMultiple)

    def test_radio_field_rendering(self, profile_group):
        """Test RADIO field type renders as ChoiceField with RadioSelect."""
        user = UserFactory()

        # Create radio field
        ProfileField.objects.create(
            field_key="employment",
            field_type=ProfileField.FieldType.RADIO,
            label_translations={"en": "Employment"},
            options={
                "choices": [
                    {"value": "fulltime", "label_translations": {"en": "Full-time"}},
                    {"value": "parttime", "label_translations": {"en": "Part-time"}},
                ],
            },
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert isinstance(form.fields["employment"], ChoiceField)
        assert isinstance(form.fields["employment"].widget, RadioSelect)

    def test_form_has_crispy_helper(self, profile_group):
        """Test form has crispy FormHelper configured."""
        user = UserFactory()

        # Create a field for the form
        ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )

        form = UserUpdateForm(instance=user)

        assert hasattr(form, "helper")
        assert form.helper.form_method == "post"
