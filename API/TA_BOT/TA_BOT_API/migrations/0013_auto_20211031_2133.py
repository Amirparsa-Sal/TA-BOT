# Generated by Django 3.2.7 on 2021-10-31 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TA_BOT_API', '0012_questionanswer_source_chat_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='homework',
            name='file',
        ),
        migrations.AddField(
            model_name='homework',
            name='file_id',
            field=models.BigIntegerField(null=True),
        ),
    ]