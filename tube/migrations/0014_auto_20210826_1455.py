# Generated by Django 3.1.2 on 2021-08-26 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tube', '0013_remove_video_view'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoview',
            name='date',
            field=models.DateField(verbose_name='再生日'),
        ),
    ]
