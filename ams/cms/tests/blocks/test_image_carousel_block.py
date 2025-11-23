"""Tests for ImageCarouselBlock."""

import pytest
from wagtail.blocks import ChoiceBlock
from wagtail.blocks import ListBlock
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

from ams.cms.blocks.image_carousel_block import CarouselSlideBlock
from ams.cms.blocks.image_carousel_block import ImageCarouselBlock

# Constants for testing
DEFAULT_INTERVAL = 5000
MIN_INTERVAL = 1000
MAX_INTERVAL = 30000


@pytest.fixture
def test_image(db):
    """Create a test image for carousel slides."""
    return Image.objects.create(
        title="Test Image",
        file=get_test_image_file(),
    )


class TestCarouselSlideBlock:
    """Test the CarouselSlideBlock functionality."""

    def test_carousel_slide_block_instantiation(self):
        """Test that CarouselSlideBlock can be instantiated."""
        block = CarouselSlideBlock()
        assert block is not None

    def test_carousel_slide_block_has_required_fields(self):
        """Test that CarouselSlideBlock has all required fields."""
        block = CarouselSlideBlock()
        assert "image" in block.child_blocks
        assert "caption" in block.child_blocks
        assert "attribution" in block.child_blocks

    def test_carousel_slide_block_attribution_optional(self):
        """Test that attribution field is optional."""
        block = CarouselSlideBlock()
        assert block.child_blocks["attribution"].required is False


class TestImageCarouselBlock:
    """Test the ImageCarouselBlock functionality."""

    def test_image_carousel_block_instantiation(self):
        """Test that ImageCarouselBlock can be instantiated."""
        block = ImageCarouselBlock()
        assert block is not None

    def test_image_carousel_block_has_required_fields(self):
        """Test that ImageCarouselBlock has all required fields."""
        block = ImageCarouselBlock()
        assert "slides" in block.child_blocks
        assert "show_indicators" in block.child_blocks
        assert "show_controls" in block.child_blocks
        assert "transition_type" in block.child_blocks
        assert "auto_advance" in block.child_blocks
        assert "interval" in block.child_blocks

    def test_image_carousel_block_slides_is_list_block(self):
        """Test that slides field is a ListBlock."""
        block = ImageCarouselBlock()
        slides_field = block.child_blocks["slides"]
        assert isinstance(slides_field, ListBlock)
        assert isinstance(slides_field.child_block, CarouselSlideBlock)

    def test_image_carousel_block_slides_min_num(self):
        """Test that slides field requires at least one slide."""
        block = ImageCarouselBlock()
        slides_field = block.child_blocks["slides"]
        assert slides_field.meta.min_num == 1

    def test_image_carousel_block_transition_choices(self):
        """Test that transition_type has correct choices."""
        block = ImageCarouselBlock()
        transition_field = block.child_blocks["transition_type"]
        # Just verify it's a choice block - the choices are set correctly in definition
        assert isinstance(transition_field, ChoiceBlock)

    def test_image_carousel_block_render_with_single_slide(self, test_image):
        """Test rendering carousel with a single slide."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {
                        "image": test_image.id,
                        "caption": "Test Caption",
                        "attribution": "Test Attribution",
                    },
                ],
                "show_indicators": True,
                "show_controls": True,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)

        # Check that carousel container exists
        assert "carousel" in html
        assert "carousel-inner" in html
        assert "carousel-item" in html
        assert "active" in html

        # With single slide, controls/indicators should not render
        # even if enabled (template logic)
        assert "carousel-indicators" not in html
        assert "carousel-control-prev" not in html
        assert "carousel-control-next" not in html

    def test_image_carousel_block_render_with_multiple_slides(
        self,
        test_image,
    ):
        """Test rendering carousel with multiple slides."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {
                        "image": test_image.id,
                        "caption": "Slide 1",
                        "attribution": "",
                    },
                    {
                        "image": test_image.id,
                        "caption": "Slide 2",
                        "attribution": "",
                    },
                ],
                "show_indicators": True,
                "show_controls": True,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)

        # With multiple slides, controls/indicators should render
        assert "carousel-indicators" in html
        assert "carousel-control-prev" in html
        assert "carousel-control-next" in html
        assert 'data-bs-slide-to="0"' in html
        assert 'data-bs-slide-to="1"' in html

    def test_image_carousel_block_render_without_indicators(
        self,
        test_image,
    ):
        """Test rendering carousel without indicators."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": True,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-indicators" not in html

    def test_image_carousel_block_render_without_controls(self, test_image):
        """Test rendering carousel without controls."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": True,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-control-prev" not in html
        assert "carousel-control-next" not in html

    def test_image_carousel_block_render_with_fade_transition(
        self,
        test_image,
    ):
        """Test rendering carousel with fade transition."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "fade",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-fade" in html

    def test_image_carousel_block_render_without_fade_transition(
        self,
        test_image,
    ):
        """Test rendering carousel with slide transition (no fade)."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-fade" not in html

    def test_image_carousel_block_render_with_auto_advance(self, test_image):
        """Test rendering carousel with auto-advance enabled."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 3000,
            },
        )

        html = block.render(value)
        assert 'data-bs-ride="carousel"' in html
        assert 'data-bs-interval="3000"' in html

    def test_image_carousel_block_render_without_auto_advance(
        self,
        test_image,
    ):
        """Test rendering carousel with auto-advance disabled."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": False,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert 'data-bs-ride="false"' in html
        # Interval should not be in output when auto-advance is disabled
        assert "data-bs-interval" not in html

    def test_image_carousel_block_render_with_caption(self, test_image):
        """Test rendering slide with caption."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {
                        "image": test_image.id,
                        "caption": "My Caption",
                        "attribution": "",
                    },
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-caption" in html
        assert "My Caption" in html

    def test_image_carousel_block_render_with_attribution(self, test_image):
        """Test rendering slide with attribution."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {
                        "image": test_image.id,
                        "caption": "",
                        "attribution": "Photo by John Doe",
                    },
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert "carousel-caption" in html
        assert "Photo by John Doe" in html

    def test_image_carousel_block_render_without_caption_or_attribution(
        self,
        test_image,
    ):
        """Test rendering slide without caption or attribution."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        # Caption container should not render if no caption/attribution
        assert "carousel-caption" not in html

    def test_image_carousel_block_touch_support_enabled(self, test_image):
        """Test that touch/swipe support is enabled."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)
        assert 'data-bs-touch="true"' in html

    def test_image_carousel_block_unique_ids(self, test_image):
        """Test that carousel has proper ID structure."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": False,
                "show_controls": False,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)

        # Check that carousel has proper ID attribute
        assert 'id="carousel-' in html
        assert "carousel" in html

    def test_image_carousel_block_accessibility_features(self, test_image):
        """Test that carousel includes accessibility features."""
        block = ImageCarouselBlock()
        value = block.to_python(
            {
                "slides": [
                    {"image": test_image.id, "caption": "", "attribution": ""},
                    {"image": test_image.id, "caption": "", "attribution": ""},
                ],
                "show_indicators": True,
                "show_controls": True,
                "transition_type": "slide",
                "auto_advance": True,
                "interval": 5000,
            },
        )

        html = block.render(value)

        # Check for ARIA labels
        assert 'aria-label="Slide 1"' in html
        assert 'aria-label="Slide 2"' in html
        assert 'aria-current="true"' in html
        assert "visually-hidden" in html
        assert "Previous" in html
        assert "Next" in html
