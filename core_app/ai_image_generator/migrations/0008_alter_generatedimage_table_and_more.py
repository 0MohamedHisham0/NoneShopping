# Generated by Django 4.2.3 on 2023-07-09 06:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_image_generator', '0007_generatedimageitem'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='generatedimage',
            table='generated_image',
        ),
        migrations.AlterModelTable(
            name='generatedimageitem',
            table='generated_image_item',
        ),
    ]