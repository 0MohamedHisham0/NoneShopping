from django.db import models


class GeneratedImageStatus(models.TextChoices):
    SUCCESS = 'success'
    FAILED = 'failed'
    PROCESSING = 'processing'
