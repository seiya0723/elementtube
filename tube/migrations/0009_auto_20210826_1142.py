# Generated by Django 3.1.2 on 2021-08-26 02:42

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tube', '0008_auto_20210826_1122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoview',
            name='date',
            field=models.DateTimeField(verbose_name='再生日'),
        ),
        migrations.AlterUniqueTogether(
            name='videoview',
            unique_together={('target', 'date', 'user'), ('target', 'date', 'ip')},
        ),
    ]
