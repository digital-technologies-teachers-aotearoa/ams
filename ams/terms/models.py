"""Models for terms and conditions management."""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.admin.panels import HelpPanel
from wagtail.admin.panels import MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index


class Term(models.Model):
    """Represents a logical legal document (e.g., Privacy Policy, Terms of Service)."""

    key = models.SlugField(
        max_length=100,
        unique=True,
        help_text=_("Unique identifier (e.g., 'privacy-policy', 'terms-of-service')"),
    )
    name = models.CharField(
        max_length=255,
        help_text=_("Human-readable name displayed to users"),
    )
    description = models.TextField(
        blank=True,
        help_text=_("Internal description for administrators"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("key"),
        FieldPanel("name"),
        FieldPanel("description"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("key"),
    ]

    class Meta:
        ordering = ["key"]
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")

    def __str__(self):
        return self.name


class TermVersion(models.Model):
    """
    Represents a specific, immutable version of a Term.

    IMPORTANT: The "latest" version shown to users is determined by the most recent
    date_active timestamp, NOT by version number. For example, version "1.5" with
    a newer date_active will be considered "latest" over version "2.0" with an
    older date_active.
    """

    term = models.ForeignKey(
        "Term",
        on_delete=models.PROTECT,  # Prevent deletion if versions exist
        related_name="versions",
    )
    version = models.CharField(
        max_length=50,
        help_text=_(
            "Version identifier (e.g., '1.0', '2.1', '2024-01-15'). "
            "This is for reference only - the 'latest' version is determined "
            "by the most recent activation date, not this version number.",
        ),
    )
    content = RichTextField(
        help_text=_("The full legal text users must accept"),
        features=[
            "h2",
            "h3",
            "h4",
            "bold",
            "italic",
            "ol",
            "ul",
            "link",
        ],
    )
    change_log = RichTextField(
        blank=True,
        help_text=_("Summary of changes from previous version (for internal use)"),
        features=[
            "h2",
            "h3",
            "h4",
            "bold",
            "italic",
            "ol",
            "ul",
            "link",
        ],
    )
    is_active = models.BooleanField(
        default=False,
        help_text=_(
            "Draft versions should be inactive. Activate when ready to enforce.",
        ),
    )
    date_active = models.DateTimeField(
        help_text=_(
            "Version becomes enforceable from this date/time. "
            "The version with the most recent activation date is considered the "
            "'latest' version that users must accept, regardless of version number.",
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        HelpPanel(
            content=_(
                "<p><strong>Important:</strong> Users always see the version with the "
                "most recent <strong>activation date</strong>, not the highest version "
                "number.</p>"
                "<p>For example, version '1.5' with a newer Effective Date will be "
                "shown instead of version '2.0' with an older Effective Date.</p>",
            ),
        ),
        MultiFieldPanel(
            [
                FieldPanel("term"),
                FieldPanel("version"),
            ],
            heading=_("Version Info"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_active"),
                FieldPanel("date_active"),
            ],
            heading=_("Activation"),
        ),
        FieldPanel("content"),
        FieldPanel("change_log"),
    ]

    search_fields = [
        index.SearchField("version"),
        index.SearchField("content"),
    ]

    class Meta:
        ordering = ["-date_active", "-created_at"]
        verbose_name = _("Term Version")
        verbose_name_plural = _("Term Versions")
        constraints = [
            models.UniqueConstraint(
                fields=["term", "version"],
                name="unique_term_version",
            ),
        ]
        indexes = [
            models.Index(
                fields=["is_active", "date_active"],
            ),  # For current version queries
        ]

    def __str__(self):
        return f"{self.term.name} v{self.version}"

    def is_current(self):
        """Check if this version is currently enforceable."""
        return self.is_active and self.date_active <= timezone.now()


class TermAcceptance(models.Model):
    """Records that a user accepted a specific TermVersion."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # If user deleted, remove acceptances
        related_name="term_acceptances",
    )
    term_version = models.ForeignKey(
        "TermVersion",
        on_delete=models.PROTECT,  # Never delete accepted versions
        related_name="acceptances",
    )
    accepted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(
        help_text=_("IP address from which acceptance was recorded"),
    )
    user_agent = models.TextField(
        help_text=_("Browser user agent string"),
    )
    source = models.CharField(
        max_length=50,
        default="web",
        help_text=_("Source of acceptance (e.g., 'web', 'api', 'sso')"),
    )

    class Meta:
        ordering = ["-accepted_at"]
        verbose_name = _("Term Acceptance")
        verbose_name_plural = _("Term Acceptances")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "term_version"],
                name="unique_user_term_version_acceptance",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "accepted_at"]),  # For user history queries
        ]

    def __str__(self):
        return f"{self.user.email} accepted {self.term_version} on {self.accepted_at}"
