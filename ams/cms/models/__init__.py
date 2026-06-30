"""CMS models - organized into logical modules for better maintainability.

This module re-exports all models to maintain backward compatibility with
existing code that imports from ams.cms.models.
"""

# Contact form models
from ams.cms.models.contact import ContactFormSubmission

# Page models
# Document models
from ams.cms.models.documents import AMSDocument
from ams.cms.models.pages import ArticlePage
from ams.cms.models.pages import ArticlesIndexPage
from ams.cms.models.pages import ContentPage
from ams.cms.models.pages import HomePage

# Settings models
from ams.cms.models.settings import AssociationSettings
from ams.cms.models.settings import SiteSettings

# Theme models
from ams.cms.models.theme import ThemeSettings
from ams.cms.models.theme import ThemeSettingsRevision

__all__ = [
    "AMSDocument",
    "ArticlePage",
    "ArticlesIndexPage",
    "AssociationSettings",
    "ContactFormSubmission",
    "ContentPage",
    "HomePage",
    "SiteSettings",
    "ThemeSettings",
    "ThemeSettingsRevision",
]
