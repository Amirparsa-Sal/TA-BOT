# Generated by Django 3.2.18 on 2023-03-02 08:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('TA_BOT_API', '0019_alter_user_student_id'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='authdata',
            options={'verbose_name_plural': 'Auth Data'},
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'Categories'},
        ),
        migrations.RemoveField(
            model_name='authdata',
            name='password',
        ),
    ]