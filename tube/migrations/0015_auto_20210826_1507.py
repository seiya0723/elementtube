# Generated by Django 3.1.2 on 2021-08-26 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tube', '0014_auto_20210826_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoview',
            name='date',
            field=models.DateTimeField(verbose_name='再生日'),
        ),
    ]
