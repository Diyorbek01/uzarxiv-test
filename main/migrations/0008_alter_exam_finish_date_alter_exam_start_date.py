# Generated by Django 4.0.4 on 2022-05-12 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_exam_finish_date_alter_exam_start_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exam',
            name='finish_date',
            field=models.DateTimeField(verbose_name='Yopilish sanasi'),
        ),
        migrations.AlterField(
            model_name='exam',
            name='start_date',
            field=models.DateTimeField(verbose_name='Ochilish sanasi'),
        ),
    ]