"""Pytest tests ensuring reserved paths remain consistent across the project."""

from pathlib import Path

from django.conf import settings

import ams.utils.middleware.site_by_path as mw
from ams.cms import models
from ams.utils.reserved_paths import get_reserved_paths_list
from ams.utils.reserved_paths import get_reserved_paths_set


def test_reserved_paths_extracted_from_urls():
    reserved_paths = get_reserved_paths_set()
    expected_paths = {"billing", "cms", "forum", "users", "accounts", "admin"}
    for path in expected_paths:
        assert path in reserved_paths, f"Expected '{path}' to be in reserved paths"


def test_reserved_paths_functions():
    paths_list = get_reserved_paths_list()
    paths_set = get_reserved_paths_set()
    assert paths_list
    assert paths_set
    assert set(paths_list) == paths_set


def test_cms_models_uses_function():
    assert hasattr(models, "ContentPage")
    assert not hasattr(models, "RESERVED_URL_SLUGS")


def test_middleware_uses_function():
    assert hasattr(mw, "get_reserved_paths_set")


def test_no_hardcoded_reserved_paths_in_urls():
    content = Path("/app/config/urls.py").read_text(encoding="utf-8")
    assert "from ams.utils.reserved_paths import RESERVED_PATHS" not in content


def test_admin_url_included_in_reserved_paths():
    reserved_paths = get_reserved_paths_set()
    admin_url_segment = settings.ADMIN_URL.strip("/").split("/")[0]
    assert admin_url_segment in reserved_paths, (
        f"Expected admin URL segment '{admin_url_segment}' to be in reserved paths"
    )
