# Generated by Django 4.0.4 on 2022-06-08 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_operations_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='organization',
            field=models.CharField(max_length=750),
        ),
        migrations.AlterField(
            model_name='user',
            name='position',
            field=models.CharField(max_length=500),
        ),
    ]