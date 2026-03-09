import pytest
from wagtail.models import Page
from wagtail.models import Site


@pytest.fixture(autouse=True)
def wagtail_site(db):
    """Ensure a Wagtail Site exists for template rendering."""
    root_page = Page.objects.filter(depth=1).first()
    if not root_page:
        root_page = Page.add_root(title="Root", slug="root")
    site, _ = Site.objects.get_or_create(
        is_default_site=True,
        defaults={
            "hostname": "localhost",
            "root_page": root_page,
        },
    )
    return site
