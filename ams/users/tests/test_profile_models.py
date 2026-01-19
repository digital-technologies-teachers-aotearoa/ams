import json

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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
class TestProfileFieldGroup:
    """Tests for ProfileFieldGroup model."""

    def test_creation(self, profile_group):
        """Test ProfileFieldGroup can be created."""
        assert profile_group.pk is not None
        assert profile_group.is_active is True

    def test_get_name_english(self):
        """Test get_name returns English name."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Teaching Background", "mi": "Kōrero Whakaako"},
            is_active=True,
        )
        assert group.get_name("en") == "Teaching Background"

    def test_get_name_maori(self):
        """Test get_name returns Māori name."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Teaching Background", "mi": "Kōrero Whakaako"},
            is_active=True,
        )
        assert group.get_name("mi") == "Kōrero Whakaako"

    def test_get_name_fallback(self):
        """Test get_name falls back to first available translation."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Teaching Background", "mi": "Kōrero Whakaako"},
            is_active=True,
        )
        name = group.get_name("fr")
        assert name in ["Teaching Background", "Kōrero Whakaako"]

    def test_get_description_english(self):
        """Test get_description returns English description."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            description_translations={
                "en": "Information about your teaching career",
                "mi": "Mōhiohio mō tō mahi whakaako",
            },
            is_active=True,
        )
        assert group.get_description("en") == "Information about your teaching career"

    def test_get_description_maori(self):
        """Test get_description returns Māori description."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            description_translations={
                "en": "Information about your teaching career",
                "mi": "Mōhiohio mō tō mahi whakaako",
            },
            is_active=True,
        )
        assert group.get_description("mi") == "Mōhiohio mō tō mahi whakaako"

    def test_get_description_fallback(self):
        """Test get_description falls back to first available translation."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            description_translations={
                "en": "Information about your teaching career",
                "mi": "Mōhiohio mō tō mahi whakaako",
            },
            is_active=True,
        )
        description = group.get_description("fr")
        assert description in [
            "Information about your teaching career",
            "Mōhiohio mō tō mahi whakaako",
        ]

    def test_get_description_empty(self):
        """Test get_description returns empty string when no translations."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group"},
            description_translations={},
        )
        assert group.get_description("en") == ""

    def test_str(self):
        """Test __str__ method returns name."""
        group = ProfileFieldGroup.objects.create(
            name_translations={"en": "Teaching Background", "mi": "Kōrero Whakaako"},
            is_active=True,
        )
        assert str(group) in ["Teaching Background", "Kōrero Whakaako"]

    def test_ordering(self):
        """Test groups are ordered by order field."""
        group1 = ProfileFieldGroup.objects.create(
            name_translations={"en": "Group 1"},
            order=2,
        )
        group2 = ProfileFieldGroup.objects.create(
            name_translations={"en": "Group 2"},
            order=1,
        )
        groups = list(ProfileFieldGroup.objects.all())
        assert groups[0] == group2
        assert groups[1] == group1


@pytest.mark.django_db
class TestProfileField:
    """Tests for ProfileField model."""

    def test_creation_text(self, profile_group):
        """Test text ProfileField can be created."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject"},
            group=profile_group,
            is_active=True,
        )
        assert text_field.pk is not None
        assert text_field.field_key == "teaching_subject"
        assert text_field.field_type == ProfileField.FieldType.TEXT
        assert text_field.is_active is True

    def test_creation_number(self, profile_group):
        """Test number ProfileField can be created."""
        number_field = ProfileField.objects.create(
            field_key="years_experience",
            field_type=ProfileField.FieldType.NUMBER,
            label_translations={"en": "Years Experience"},
            min_value=0,
            max_value=50,
            group=profile_group,
            is_active=True,
        )
        assert number_field.pk is not None
        expected_min_value = 0
        expected_max_value = 50
        assert number_field.min_value == expected_min_value
        assert number_field.max_value == expected_max_value

    def test_creation_select(self, profile_group):
        """Test select ProfileField can be created."""
        select_field = ProfileField.objects.create(
            field_key="school_type",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Type"},
            options={
                "choices": [
                    {"value": "primary", "label_translations": {"en": "Primary"}},
                    {"value": "secondary", "label_translations": {"en": "Secondary"}},
                ],
            },
            group=profile_group,
            is_active=True,
        )
        assert select_field.pk is not None
        assert "choices" in select_field.options
        expected_options = 2
        assert len(select_field.options["choices"]) == expected_options

    def test_field_key_validation_valid(self, profile_group):
        """Test field_key validation accepts valid keys."""
        field = ProfileField(
            field_key="valid_key_123",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Test"},
            group=profile_group,
        )
        field.clean()  # Should not raise

    def test_field_key_validation_invalid_start(self, profile_group):
        """Test field_key validation rejects keys starting with number."""
        field = ProfileField(
            field_key="123invalid",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Test"},
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "field_key" in exc_info.value.error_dict

    def test_field_key_validation_invalid_chars(self, profile_group):
        """Test field_key validation rejects invalid characters."""
        field = ProfileField(
            field_key="invalid-key!",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Test"},
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "field_key" in exc_info.value.error_dict

    def test_label_translations_empty(self, profile_group):
        """Test validation fails when label_translations is empty."""
        field = ProfileField(
            field_key="test_field",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={},
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "label_translations" in exc_info.value.error_dict

    def test_select_validation_missing_choices(self, profile_group):
        """Test validation fails for select field without choices."""
        field = ProfileField(
            field_key="test_select",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "Test"},
            options={},
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "options" in exc_info.value.error_dict

    def test_checkbox_validation_missing_label_translations(self, profile_group):
        """Test validation fails for checkbox choice without label_translations."""
        field = ProfileField(
            field_key="test_checkbox",
            field_type=ProfileField.FieldType.CHECKBOX,
            label_translations={"en": "Test"},
            options={"choices": [{"value": "opt1"}]},
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "options" in exc_info.value.error_dict

    def test_number_validation_min_max(self, profile_group):
        """Test validation fails when min_value >= max_value."""
        field = ProfileField(
            field_key="test_number",
            field_type=ProfileField.FieldType.NUMBER,
            label_translations={"en": "Test"},
            min_value=10,
            max_value=5,
            group=profile_group,
        )
        with pytest.raises(ValidationError) as exc_info:
            field.clean()
        assert "min_value" in exc_info.value.error_dict

    def test_get_label_english(self, profile_group):
        """Test get_label returns English label."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject", "mi": "Kaupapa Whakaako"},
            group=profile_group,
            is_active=True,
        )
        assert text_field.get_label("en") == "Teaching Subject"

    def test_get_label_maori(self, profile_group):
        """Test get_label returns Māori label."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject", "mi": "Kaupapa Whakaako"},
            group=profile_group,
            is_active=True,
        )
        assert text_field.get_label("mi") == "Kaupapa Whakaako"

    def test_get_label_fallback(self, profile_group):
        """Test get_label falls back to first available translation."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject", "mi": "Kaupapa Whakaako"},
            group=profile_group,
            is_active=True,
        )
        label = text_field.get_label("fr")
        assert label in ["Teaching Subject", "Kaupapa Whakaako"]

    def test_get_help_text_english(self, profile_group):
        """Test get_help_text returns English help text."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject"},
            help_text_translations={
                "en": "What subject do you teach?",
                "mi": "He aha te kaupapa e whakaako ana koe?",
            },
            group=profile_group,
            is_active=True,
        )
        assert text_field.get_help_text("en") == "What subject do you teach?"

    def test_get_help_text_fallback(self, profile_group):
        """Test get_help_text falls back to first available translation."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject"},
            help_text_translations={
                "en": "What subject do you teach?",
                "mi": "He aha te kaupapa e whakaako ana koe?",
            },
            group=profile_group,
            is_active=True,
        )
        help_text = text_field.get_help_text("fr")
        assert help_text in [
            "What subject do you teach?",
            "He aha te kaupapa e whakaako ana koe?",
        ]

    def test_get_choices_english(self, profile_group):
        """Test get_choices returns English labels."""
        select_field = ProfileField.objects.create(
            field_key="school_type",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Type"},
            options={
                "choices": [
                    {
                        "value": "primary",
                        "label_translations": {
                            "en": "Primary School",
                            "mi": "Kura Tuatahi",
                        },
                    },
                    {
                        "value": "secondary",
                        "label_translations": {
                            "en": "Secondary School",
                            "mi": "Kura Tuarua",
                        },
                    },
                ],
            },
            group=profile_group,
            is_active=True,
        )
        choices = select_field.get_choices("en")
        expected_choice = 2
        assert len(choices) == expected_choice
        assert choices[0] == ("primary", "Primary School")
        assert choices[1] == ("secondary", "Secondary School")

    def test_get_choices_maori(self, profile_group):
        """Test get_choices returns Māori labels."""
        select_field = ProfileField.objects.create(
            field_key="school_type",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Type"},
            options={
                "choices": [
                    {
                        "value": "primary",
                        "label_translations": {
                            "en": "Primary School",
                            "mi": "Kura Tuatahi",
                        },
                    },
                    {
                        "value": "secondary",
                        "label_translations": {
                            "en": "Secondary School",
                            "mi": "Kura Tuarua",
                        },
                    },
                ],
            },
            group=profile_group,
            is_active=True,
        )
        choices = select_field.get_choices("mi")
        expected_choice = 2
        assert len(choices) == expected_choice
        assert choices[0] == ("primary", "Kura Tuatahi")
        assert choices[1] == ("secondary", "Kura Tuarua")

    def test_get_choices_fallback(self, profile_group):
        """Test get_choices falls back to first available translation."""
        select_field = ProfileField.objects.create(
            field_key="school_type",
            field_type=ProfileField.FieldType.SELECT,
            label_translations={"en": "School Type"},
            options={
                "choices": [
                    {
                        "value": "primary",
                        "label_translations": {
                            "en": "Primary School",
                            "mi": "Kura Tuatahi",
                        },
                    },
                    {
                        "value": "secondary",
                        "label_translations": {
                            "en": "Secondary School",
                            "mi": "Kura Tuarua",
                        },
                    },
                ],
            },
            group=profile_group,
            is_active=True,
        )
        choices = select_field.get_choices("fr")
        expected_choice = 2
        assert len(choices) == expected_choice
        # Should get first available translation
        assert choices[0][0] == "primary"
        assert choices[0][1] in ["Primary School", "Kura Tuatahi"]

    def test_str(self, profile_group):
        """Test __str__ method returns label."""
        text_field = ProfileField.objects.create(
            field_key="teaching_subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Teaching Subject", "mi": "Kaupapa Whakaako"},
            group=profile_group,
            is_active=True,
        )
        assert str(text_field) in ["Teaching Subject", "Kaupapa Whakaako"]

    def test_unique_together(self, profile_group):
        """Test unique_together constraint on group and field_key."""
        text_field = ProfileField.objects.create(
            field_key="duplicate_key",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "First Field"},
            group=profile_group,
        )
        with pytest.raises(IntegrityError):
            ProfileField.objects.create(
                field_key=text_field.field_key,
                field_type=ProfileField.FieldType.TEXT,
                label_translations={"en": "Duplicate"},
                group=profile_group,
            )


@pytest.mark.django_db
class TestProfileFieldResponse:
    """Tests for ProfileFieldResponse model."""

    def test_creation(self, profile_group):
        """Test ProfileFieldResponse can be created."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Mathematics",
        )
        assert response.pk is not None
        assert response.user == user
        assert response.profile_field == text_field
        assert response.value == "Mathematics"

    def test_unique_together(self, profile_group):
        """Test unique_together constraint on user and profile_field."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="First",
        )
        with pytest.raises(IntegrityError):
            ProfileFieldResponse.objects.create(
                user=user,
                profile_field=text_field,
                value="Second",
            )

    def test_get_value_text(self, profile_group):
        """Test get_value returns text value."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Science",
        )
        assert response.get_value() == "Science"

    def test_get_value_empty(self, profile_group):
        """Test get_value returns None for empty value."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="",
        )
        assert response.get_value() is None

    def test_get_value_checkbox_list(self, profile_group):
        """Test get_value parses JSON list for checkbox fields."""
        user = UserFactory()
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
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=checkbox_field,
            value=json.dumps(["math", "science"]),
        )
        assert response.get_value() == ["math", "science"]

    def test_get_value_checkbox_invalid_json(self, profile_group):
        """Test get_value returns empty list for invalid JSON."""
        user = UserFactory()
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
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=checkbox_field,
            value="invalid json",
        )
        assert response.get_value() == []

    def test_set_value_text(self, profile_group):
        """Test set_value stores text value."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
        )
        response.set_value("History")
        assert response.value == "History"

    def test_set_value_none(self, profile_group):
        """Test set_value stores empty string for None."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
        )
        response.set_value(None)
        assert response.value == ""

    def test_set_value_list(self, profile_group):
        """Test set_value encodes list as JSON."""
        user = UserFactory()
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
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=checkbox_field,
        )
        response.set_value(["math", "science"])
        assert response.value == json.dumps(["math", "science"])
        assert response.get_value() == ["math", "science"]

    def test_str(self, profile_group):
        """Test __str__ method."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Test",
        )
        expected = f"{user.email} - {text_field.get_label()}"
        assert str(response) == expected

    def test_updated_datetime_auto(self, profile_group):
        """Test updated_datetime is automatically set."""
        user = UserFactory()
        text_field = ProfileField.objects.create(
            field_key="subject",
            field_type=ProfileField.FieldType.TEXT,
            label_translations={"en": "Subject"},
            group=profile_group,
            is_active=True,
        )
        response = ProfileFieldResponse.objects.create(
            user=user,
            profile_field=text_field,
            value="Initial",
        )
        first_update = response.updated_datetime
        assert first_update is not None

        # Update and save
        response.value = "Updated"
        response.save()
        assert response.updated_datetime > first_update
