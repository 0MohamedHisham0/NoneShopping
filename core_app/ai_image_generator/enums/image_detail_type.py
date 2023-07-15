from django.db import models


class ImageDetailsType(models.TextChoices):
    MAIN = 'main'
    SPLITTED = 'splitted'
    REMOVED_BACKGROUND = 'removed_background'
    UP_SCALED = 'up_scaled'
