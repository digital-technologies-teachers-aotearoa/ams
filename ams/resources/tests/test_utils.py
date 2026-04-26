from datetime import UTC
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import UUID

from ams.resources.utils import resource_upload_path

FIXED_UUID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
FIXED_DT = datetime(2026, 4, 26, 14, 30, 22, tzinfo=UTC)
FIXED_TS = "20260426-143022"


class TestResourceUploadPath:
    def _make_instance(self, pk, component_uuid=FIXED_UUID):
        instance = MagicMock()
        instance.resource.pk = pk
        instance.uuid = component_uuid
        return instance

    def test_returns_correct_path(self):
        instance = self._make_instance(42)
        with patch("ams.resources.utils.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_DT
            result = resource_upload_path(instance, "report.pdf")
        assert result == Path(f"resources/42/{FIXED_UUID}_{FIXED_TS}/report.pdf")

    def test_includes_filename_as_provided(self):
        instance = self._make_instance(7)
        with patch("ams.resources.utils.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_DT
            result = resource_upload_path(instance, "my document.docx")
        assert result == Path(f"resources/7/{FIXED_UUID}_{FIXED_TS}/my document.docx")

    def test_path_uses_resource_pk(self):
        instance = self._make_instance(999)
        with patch("ams.resources.utils.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_DT
            result = resource_upload_path(instance, "file.txt")
        assert str(result).startswith("resources/999/")

    def test_path_uses_component_uuid(self):
        other_uuid = UUID("11111111-2222-3333-4444-555555555555")
        instance = self._make_instance(42, component_uuid=other_uuid)
        with patch("ams.resources.utils.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_DT
            result = resource_upload_path(instance, "file.txt")
        assert f"{other_uuid}_" in str(result)

    def test_path_includes_timestamp(self):
        instance = self._make_instance(42)
        with patch("ams.resources.utils.datetime") as mock_dt:
            mock_dt.now.return_value = FIXED_DT
            result = resource_upload_path(instance, "file.txt")
        assert FIXED_TS in str(result)
