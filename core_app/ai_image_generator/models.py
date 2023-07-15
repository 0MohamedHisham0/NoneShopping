from django.db import models

from ai_image_generator.enums.generated_image_status import GeneratedImageStatus
from ai_image_generator.enums.image_detail_type import ImageDetailsType


class GeneratedImage(models.Model):
    title = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=GeneratedImageStatus.choices,
                              default=GeneratedImageStatus.PROCESSING)
    platform_image_url = models.CharField(max_length=255)
    drive_image_url = models.CharField(max_length=255)
    drive_folder_url = models.CharField(max_length=255)
    selected_image_id = models.BigIntegerField(null=True)
    task_id = models.CharField(null=True)
    is_selected = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    selected_at = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.title} {self.status} {self.is_selected} {self.drive_image_url} {self.drive_folder_url} {self.task_id}"

    class Meta:
        db_table = 'generated_image'


class GeneratedImageItem(models.Model):
    generated_image_id = models.CharField(max_length=255)
    image_type = models.CharField(max_length=20, choices=ImageDetailsType.choices, null=True)
    image_url = models.CharField(max_length=255)
    is_selected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.generated_image_id} {self.image_type} {self.image_url} {self.is_selected}"

    class Meta:
        db_table = 'generated_image_item'

# py manage.py makemigrations ai_image_generator
# py manage.py migrate
