from django.core.files.storage import storages
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.documents.models import AbstractDocument
from wagtail.documents.models import Document


class AMSDocument(AbstractDocument):
    """Custom Document model that stores to private storage."""

    file = models.FileField(
        storage=storages["private"],
        upload_to="documents",
        verbose_name=_("file"),
    )

    admin_form_fields = Document.admin_form_fields
