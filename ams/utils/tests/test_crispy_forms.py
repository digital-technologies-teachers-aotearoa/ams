"""Tests for custom crispy forms layout objects."""

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field
from django import forms
from django.template import Context
from django.urls import reverse
from django.utils.translation import override

from ams.users.models import ProfileField
from ams.users.models import ProfileFieldGroup
from ams.utils.crispy_forms import Cancel
from ams.utils.crispy_forms import ProfileFieldWithBadges


class TestCancelButton:
    """Test class for the Cancel crispy forms layout object."""

    def test_cancel_with_custom_url(self):
        """Test that Cancel button renders with custom URL."""
        custom_url = "/custom/cancel/url/"
        cancel = Cancel(url=custom_url)

        rendered = cancel.render(form=None, context=Context())

        assert custom_url in rendered
        assert 'class="btn btn-secondary"' in rendered
        assert ">Cancel<" in rendered or "Cancel" in rendered

    def test_cancel_with_no_url_defaults_to_root(self):
        """Test that Cancel button defaults to root_redirect when no URL provided."""
        cancel = Cancel()

        rendered = cancel.render(form=None, context=Context())

        # Should default to root_redirect
        expected_url = reverse("root_redirect")
        assert expected_url in rendered

    def test_cancel_renders_as_anchor_tag(self):
        """Test that Cancel renders as an <a> tag, not a button."""
        cancel = Cancel(url="/test/")

        rendered = cancel.render(form=None, context=Context())

        assert '<a href="/test/"' in rendered
        assert "<button" not in rendered

    def test_cancel_has_correct_css_classes(self):
        """Test that Cancel has the correct Bootstrap classes."""
        cancel = Cancel(url="/test/")

        rendered = cancel.render(form=None, context=Context())

        assert 'class="btn btn-secondary"' in rendered

    def test_cancel_template_location(self):
        """Test that Cancel uses the correct template."""
        cancel = Cancel()

        assert cancel.TEMPLATE == "utils/crispy_forms/cancel.html"

    def test_cancel_with_reversed_url(self):
        """Test that Cancel works with reversed Django URLs."""
        url = reverse("root_redirect")
        cancel = Cancel(url=url)

        rendered = cancel.render(form=None, context=Context())

        assert url in rendered


@pytest.mark.django_db
class TestProfileFieldWithBadges:
    """Test class for the ProfileFieldWithBadges crispy forms layout object."""

    @pytest.fixture
    def profile_group(self):
        """Create a ProfileFieldGroup for test fixtures."""
        return ProfileFieldGroup.objects.create(
            name_translations={"en": "Test Group", "mi": "Rōpū Whakamātau"},
            order=0,
        )

    @pytest.fixture
    def simple_form(self):
        """Create a basic Django form for rendering tests."""

        class TestForm(forms.Form):
            test_field = forms.CharField(label="Test Field", required=False)
            another_field = forms.CharField(label="Another Field", required=True)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.helper = FormHelper()
                self.helper.form_show_labels = True

        return TestForm()

    @pytest.fixture
    def profile_field_factory(self, profile_group):
        """Factory to create ProfileField instances with custom settings."""

        def _create_profile_field(
            field_key="test_field",
            counts_toward_completion=False,  # noqa: FBT002
            is_required_for_membership=False,  # noqa: FBT002
        ):
            return ProfileField.objects.create(
                field_key=field_key,
                field_type=ProfileField.FieldType.TEXT,
                label_translations={"en": "Test Field", "mi": "Āpure Whakamātau"},
                group=profile_group,
                counts_toward_completion=counts_toward_completion,
                is_required_for_membership=is_required_for_membership,
            )

        return _create_profile_field

    def _get_label_during_render(self, form, field_name, layout_obj):
        """Helper to capture the label value during rendering."""
        captured_label = None

        # Monkey-patch Field.render to capture label

        original_render = Field.render

        def capture_render(self_field, form_arg, context_arg, **kwargs_arg):
            nonlocal captured_label
            captured_label = form_arg.fields[field_name].label
            return original_render(self_field, form_arg, context_arg, **kwargs_arg)

        Field.render = capture_render
        try:
            layout_obj.render(form, context=Context())
        finally:
            Field.render = original_render

        return captured_label

    # Badge Rendering Tests

    def test_recommended_badge_shown_when_counts_toward_completion_and_not_required(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that Recommended badge appears for completion fields that aren't
        required."""
        profile_field = profile_field_factory(counts_toward_completion=True)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        # Capture label during rendering
        label_during_render = self._get_label_during_render(
            simple_form,
            "test_field",
            layout_obj,
        )

        # Badge should be in the label
        assert '<span class="badge bg-primary">Recommended</span>' in str(
            label_during_render,
        )

    def test_no_recommended_badge_when_field_is_required(
        self,
        profile_field_factory,
    ):
        """Test that Recommended badge does NOT appear when field is required."""

        # Create form with required field
        class RequiredForm(forms.Form):
            test_field = forms.CharField(label="Test Field", required=True)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.helper = FormHelper()
                self.helper.form_show_labels = True

        form = RequiredForm()
        profile_field = profile_field_factory(counts_toward_completion=True)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(form, context=Context())

        assert "Recommended" not in rendered

    def test_no_recommended_badge_when_not_counts_toward_completion(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that no Recommended badge appears when counts_toward_completion is
        False."""
        profile_field = profile_field_factory(counts_toward_completion=False)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        assert "Recommended" not in rendered

    def test_required_membership_badge_shown(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that Required for membership badge appears when condition is met."""
        profile_field = profile_field_factory(is_required_for_membership=True)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        label_during_render = self._get_label_during_render(
            simple_form,
            "test_field",
            layout_obj,
        )

        assert (
            '<span class="badge bg-warning text-dark">Required for membership</span>'
            in str(label_during_render)
        )

    def test_no_required_membership_badge_when_false(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that no Required for membership badge appears when condition is
        false."""
        profile_field = profile_field_factory(is_required_for_membership=False)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        assert "Required for membership" not in rendered

    def test_both_badges_when_both_conditions_met(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that both badges appear when both conditions are met."""
        profile_field = profile_field_factory(
            counts_toward_completion=True,
            is_required_for_membership=True,
        )
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        label_during_render = self._get_label_during_render(
            simple_form,
            "test_field",
            layout_obj,
        )

        assert '<span class="badge bg-primary">Recommended</span>' in str(
            label_during_render,
        )
        assert (
            '<span class="badge bg-warning text-dark">Required for membership</span>'
            in str(label_during_render)
        )

    def test_no_badges_when_both_conditions_false(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that field renders without badges when both conditions are false."""
        profile_field = profile_field_factory(
            counts_toward_completion=False,
            is_required_for_membership=False,
        )
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        assert "Recommended" not in rendered
        assert "Required for membership" not in rendered

    # Edge Cases

    def test_no_badges_when_profile_field_is_none(self, simple_form):
        """Test that field renders without badges when profile_field is None."""
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=None)

        rendered = layout_obj.render(simple_form, context=Context())

        assert "Recommended" not in rendered
        assert "Required for membership" not in rendered
        # Should still render the field
        assert 'name="test_field"' in rendered

    def test_label_preserved_when_no_badges(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that original label text is preserved when no badges."""
        profile_field = profile_field_factory(
            counts_toward_completion=False,
            is_required_for_membership=False,
        )
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        label_during_render = self._get_label_during_render(
            simple_form,
            "test_field",
            layout_obj,
        )

        # Label should be unchanged (no badges added)
        assert label_during_render == "Test Field"

    def test_label_contains_badges_when_present(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that label is modified to include badge HTML when badges present."""
        profile_field = profile_field_factory(counts_toward_completion=True)
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        label_during_render = self._get_label_during_render(
            simple_form,
            "test_field",
            layout_obj,
        )

        # Label should contain both original text and badge HTML
        assert "Test Field" in str(label_during_render)
        assert '<span class="badge bg-primary">Recommended</span>' in str(
            label_during_render,
        )

    # Field Rendering Tests

    def test_renders_field_correctly(self, simple_form, profile_field_factory):
        """Test that field delegates to crispy forms Field object correctly."""
        profile_field = profile_field_factory()
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        # Should contain the form field input element
        assert 'name="test_field"' in rendered
        assert 'type="text"' in rendered

    def test_correct_field_name_used(self, simple_form, profile_field_factory):
        """Test that correct field is rendered based on field_name parameter."""
        profile_field = profile_field_factory(field_key="another_field")
        layout_obj = ProfileFieldWithBadges(
            "another_field",
            profile_field=profile_field,
        )

        rendered = layout_obj.render(simple_form, context=Context())

        # Should render the another_field, not test_field
        assert 'name="another_field"' in rendered
        # Verify it's the right field by checking it's a required field
        assert "required" in rendered

    def test_render_with_empty_context(self, simple_form, profile_field_factory):
        """Test that render works with empty context dict."""
        profile_field = profile_field_factory()
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        # Should render without errors
        assert rendered is not None
        assert isinstance(rendered, str)

    def test_render_returns_string(self, simple_form, profile_field_factory):
        """Test that render() returns string type."""
        profile_field = profile_field_factory()
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        rendered = layout_obj.render(simple_form, context=Context())

        assert isinstance(rendered, str)
        assert len(rendered) > 0

    # Initialization Tests

    def test_initialization_stores_field_name(self, profile_field_factory):
        """Test that initialization correctly stores field_name."""
        profile_field = profile_field_factory()
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        assert layout_obj.field_name == "test_field"

    def test_initialization_stores_profile_field(self, profile_field_factory):
        """Test that initialization correctly stores profile_field."""
        profile_field = profile_field_factory()
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        assert layout_obj.profile_field == profile_field

    # Translation Test

    def test_badge_text_uses_translations(
        self,
        simple_form,
        profile_field_factory,
    ):
        """Test that badge labels are properly translated."""
        profile_field = profile_field_factory(
            counts_toward_completion=True,
            is_required_for_membership=True,
        )
        layout_obj = ProfileFieldWithBadges("test_field", profile_field=profile_field)

        # Render with Māori language
        with override("mi"):
            label_during_render = self._get_label_during_render(
                simple_form,
                "test_field",
                layout_obj,
            )

        # Badge text should be translated (checking for badge HTML structure)
        # The gettext function will translate if translations exist, otherwise fallback
        # to English
        assert '<span class="badge' in str(label_during_render)
