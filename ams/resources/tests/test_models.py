from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from ams.resources import file_types
from ams.resources.models import ResourceComponent
from ams.resources.tests.factories import ResourceComponentFactory
from ams.resources.tests.factories import ResourceFactory
from config.storage_backends import PrivateMediaStorage

pytestmark = pytest.mark.django_db


class TestResourceModel:
    def test_str_returns_name(self):
        resource = ResourceFactory(name="Test Resource")
        assert str(resource) == "Test Resource"

    def test_slug_is_generated_from_name(self):
        resource = ResourceFactory(name="Some Useful Resource")
        assert resource.slug == "some-useful-resource"

    @pytest.mark.skip(reason="Not implemented yet")
    def test_get_absolute_url_contains_pk_and_slug(self):
        resource = ResourceFactory(name="Example Title")
        url = resource.get_absolute_url()
        assert str(resource.pk) in url
        assert "example-title" in url


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

    def test_filename_returns_none_without_file(self):
        component = ResourceComponentFactory.build()
        assert component.filename() is None

    def test_icon_name_returns_icon_for_component_type(self):
        component = ResourceComponent(component_type=file_types.TYPE_PDF)
        assert component.icon_name() == "file-earmark-pdf"
