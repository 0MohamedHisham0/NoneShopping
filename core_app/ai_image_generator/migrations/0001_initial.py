# Generated by Django 4.2.3 on 2023-07-06 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeneratedImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('tags', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('platform_image_url', models.CharField(max_length=255)),
                ('drive_image_url', models.CharField(max_length=255)),
                ('drive_folder_url', models.CharField(max_length=255)),
                ('selected_image_id', models.IntegerField()),
                ('is_selected', models.BooleanField()),
                ('is_viewed', models.BooleanField()),
            ],
        ),
    ]
