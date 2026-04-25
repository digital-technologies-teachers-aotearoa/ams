from unittest.mock import patch

import pytest
from django.core.files.storage import InMemoryStorage

from ams.resources.models import ResourceComponent


@pytest.fixture
def file_storage():
    storage = InMemoryStorage(location="", base_url="/private-media/")
    with patch.object(
        ResourceComponent._meta.get_field("component_file"),  # noqa: SLF001
        "storage",
        storage,
    ):
        yield storage
