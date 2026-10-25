from django.db import models


class Parameter(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    value = models.JSONField()
