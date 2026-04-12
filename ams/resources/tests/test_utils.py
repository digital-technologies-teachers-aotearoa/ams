from pathlib import Path
from unittest.mock import MagicMock

from ams.resources.utils import resource_upload_path


class TestResourceUploadPath:
    def _make_instance(self, pk):
        instance = MagicMock()
        instance.resource.pk = pk
        return instance

    def test_returns_correct_path(self):
        instance = self._make_instance(42)
        result = resource_upload_path(instance, "report.pdf")
        assert result == Path("resources/42/report.pdf")

    def test_includes_filename_as_provided(self):
        instance = self._make_instance(7)
        result = resource_upload_path(instance, "my document.docx")
        assert result == Path("resources/7/my document.docx")

    def test_path_uses_resource_pk(self):
        instance = self._make_instance(999)
        result = resource_upload_path(instance, "file.txt")
        assert str(result).startswith("resources/999/")
