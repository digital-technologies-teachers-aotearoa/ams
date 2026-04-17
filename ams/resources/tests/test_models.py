from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from ams.resources import file_types
from ams.resources.models import ResourceCategory
from ams.resources.models import ResourceComponent
from ams.resources.models import ResourceTag
from ams.resources.tests.factories import ResourceCategoryFactory
from ams.resources.tests.factories import ResourceComponentFactory
from ams.resources.tests.factories import ResourceFactory
from ams.resources.tests.factories import ResourceTagFactory
from config.storage_backends import PrivateMediaStorage

pytestmark = pytest.mark.django_db


class TestResourceCategoryModel:
    def test_str_returns_name(self):
        category = ResourceCategoryFactory(name="Year Level")
        assert str(category) == "Year Level"

    def test_ordering_by_order_then_name(self):
        b = ResourceCategoryFactory(name="B Category", order=2)
        a = ResourceCategoryFactory(name="A Category", order=1)
        c = ResourceCategoryFactory(name="C Category", order=1)
        qs = list(ResourceCategory.objects.all())
        assert qs.index(a) < qs.index(b)
        assert qs.index(c) < qs.index(b)


class TestResourceTagModel:
    def test_str_returns_name(self):
        tag = ResourceTagFactory(name="Level 1")
        assert str(tag) == "Level 1"

    def test_same_slug_allowed_in_different_categories(self):
        cat_a = ResourceCategoryFactory(name="Category A")
        cat_b = ResourceCategoryFactory(name="Category B")
        tag_a = ResourceTagFactory(name="duplicate", category=cat_a)
        tag_b = ResourceTagFactory(name="duplicate", category=cat_b)
        assert tag_a.slug == tag_b.slug

    def test_ordering_by_order_then_name(self):
        category = ResourceCategoryFactory()
        b = ResourceTagFactory(name="B Tag", order=2, category=category)
        a = ResourceTagFactory(name="A Tag", order=1, category=category)
        qs = list(ResourceTag.objects.filter(category=category))
        assert qs.index(a) < qs.index(b)


class TestResourceTagsM2M:
    def test_resource_can_have_tags(self):
        resource = ResourceFactory()
        tag = ResourceTagFactory()
        resource.tags.add(tag)
        assert tag in resource.tags.all()

    def test_tag_resources_reverse_relation(self):
        resource = ResourceFactory()
        tag = ResourceTagFactory()
        resource.tags.add(tag)
        assert resource in tag.resources.all()


class TestResourceModel:
    def test_str_returns_name(self):
        resource = ResourceFactory(name="Test Resource")
        assert str(resource) == "Test Resource"

    def test_slug_is_generated_from_name(self):
        resource = ResourceFactory(name="Some Useful Resource")
        assert resource.slug == "some-useful-resource"

    def test_get_absolute_url_contains_pk_and_slug(self):
        resource = ResourceFactory(name="Example Title")
        url = resource.get_absolute_url()
        assert str(resource.pk) in url
        assert "example-title" in url

    def test_default_ordering_is_datetime_updated_descending(self):
        older = ResourceFactory()
        newer = ResourceFactory()
        # Touch newer so its datetime_updated is later
        newer.save()
        qs = list(type(older).objects.all())
        assert qs[0] == newer
        assert qs[1] == older


class TestResourceComponentModel:
    def test_str_returns_name(self):
        component = ResourceComponentFactory.build(name="My Component")
        assert str(component) == "My Component"

    def test_save_with_no_data_sets_type_other(self):
        resource = ResourceFactory()
        component = ResourceComponent(name="c", resource=resource)
        # Bypass clean() to test save() directly
        component.component_url = ""
        component.component_file = None
        component.component_resource = None
        component.save()
        assert component.component_type == file_types.TYPE_OTHER


class TestResourceComponentClean:
    def test_clean_rejects_no_data_fields(self):
        resource = ResourceFactory()
        component = ResourceComponent(name="c", resource=resource)
        with pytest.raises(ValidationError):
            component.clean()

    def test_clean_rejects_multiple_data_fields(self):
        resource = ResourceFactory()
        other = ResourceFactory()
        component = ResourceComponent(
            name="c",
            resource=resource,
            component_url="https://example.com",
            component_resource=other,
        )
        with pytest.raises(ValidationError):
            component.clean()

    def test_clean_accepts_url_only(self):
        resource = ResourceFactory()
        component = ResourceComponent(
            name="c",
            resource=resource,
            component_url="https://example.com",
        )
        component.clean()

    def test_clean_accepts_resource_only(self):
        resource = ResourceFactory()
        other = ResourceFactory()
        component = ResourceComponent(
            name="c",
            resource=resource,
            component_resource=other,
        )
        component.clean()

    def test_clean_rejects_self_reference(self):
        resource = ResourceFactory()
        resource.save()
        component = ResourceComponent(
            name="c",
            resource=resource,
            component_resource=resource,
        )
        with pytest.raises(ValidationError):
            component.clean()


class TestResourceComponentTypeDetection:
    def _save_with_file(self, filename, content=b"data"):
        resource = ResourceFactory()
        component = ResourceComponent(name="c", resource=resource)
        component.component_file = SimpleUploadedFile(filename, content)
        with patch(
            "config.storage_backends.PrivateMediaStorage.save",
            return_value=f"resources/{resource.pk}/{filename}",
        ):
            component.save()
        return component

    def _save_with_url(self, url):
        resource = ResourceFactory()
        component = ResourceComponent(name="c", resource=resource, component_url=url)
        component.save()
        return component

    def test_pdf_file_detected_as_pdf(self):
        component = self._save_with_file("doc.pdf")
        assert component.component_type == file_types.TYPE_PDF

    def test_docx_file_detected_as_document(self):
        component = self._save_with_file("notes.docx")
        assert component.component_type == file_types.TYPE_DOCUMENT

    def test_youtube_url_detected_as_video(self):
        component = self._save_with_url("https://www.youtube.com/watch?v=abc123")
        assert component.component_type == file_types.TYPE_VIDEO

    def test_vimeo_url_detected_as_video(self):
        component = self._save_with_url("https://vimeo.com/12345")
        assert component.component_type == file_types.TYPE_VIDEO

    def test_google_drive_document_detected_as_document(self):
        component = self._save_with_url(
            "https://docs.google.com/document/d/abc123/edit",
        )
        assert component.component_type == file_types.TYPE_DOCUMENT

    def test_google_drive_spreadsheet_detected_as_spreadsheet(self):
        component = self._save_with_url(
            "https://docs.google.com/spreadsheets/d/abc123/edit",
        )
        assert component.component_type == file_types.TYPE_SPREADSHEET

    def test_google_drive_presentation_detected_as_slideshow(self):
        component = self._save_with_url(
            "https://docs.google.com/presentation/d/abc123/edit",
        )
        assert component.component_type == file_types.TYPE_SLIDESHOW

    def test_arbitrary_url_detected_as_website(self):
        component = self._save_with_url("https://example.org/something")
        assert component.component_type == file_types.TYPE_WEBSITE

    def test_component_resource_detected_as_resource(self):
        resource = ResourceFactory()
        other = ResourceFactory()
        component = ResourceComponent(
            name="c",
            resource=resource,
            component_resource=other,
        )
        component.save()
        assert component.component_type == file_types.TYPE_RESOURCE


class TestResourceComponentStorage:
    def test_component_file_uses_private_storage(self):
        field = ResourceComponent._meta.get_field("component_file")  # noqa: SLF001
        assert isinstance(field.storage, PrivateMediaStorage)


class TestResourceComponentHelpers:
    def test_filename_returns_basename(self):
        component = ResourceComponentFactory.build()
        component.component_file = SimpleUploadedFile("doc.pdf", b"data")
        component.component_url = ""
        assert component.filename() == "doc.pdf"

    def test_filename_returns_basename_when_stored_under_subpath(self):
        component = ResourceComponentFactory.build()
        component.component_file = SimpleUploadedFile("resources/42/doc.pdf", b"data")
        component.component_url = ""
        assert component.filename() == "doc.pdf"

    def test_filename_returns_none_without_file(self):
        component = ResourceComponentFactory.build()
        assert component.filename() is None

    def test_icon_name_returns_icon_for_component_type(self):
        component = ResourceComponent(component_type=file_types.TYPE_PDF)
        assert component.icon_name() == "file-earmark-pdf"

    def test_icon_name_for_video(self):
        component = ResourceComponent(component_type=file_types.TYPE_VIDEO)
        assert component.icon_name() == "file-earmark-play"

    def test_icon_name_for_website(self):
        component = ResourceComponent(component_type=file_types.TYPE_WEBSITE)
        assert component.icon_name() == "globe2"

    def test_icon_name_for_resource(self):
        component = ResourceComponent(component_type=file_types.TYPE_RESOURCE)
        assert component.icon_name() == "folder-symlink"
