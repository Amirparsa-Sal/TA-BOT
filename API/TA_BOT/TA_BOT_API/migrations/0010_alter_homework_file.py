# Generated by Django 3.2.7 on 2021-10-11 12:01

import TA_BOT_API.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TA_BOT_API', '0009_alter_due_date_time_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homework',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to=TA_BOT_API.models.homework_file_directory_path),
        ),
    ]
