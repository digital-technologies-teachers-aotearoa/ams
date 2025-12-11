import pytest
from django.template import Context
from django.template import Template
from django.template import TemplateDoesNotExist


@pytest.mark.django_db
class TestIconTemplateTag:
    """Tests for the icon template tag."""

    def test_icon_without_classes(self):
        """Test that icon renders correctly without additional classes."""
        template = Template("{% load icon %}{% icon 'person-fill' %}")
        result = template.render(Context({}))

        assert "<svg" in result
        assert "bi-person-fill" in result
        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert isinstance(result, str)
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_with_single_class(self):
        """Test that icon renders correctly with a single additional class."""
        template = Template("{% load icon %}{% icon 'person-fill' 'icon-lg' %}")
        result = template.render(Context({}))

        assert "<svg" in result
        assert "bi-person-fill icon-lg" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result
        assert "&quot;" not in result

    def test_icon_with_multiple_classes(self):
        """Test that icon renders correctly with multiple additional classes."""
        template = Template(
            "{% load icon %}{% icon 'person-fill' 'icon-lg text-primary' %}",
        )
        result = template.render(Context({}))

        assert "<svg" in result
        assert "bi-person-fill icon-lg text-primary" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_with_hyphenated_classes(self):
        """Test that icon handles hyphenated class names correctly."""
        template = Template(
            "{% load icon %}{% icon 'person-fill' 'my-custom-class another-class' %}",
        )
        result = template.render(Context({}))

        assert "<svg" in result
        assert "my-custom-class another-class" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_with_invalid_classes_rejected(self):
        """Test that invalid class names are rejected for security."""
        # Classes with special characters should be rejected
        template = Template(
            "{% load icon %}{% icon 'person-fill' 'class<script>alert(1)</script>' %}",
        )
        result = template.render(Context({}))

        assert "<svg" in result
        # Invalid classes should not be added
        assert "script" not in result
        # But the icon should still render with original classes
        assert "bi-person-fill" in result

    def test_icon_with_quotes_in_classes_rejected(self):
        """Test that class names with quotes are rejected."""
        template = Template(
            "{% load icon %}{% icon 'person-fill' 'class\" onload=\"alert(1)' %}",
        )
        result = template.render(Context({}))

        assert "<svg" in result
        # Invalid classes should not be added
        assert "onload" not in result
        # But the icon should still render with original classes
        assert "bi-person-fill" in result

    def test_icon_with_empty_class_string(self):
        """Test that icon handles empty class string correctly."""
        template = Template("{% load icon %}{% icon 'person-fill' '' %}")
        result = template.render(Context({}))

        assert "<svg" in result
        assert "bi-person-fill" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_returns_safe_string(self):
        """Test that icon returns a SafeString to prevent auto-escaping."""
        template = Template("{% load icon %}{% icon 'person-fill' %}")
        result = template.render(Context({}))

        # The result should be rendered as HTML, not escaped
        assert "<svg" in result
        assert "&lt;" not in result

    def test_icon_returns_safe_string_with_classes(self):
        """Test that icon returns a SafeString even when classes are added."""
        template = Template("{% load icon %}{% icon 'person-fill' 'custom-class' %}")
        result = template.render(Context({}))

        # The result should be rendered as HTML, not escaped
        assert "<svg" in result
        assert "custom-class" in result
        assert "&lt;" not in result
        assert "&quot;" not in result

    def test_icon_preserves_svg_attributes(self):
        """Test that icon preserves all SVG attributes."""
        template = Template("{% load icon %}{% icon 'person-fill' 'extra-class' %}")
        result = template.render(Context({}))

        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert 'width="16"' in result
        assert 'height="16"' in result
        assert 'fill="currentColor"' in result
        assert 'viewBox="0 0 16 16"' in result

    def test_icon_with_numeric_classes(self):
        """Test that icon handles numeric class names."""
        template = Template("{% load icon %}{% icon 'person-fill' 'w-100 h-50' %}")
        result = template.render(Context({}))

        assert "<svg" in result
        assert "w-100 h-50" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_with_underscores_in_classes(self):
        """Test that icon handles underscores in class names."""
        template = Template("{% load icon %}{% icon 'person-fill' 'my_custom_class' %}")
        result = template.render(Context({}))

        assert "<svg" in result
        assert "my_custom_class" in result
        # Should not be HTML-escaped
        assert "&lt;svg" not in result

    def test_icon_nonexistent_icon_raises_error(self):
        """Test that requesting a nonexistent icon raises an error."""
        template = Template("{% load icon %}{% icon 'nonexistent-icon' %}")

        with pytest.raises(TemplateDoesNotExist):
            template.render(Context({}))
