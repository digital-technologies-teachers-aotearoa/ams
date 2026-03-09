from django.db import models


class Entity(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to="entities/", blank=True)
    url = models.URLField(blank=True)

    class Meta:
        verbose_name_plural = "entities"
        ordering = ["name"]

    def __str__(self):
        return self.name
