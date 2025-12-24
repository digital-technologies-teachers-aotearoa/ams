"""Tests for custom crispy forms layout objects."""

from django.urls import reverse

from ams.utils.crispy_forms import Cancel


class TestCancelButton:
    """Test class for the Cancel crispy forms layout object."""

    def test_cancel_with_custom_url(self):
        """Test that Cancel button renders with custom URL."""
        custom_url = "/custom/cancel/url/"
        cancel = Cancel(url=custom_url)

        rendered = cancel.render(form=None, context={})

        assert custom_url in rendered
        assert 'class="btn btn-secondary"' in rendered
        assert ">Cancel<" in rendered or "Cancel" in rendered

    def test_cancel_with_no_url_defaults_to_root(self):
        """Test that Cancel button defaults to root_redirect when no URL provided."""
        cancel = Cancel()

        rendered = cancel.render(form=None, context={})

        # Should default to root_redirect
        expected_url = reverse("root_redirect")
        assert expected_url in rendered

    def test_cancel_renders_as_anchor_tag(self):
        """Test that Cancel renders as an <a> tag, not a button."""
        cancel = Cancel(url="/test/")

        rendered = cancel.render(form=None, context={})

        assert '<a href="/test/"' in rendered
        assert "<button" not in rendered

    def test_cancel_has_correct_css_classes(self):
        """Test that Cancel has the correct Bootstrap classes."""
        cancel = Cancel(url="/test/")

        rendered = cancel.render(form=None, context={})

        assert 'class="btn btn-secondary"' in rendered

    def test_cancel_template_location(self):
        """Test that Cancel uses the correct template."""
        cancel = Cancel()

        assert cancel.TEMPLATE == "utils/crispy_forms/cancel.html"

    def test_cancel_with_reversed_url(self):
        """Test that Cancel works with reversed Django URLs."""
        url = reverse("root_redirect")
        cancel = Cancel(url=url)

        rendered = cancel.render(form=None, context={})

        assert url in rendered
