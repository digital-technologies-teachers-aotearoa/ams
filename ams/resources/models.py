from pathlib import Path

from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from ams.resources import file_types
from ams.resources.utils import resource_upload_path
from config.storage_backends import PrivateMediaStorage


class Resource(models.Model):
    name = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from="name", always_update=True, null=True)
    description = HTMLField()
    published = models.BooleanField(default=False)
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    # Maintained by Postgres triggers (see migration 0003).
    # Weights: name=A, description & component names=B, author user & entity names=C.
    search_vector = SearchVectorField(null=True, editable=False)
    author_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="resources",
        blank=True,
    )
    author_entities = models.ManyToManyField(
        "entities.Entity",
        related_name="resources",
        blank=True,
    )

    class Meta:
        ordering = ["-datetime_updated"]
        indexes = [
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "resources:resource",
            kwargs={"pk": self.pk, "slug": self.slug},
        )


class ResourceComponent(models.Model):
    DATA_FIELDS = ("component_url", "component_file", "component_resource")

    TYPE_OTHER = file_types.TYPE_OTHER
    TYPE_DOCUMENT = file_types.TYPE_DOCUMENT
    TYPE_PDF = file_types.TYPE_PDF
    TYPE_IMAGE = file_types.TYPE_IMAGE
    TYPE_SLIDESHOW = file_types.TYPE_SLIDESHOW
    TYPE_VIDEO = file_types.TYPE_VIDEO
    TYPE_WEBSITE = file_types.TYPE_WEBSITE
    TYPE_AUDIO = file_types.TYPE_AUDIO
    TYPE_ARCHIVE = file_types.TYPE_ARCHIVE
    TYPE_RESOURCE = file_types.TYPE_RESOURCE
    TYPE_SPREADSHEET = file_types.TYPE_SPREADSHEET

    name = models.CharField(max_length=300)
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="components",
    )
    component_type = models.PositiveSmallIntegerField(
        choices=file_types.COMPONENT_TYPE_CHOICES,
        default=file_types.TYPE_OTHER,
    )
    component_url = models.URLField(blank=True)
    component_file = models.FileField(
        null=True,
        blank=True,
        upload_to=resource_upload_path,
        storage=PrivateMediaStorage(),
    )
    component_resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="component_of",
        null=True,
        blank=True,
    )
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.component_url:
            self.component_type = file_types.detect_url_type(self.component_url)
        elif self.component_resource_id:
            self.component_type = file_types.TYPE_RESOURCE
        elif self.component_file:
            self.component_type = file_types.detect_file_type(self.component_file)
        else:
            self.component_type = file_types.TYPE_OTHER
        super().save(*args, **kwargs)

    def clean(self):
        data_count = sum(1 for field in self.DATA_FIELDS if getattr(self, field, None))
        if data_count != 1:
            raise ValidationError(
                _(
                    "Resource components must have exactly one type of data "
                    "(file, URL, or another resource).",
                ),
            )
        if (
            self.component_resource_id
            and self.component_resource_id == self.resource_id
        ):
            raise ValidationError(
                _("Cannot set a resource to be a component of itself."),
            )

    def filename(self):
        if self.component_file:
            return Path(self.component_file.name).name
        return None

    def icon_name(self):
        return file_types.COMPONENT_TYPE_DATA[self.component_type]["icon"]
