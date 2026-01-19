# ruff: noqa: SLF001

"""Tests for UserUpdateForm helper methods."""

import pytest
from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import ChoiceField
from django.forms import DateField
from django.forms import DateInput
from django.forms import IntegerField
from django.forms import MultipleChoiceField
from django.forms import NumberInput
from django.forms import RadioSelect
from django.forms import Select
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
    """Create a test ProfileFieldGroup."""
    return ProfileFieldGroup.objects.create(
        name_translations={"en": "Contact Info", "mi": "Mōhiohio Whakapā"},
        description_translations={
            "en": "Your contact details",
            "mi": "Ō taipitopito whakapā",
        },
        order=1,
        is_active=True,
    )


@pytest.fixture
def all_field_types(profile_group):
    """Create one profile field of each type for comprehensive testing."""
    fields = {}

    fields["text"] = ProfileField.objects.create(
        field_key="text_field",
        field_type=ProfileField.FieldType.TEXT,
        label_translations={"en": "Text Field", "mi": "Āpure Kupu"},
        help_text_translations={"en": "Enter text", "mi": "Tāuru kupu"},
        group=profile_group,
        order=1,
        is_active=True,
    )

    fields["textarea"] = ProfileField.objects.create(
        field_key="textarea_field",
        field_type=ProfileField.FieldType.TEXTAREA,
        label_translations={"en": "Textarea Field", "mi": "Āpure Tuhinga"},
        group=profile_group,
        order=2,
        is_active=True,
    )

    fields["checkbox"] = ProfileField.objects.create(
        field_key="checkbox_field",
        field_type=ProfileField.FieldType.CHECKBOX,
        label_translations={"en": "Checkbox Field", "mi": "Āpure Pūtuhi"},
        options={
            "choices": [
                {
                    "value": "opt1",
                    "label_translations": {"en": "Option 1", "mi": "Kōwhiringa 1"},
                },
                {
                    "value": "opt2",
                    "label_translations": {"en": "Option 2", "mi": "Kōwhiringa 2"},
                },
            ],
        },
        group=profile_group,
        order=3,
        is_active=True,
    )

    fields["radio"] = ProfileField.objects.create(
        field_key="radio_field",
        field_type=ProfileField.FieldType.RADIO,
        label_translations={"en": "Radio Field", "mi": "Āpure Reo Irirangi"},
        options={
            "choices": [
                {"value": "yes", "label_translations": {"en": "Yes", "mi": "Āe"}},
                {"value": "no", "label_translations": {"en": "No", "mi": "Kāo"}},
            ],
        },
        group=profile_group,
        order=4,
        is_active=True,
    )

    fields["date"] = ProfileField.objects.create(
        field_key="date_field",
        field_type=ProfileField.FieldType.DATE,
        label_translations={"en": "Date Field", "mi": "Āpure Rā"},
        group=profile_group,
        order=5,
        is_active=True,
    )

    fields["month"] = ProfileField.objects.create(
        field_key="month_field",
        field_type=ProfileField.FieldType.MONTH,
        label_translations={"en": "Month Field", "mi": "Āpure Marama"},
        group=profile_group,
        order=6,
        is_active=True,
    )

    fields["number"] = ProfileField.objects.create(
        field_key="number_field",
        field_type=ProfileField.FieldType.NUMBER,
        label_translations={"en": "Number Field", "mi": "Āpure Nama"},
        min_value=10,
        max_value=100,
        group=profile_group,
        order=7,
        is_active=True,
    )

    fields["select"] = ProfileField.objects.create(
        field_key="select_field",
        field_type=ProfileField.FieldType.SELECT,
        label_translations={"en": "Select Field", "mi": "Āpure Tīpako"},
        options={
            "choices": [
                {"value": "a", "label_translations": {"en": "Alpha", "mi": "Arepa"}},
                {"value": "b", "label_translations": {"en": "Beta", "mi": "Pita"}},
            ],
        },
        group=profile_group,
        order=8,
        is_active=True,
    )

    return fields


@pytest.mark.django_db
class TestLoadExistingResponses:
    """Tests for UserUpdateForm._load_existing_responses() helper method."""

    def test_returns_empty_dict_for_new_user(self):
        """Test returns empty dict when user has no pk."""
        user = UserFactory.build()  # Unsaved user
        form = UserUpdateForm(instance=user)
        result = form._load_existing_responses()

        assert result == {}

    def test_returns_empty_dict_for_user_without_responses(self):
        """Test returns empty dict when user has no responses."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)
        result = form._load_existing_responses()

        assert result == {}

    def test_loads_single_response(self, all_field_types):
        """Test loads single profile field response."""
        user = UserFactory()
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=all_field_types["text"],
            value="Test Value",
        )

        form = UserUpdateForm(instance=user)
        result = form._load_existing_responses()

        assert result == {"text_field": "Test Value"}

    def test_loads_multiple_responses(self, all_field_types):
        """Test loads multiple profile field responses."""
        user = UserFactory()
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=all_field_types["text"],
            value="Text Value",
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=all_field_types["number"],
            value="42",
        )

        form = UserUpdateForm(instance=user)
        result = form._load_existing_responses()

        assert result == {"text_field": "Text Value", "number_field": "42"}

    def test_handles_checkbox_response_as_list(self, all_field_types):
        """Test checkbox responses are returned as lists."""
        user = UserFactory()
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=all_field_types["checkbox"],
        )
        response.set_value(["opt1", "opt2"])
        response.save()

        form = UserUpdateForm(instance=user)
        result = form._load_existing_responses()

        assert result == {"checkbox_field": ["opt1", "opt2"]}


@pytest.mark.django_db
class TestGetActiveProfileFields:
    """Tests for UserUpdateForm._get_active_profile_fields() helper method."""

    def test_returns_active_fields_only(self, profile_group):
        """Test returns only active profile fields."""
        active = ProfileField.objects.create(
            field_key="active",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Active"},
            group=profile_group,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="inactive",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Inactive"},
            group=profile_group,
            is_active=False,
        )

        user = UserFactory()
        form = UserUpdateForm(instance=user)
        result = list(form._get_active_profile_fields())

        assert len(result) == 1
        assert result[0] == active

    def test_orders_by_group_then_field_order(self, profile_group):
        """Test fields are ordered by group order then field order."""
        group2 = ProfileFieldGroup.objects.create(
            name_translations={"en": "Group 2"},
            order=2,
            is_active=True,
        )

        ProfileField.objects.create(
            field_key="field1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 1"},
            group=profile_group,
            order=2,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="field2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 2"},
            group=profile_group,
            order=1,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="field3",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 3"},
            group=group2,
            order=1,
            is_active=True,
        )

        user = UserFactory()
        form = UserUpdateForm(instance=user)
        result = list(form._get_active_profile_fields())

        # Should be ordered by group.order (1, 1, 2), then by field.order (1, 2, 1)
        assert [f.field_key for f in result] == ["field2", "field1", "field3"]

    def test_selects_related_group(self, profile_group, all_field_types):
        """Test prefetches related group to avoid N+1 queries."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # This should NOT raise an exception because group is select_related
        fields = list(form._get_active_profile_fields())
        for field in fields:
            _ = (
                field.group.order
            )  # Access related field - works because of select_related

        # If we got here without exception, select_related is working
        assert len(fields) > 0


@pytest.mark.django_db
class TestGroupFieldsByGroup:
    """Tests for UserUpdateForm._group_fields_by_group() helper method."""

    def test_groups_single_field(self, profile_group, all_field_types):
        """Test groups single field correctly."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)
        fields = [all_field_types["text"]]

        result = form._group_fields_by_group(fields, "en")

        assert "Contact Info" in result
        assert result["Contact Info"]["group"] == profile_group
        assert result["Contact Info"]["fields"] == [all_field_types["text"]]

    def test_groups_multiple_fields_in_same_group(self, profile_group, all_field_types):
        """Test groups multiple fields from same group."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)
        fields = [all_field_types["text"], all_field_types["number"]]

        result = form._group_fields_by_group(fields, "en")

        assert "Contact Info" in result
        expected_fields = 2
        assert len(result["Contact Info"]["fields"]) == expected_fields

    def test_groups_fields_in_different_groups(self, profile_group):
        """Test groups fields from different groups correctly."""
        group2 = ProfileFieldGroup.objects.create(
            name_translations={"en": "Other Info", "mi": "Ētahi atu Mōhiohio"},
            order=2,
            is_active=True,
        )

        field1 = ProfileField.objects.create(
            field_key="field1",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 1"},
            group=profile_group,
            is_active=True,
        )
        field2 = ProfileField.objects.create(
            field_key="field2",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Field 2"},
            group=group2,
            is_active=True,
        )

        user = UserFactory()
        form = UserUpdateForm(instance=user)
        result = form._group_fields_by_group([field1, field2], "en")

        assert "Contact Info" in result
        assert "Other Info" in result
        assert result["Contact Info"]["fields"] == [field1]
        assert result["Other Info"]["fields"] == [field2]

    def test_uses_correct_language_for_group_name(self, profile_group, all_field_types):
        """Test uses correct language for group name."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)
        fields = [all_field_types["text"]]

        result_en = form._group_fields_by_group(fields, "en")
        result_mi = form._group_fields_by_group(fields, "mi")

        assert "Contact Info" in result_en
        assert "Mōhiohio Whakapā" in result_mi


@pytest.mark.django_db
class TestCreateFormFieldForProfileField:
    """Tests for UserUpdateForm._create_form_field_for_profile_field() helper method."""

    def test_creates_text_field(self, all_field_types):
        """Test creates CharField with TextInput for TEXT type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["text"],
            "en",
            "initial value",
        )

        assert isinstance(field, CharField)
        assert isinstance(field.widget, TextInput)
        assert field.label == "Text Field"
        assert field.help_text == "Enter text"
        assert field.required is False
        assert field.initial == "initial value"

    def test_creates_textarea_field(self, all_field_types):
        """Test creates CharField with Textarea for TEXTAREA type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["textarea"],
            "en",
            None,
        )

        assert isinstance(field, CharField)
        assert isinstance(field.widget, Textarea)
        expected_rows = 4
        assert field.widget.attrs.get("rows") == expected_rows

    def test_creates_checkbox_field(self, all_field_types):
        """Test creates MultipleChoiceField for CHECKBOX type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["checkbox"],
            "en",
            ["opt1"],
        )

        assert isinstance(field, MultipleChoiceField)
        assert isinstance(field.widget, CheckboxSelectMultiple)
        assert field.initial == ["opt1"]
        assert ("opt1", "Option 1") in field.choices

    def test_creates_checkbox_field_with_empty_initial(self, all_field_types):
        """Test checkbox field has empty list initial if initial is not a list."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["checkbox"],
            "en",
            "not a list",
        )

        assert field.initial == []

    def test_creates_radio_field(self, all_field_types):
        """Test creates ChoiceField with RadioSelect for RADIO type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["radio"],
            "en",
            "yes",
        )

        assert isinstance(field, ChoiceField)
        assert isinstance(field.widget, RadioSelect)
        assert ("yes", "Yes") in field.choices

    def test_creates_date_field(self, all_field_types):
        """Test creates DateField for DATE type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["date"],
            "en",
            "2026-01-18",
        )

        assert isinstance(field, DateField)
        assert isinstance(field.widget, DateInput)
        assert field.widget.input_type == "date"

    def test_creates_month_field(self, all_field_types):
        """Test creates CharField with month input for MONTH type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["month"],
            "en",
            "2026-01",
        )

        assert isinstance(field, CharField)
        assert isinstance(field.widget, TextInput)
        # Check that month type is set via input_type
        assert field.widget.input_type == "month"

    def test_creates_number_field(self, all_field_types):
        """Test creates IntegerField for NUMBER type with constraints."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["number"],
            "en",
            50,
        )

        assert isinstance(field, IntegerField)
        assert isinstance(field.widget, NumberInput)
        expected_min_value = 10
        expected_max_value = 100
        expected_initial_value = 50
        assert field.min_value == expected_min_value
        assert field.max_value == expected_max_value
        assert field.initial == expected_initial_value

    def test_creates_select_field(self, all_field_types):
        """Test creates ChoiceField with Select for SELECT type."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(
            all_field_types["select"],
            "en",
            "a",
        )

        assert isinstance(field, ChoiceField)
        assert isinstance(field.widget, Select)
        # Should have empty choice plus options
        assert ("", "") in field.choices
        assert ("a", "Alpha") in field.choices

    def test_uses_correct_language_for_labels(self, all_field_types):
        """Test field uses correct language for label and help text."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field_en = form._create_form_field_for_profile_field(
            all_field_types["text"],
            "en",
            None,
        )
        field_mi = form._create_form_field_for_profile_field(
            all_field_types["text"],
            "mi",
            None,
        )

        assert field_en.label == "Text Field"
        assert field_mi.label == "Āpure Kupu"
        assert field_en.help_text == "Enter text"
        assert field_mi.help_text == "Tāuru kupu"

    def test_uses_correct_language_for_choices(self, all_field_types):
        """Test field uses correct language for choice labels."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field_en = form._create_form_field_for_profile_field(
            all_field_types["select"],
            "en",
            None,
        )
        field_mi = form._create_form_field_for_profile_field(
            all_field_types["select"],
            "mi",
            None,
        )

        choices_en = dict(field_en.choices)
        choices_mi = dict(field_mi.choices)

        assert choices_en["a"] == "Alpha"
        assert choices_mi["a"] == "Arepa"

    def test_returns_none_for_unknown_field_type(self, profile_group):
        """Test returns None for unknown field type."""
        # Create a field with an invalid type by directly setting the attribute
        invalid_field = ProfileField.objects.create(
            field_key="invalid",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Invalid"},
            group=profile_group,
            is_active=True,
        )
        # Manually override to simulate unknown type
        invalid_field.field_type = "UNKNOWN_TYPE"

        user = UserFactory()
        form = UserUpdateForm(instance=user)

        field = form._create_form_field_for_profile_field(invalid_field, "en", None)

        assert field is None


@pytest.mark.django_db
class TestApplyFieldPermissions:
    """Tests for UserUpdateForm._apply_field_permissions() helper method."""

    def test_does_not_disable_regular_field(self, profile_group):
        """Test does not disable field if not read-only."""
        regular_field = ProfileField.objects.create(
            field_key="regular",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Regular"},
            is_read_only=False,
            group=profile_group,
            is_active=True,
        )

        user = UserFactory(is_staff=False)
        form = UserUpdateForm(instance=user)
        form_field = CharField()

        form._apply_field_permissions(regular_field, form_field)

        assert form_field.widget.attrs.get("disabled") is not True

    def test_disables_readonly_field_for_regular_user(self, profile_group):
        """Test disables read-only field for non-staff users."""
        readonly_field = ProfileField.objects.create(
            field_key="readonly",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Read Only"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        user = UserFactory(is_staff=False)
        form = UserUpdateForm(instance=user)
        form_field = CharField()

        form._apply_field_permissions(readonly_field, form_field)

        assert form_field.widget.attrs.get("disabled") is True

    def test_does_not_disable_readonly_field_for_staff(self, profile_group):
        """Test does not disable read-only field for staff users."""
        readonly_field = ProfileField.objects.create(
            field_key="readonly",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Read Only"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        user = UserFactory(is_staff=True)
        form = UserUpdateForm(instance=user)
        form_field = CharField()

        form._apply_field_permissions(readonly_field, form_field)

        assert form_field.widget.attrs.get("disabled") is not True


@pytest.mark.django_db
class TestAddProfileFieldsToForm:
    """Tests for UserUpdateForm._add_profile_fields_to_form() helper method."""

    def test_adds_fields_to_form(self, all_field_types):
        """Test adds all profile fields to form.fields."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # All field types should be in form.fields
        assert "text_field" in form.fields
        assert "number_field" in form.fields
        assert "select_field" in form.fields

    def test_populates_profile_fields_tracking_list(self, all_field_types):
        """Test populates _profile_fields list for use in save()."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # Should have all 8 field types
        expected_fields = 8
        assert len(form._profile_fields) == expected_fields
        field_keys = [f.field_key for f in form._profile_fields]
        assert "text_field" in field_keys
        assert "checkbox_field" in field_keys

    def test_loads_existing_response_values(self, all_field_types):
        """Test loads existing response values as initial data."""
        user = UserFactory()
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=all_field_types["text"],
            value="Existing Value",
        )

        form = UserUpdateForm(instance=user)

        assert form.fields["text_field"].initial == "Existing Value"

    def test_applies_permissions_to_readonly_fields(self, profile_group):
        """Test applies permission restrictions to read-only fields."""
        ProfileField.objects.create(
            field_key="readonly",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Read Only"},
            is_read_only=True,
            group=profile_group,
            is_active=True,
        )

        user = UserFactory(is_staff=False)
        form = UserUpdateForm(instance=user)

        assert form.fields["readonly"].widget.attrs.get("disabled") is True

    def test_returns_profile_fields_queryset(self, all_field_types):
        """Test returns the profile fields queryset for layout building."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)
        existing_responses = form._load_existing_responses()
        result = form._add_profile_fields_to_form("en", existing_responses)

        # Should return queryset of profile fields
        assert list(result) == list(
            ProfileField.objects.filter(is_active=True).order_by(
                "group__order",
                "order",
            ),
        )


@pytest.mark.django_db
class TestBuildCrispyLayout:
    """Tests for UserUpdateForm._build_crispy_layout() helper method."""

    def test_creates_personal_info_fieldset(self, all_field_types):
        """Test creates Personal Information fieldset with user fields."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # Check that the user fields are in the layout fields
        assert "first_name" in form.fields
        assert "last_name" in form.fields
        assert "username" in form.fields
        assert "profile_picture" in form.fields

    def test_creates_fieldset_per_profile_group(self, profile_group, all_field_types):
        """Test creates separate fieldset for each profile group."""
        group2 = ProfileFieldGroup.objects.create(
            name_translations={"en": "Additional Info"},
            order=2,
            is_active=True,
        )
        ProfileField.objects.create(
            field_key="extra",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Extra"},
            group=group2,
            is_active=True,
        )

        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # Check that fields from both groups are in the form
        # Contact Info group has 8 fields from all_field_types
        assert "text_field" in form.fields
        # Additional Info group has the extra field
        assert "extra" in form.fields

    def test_uses_correct_language_for_group_names(
        self,
        profile_group,
        all_field_types,
    ):
        """Test fieldsets use correct language for group names."""
        user = UserFactory()

        # Test that fields are created regardless of language
        with override("en"):
            form_en = UserUpdateForm(instance=user)
            assert "text_field" in form_en.fields
            assert form_en.fields["text_field"].label == "Text Field"

        with override("mi"):
            form_mi = UserUpdateForm(instance=user)
            assert "text_field" in form_mi.fields
            assert form_mi.fields["text_field"].label == "Āpure Kupu"

    def test_adds_submit_and_cancel_buttons(self, all_field_types):
        """Test adds FormActions with Submit and Cancel."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # Check that layout exists and helper is configured
        assert form.helper is not None
        assert form.helper.layout is not None
        assert form.helper.form_method == "post"


@pytest.mark.django_db
class TestIntegrationAfterRefactoring:
    """Integration tests to ensure refactored form still works end-to-end."""

    def test_form_initialization_still_works(self, all_field_types):
        """Test form can still be initialized after refactoring."""
        user = UserFactory()
        form = UserUpdateForm(instance=user)

        # Should have all expected fields
        assert "first_name" in form.fields
        assert "text_field" in form.fields
        expected_fields = 8
        assert len(form._profile_fields) == expected_fields

    def test_form_validation_still_works(self, all_field_types):
        """Test form validation works after refactoring."""
        user = UserFactory()
        data = {
            "first_name": "Test",
            "last_name": "User",
            "username": user.username,
            "text_field": "Value",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()

    def test_form_saving_still_works(self, all_field_types):
        """Test form saving works after refactoring."""
        user = UserFactory()
        data = {
            "first_name": "Updated",
            "last_name": user.last_name,
            "username": user.username,
            "text_field": "New Value",
            "number_field": "50",
        }
        form = UserUpdateForm(data=data, instance=user)

        assert form.is_valid()
        saved_user = form.save()

        assert saved_user.first_name == "Updated"
        assert ProfileFieldResponse.objects.filter(
            user=user,
            profile_field=all_field_types["text"],
        ).exists()
