from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.models import Page


class ContactFormSubmission(models.Model):
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="contact_submissions",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = _("Contact form submission")
        verbose_name_plural = _("Contact form submissions")

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.submitted_at:%Y-%m-%d %H:%M}"
