# Generated by Django 4.0.4 on 2022-05-25 12:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_operationitem_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='operations',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='main.group'),
        ),
    ]
