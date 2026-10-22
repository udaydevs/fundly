"""Models are defined here """
from django.db import models
from django.db.models import F, Q


class Organization(models.Model):
    """
    Details containing name and slug(will be used to fetch data) are stored here.
    """
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name
