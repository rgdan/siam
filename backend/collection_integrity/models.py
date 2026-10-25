from django.conf import settings
from django.db import models


class Piece(models.Model):
    title = models.CharField(max_length=200)
    state = models.CharField(max_length=40, default="registered")
    decommissioned = models.BooleanField(default=False)
    loan_to = models.CharField(max_length=200, blank=True)


class Photo(models.Model):
    piece = models.ForeignKey(Piece, related_name="photos", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    content = models.BinaryField()


class PieceHistory(models.Model):
    piece = models.ForeignKey(Piece, related_name="history", on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    operation = models.CharField(max_length=30)
    changes = models.JSONField(default=dict)
