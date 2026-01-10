
# Create your models here.
from django.db import models

class MenuCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.PROTECT, related_name="items")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price_egp = models.PositiveIntegerField()   # avoid float money
    sizes = models.JSONField(default=list, blank=True)
    is_available = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return self.name
