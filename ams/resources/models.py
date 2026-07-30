from pathlib import Path
from uuid import uuid4

from autoslug import AutoSlugField
from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from imagekit.processors import ResizeToFit
from tinymce.models import HTMLField

from ams.resources import file_types
from ams.resources.utils import resource_thumbnail_path
from ams.resources.utils import resource_upload_path
from ams.users.models import get_public_media_storage
from ams.utils.colours import contrast_colour
from ams.utils.colours import darken
from ams.utils.colours import interpolate_colour
from config.storage_backends import PrivateMediaStorage


class ResourceCategory(models.Model):
    class TagStyle(models.TextChoices):
        SOLID = "solid", _("Solid — filled badge")
        OUTLINE = "outline", _("Outline — bordered badge")
        SOFT = "soft", _("Soft — tinted background")

    name = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from="_slug_source")
    order = models.PositiveIntegerField(default=0)
    gradient_start_colour = ColorField(
        blank=True,
        default="",
        verbose_name=_("gradient start colour"),
        help_text=_(
            "Colour for the first tag (by order). Leave blank to disable "
            "automatic colouring for this category's tags.",
        ),
    )
    gradient_end_colour = ColorField(
        blank=True,
        default="",
        verbose_name=_("gradient end colour"),
        help_text=_(
            "Colour for the last tag (by order). Leave blank to use the start "
            "colour for every tag.",
        ),
    )
    tag_style = models.CharField(
        max_length=10,
        choices=TagStyle.choices,
        default=TagStyle.SOFT,
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "resource categories"

    def __str__(self):
        return self.name

    def _slug_source(self):
        return self.name_en or self.name

    @cached_property
    def _derived_tag_colours(self) -> dict[int, str]:
        if not self.gradient_start_colour:
            return {}
        end_colour = self.gradient_end_colour or self.gradient_start_colour
        tags = list(self.tags.all())
        total = len(tags)
        return {
            tag.pk: interpolate_colour(
                self.gradient_start_colour,
                end_colour,
                i / max(total - 1, 1),
            )
            for i, tag in enumerate(tags)
        }


class ResourceTag(models.Model):
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from="_slug_source")
    abbreviation = models.CharField(max_length=20, blank=True)
    color = ColorField(
        blank=True,
        default="",
        help_text=_(
            "Optional. Overrides the colour automatically derived from the "
            "category's gradient.",
        ),
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        unique_together = [("category", "slug")]

    def __str__(self):
        return self.name

    def _slug_source(self):
        return self.name_en or self.name

    @property
    def effective_colour(self) -> str:
        if self.color:
            return self.color
        return self.category._derived_tag_colours.get(self.pk, "")  # noqa: SLF001

    @property
    def text_color(self) -> str:
        return contrast_colour(self.effective_colour)

    @property
    def style_attrs(self) -> str:
        colour = self.effective_colour
        if not colour:
            return ""
        style = self.category.tag_style
        if style == ResourceCategory.TagStyle.OUTLINE:
            return (
                f"background-color: transparent; color: {colour}; "
                f"border: 1px solid {colour};"
            )
        if style == ResourceCategory.TagStyle.SOFT:
            r = int(colour[1:3], 16)
            g = int(colour[3:5], 16)
            b = int(colour[5:7], 16)
            return (
                f"background-color: rgba({r}, {g}, {b}, 0.15); color: {darken(colour)};"
            )
        return f"background-color: {colour}; color: {contrast_colour(colour)};"


class Resource(models.Model):
    class Visibility(models.IntegerChoices):
        PUBLIC = 0, _("Public - visible and accessable by everyone")
        ACCESS_ACCOUNT_REQUIRED = (
            1,
            _(
                "Account required to access - anyone can view, "
                "logged-in users can access",
            ),
        )
        ACCESS_MEMBERSHIP_REQUIRED = (
            2,
            _(
                "Membership required to access - anyone can view, "
                "only members can access files",
            ),
        )
        MEMBERS_ONLY = 3, _("Members only - only members can view or access")

    name = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from="_slug_source", always_update=True, null=True)
    description = HTMLField()
    published = models.BooleanField(default=False)
    visibility = models.PositiveSmallIntegerField(
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        help_text=_(
            "Controls who can view and access this resource. "
            "Public: no restrictions. "
            "Account required to access: anyone can browse, "
            "logged-in users can access. "
            "Membership required to access: anyone can browse, "
            "members can access files. "
            "Members only: only members can view or access.",
        ),
    )
    datetime_added = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True)
    # One search vector per language, maintained by Postgres triggers (see
    # migration 0016) so search can be scoped to the active UI language.
    # Weights: name=A, description & component names=B, tag
    # names/abbreviations & author user/entity names=C.
    # search_vector_en indexes the _en columns with the 'english' config.
    # search_vector_mi indexes the _mi columns with the 'simple' config,
    # falling back per field to the _en value when the _mi value is blank
    # (mirroring modeltranslation's display fallback). Author user and entity
    # names are language-neutral and indexed in both vectors.
    search_vector_en = SearchVectorField(null=True, editable=False)
    search_vector_mi = SearchVectorField(null=True, editable=False)
    view_count = models.PositiveIntegerField(default=0, editable=False)
    thumbnail = models.ImageField(
        _("thumbnail"),
        upload_to=resource_thumbnail_path,
        storage=get_public_media_storage,
        blank=True,
        help_text=_("Optional image shown on the resource card and detail page."),
    )
    thumbnail_card = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFill(200, 200)],
        format="JPEG",
        options={"quality": 80},
    )
    thumbnail_detail = ImageSpecField(
        source="thumbnail",
        processors=[ResizeToFit(800, 600)],
        format="JPEG",
        options={"quality": 85},
    )
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
    tags = models.ManyToManyField(
        ResourceTag,
        related_name="resources",
        blank=True,
    )

    class Meta:
        ordering = ["-datetime_updated"]
        indexes = [
            GinIndex(fields=["search_vector_en"]),
            GinIndex(fields=["search_vector_mi"]),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "resources:resource",
            kwargs={"pk": self.pk, "slug": self.slug},
        )

    def _slug_source(self):
        return self.name_en or self.name

    @property
    def visibility_badge_label(self):
        return {
            # Translators: Short badge label — requires an account to access
            self.Visibility.ACCESS_ACCOUNT_REQUIRED: _("Login required"),
            # Translators: Short badge label — active membership required to access
            self.Visibility.ACCESS_MEMBERSHIP_REQUIRED: _("Membership required"),
            # Translators: Short badge label — resource is only visible to members
            self.Visibility.MEMBERS_ONLY: _("Membership required to view"),
        }.get(self.visibility, "")

    @property
    def visibility_badge_tooltip(self):
        return {
            # Translators: Tooltip on a resource badge — listed publicly but
            # login required to download/view it
            self.Visibility.ACCESS_ACCOUNT_REQUIRED: (
                _("Anyone can view, login required to access")
            ),
            # Translators: Tooltip on a resource badge — listed publicly but
            # an active membership is needed to download/view it
            self.Visibility.ACCESS_MEMBERSHIP_REQUIRED: (
                _("Anyone can view, membership required to access")
            ),
            # Translators: Resource badge tooltip — hidden entirely from non-members
            self.Visibility.MEMBERS_ONLY: _("Only members can view or access"),
        }.get(self.visibility, "")

    @property
    def visibility_badge_css_class(self):
        return {
            self.Visibility.ACCESS_ACCOUNT_REQUIRED: (
                "resource-visibility-account-required"
            ),
            self.Visibility.ACCESS_MEMBERSHIP_REQUIRED: (
                "resource-visibility-membership-access"
            ),
            self.Visibility.MEMBERS_ONLY: "resource-visibility-membership-only",
        }.get(self.visibility, "")


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
        max_length=500,
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
    uuid = models.UUIDField(default=uuid4, editable=False)
    view_count = models.PositiveIntegerField(default=0, editable=False)

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


class ResourceView(models.Model):
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name="views",
    )
    datetime_viewed = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["resource", "datetime_viewed"])]

    def __str__(self):
        return f"{self.resource} viewed {self.datetime_viewed}"


class ResourceComponentView(models.Model):
    component = models.ForeignKey(
        ResourceComponent,
        on_delete=models.CASCADE,
        related_name="views",
    )
    datetime_viewed = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["component", "datetime_viewed"])]

    def __str__(self):
        return f"{self.component} viewed {self.datetime_viewed}"


def record_resource_view(resource):
    ResourceView.objects.create(resource=resource)
    Resource.objects.filter(pk=resource.pk).update(
        view_count=models.F("view_count") + 1,
    )


def record_component_view(component):
    ResourceComponentView.objects.create(component=component)
    ResourceComponent.objects.filter(pk=component.pk).update(
        view_count=models.F("view_count") + 1,
    )
