# Generated by Django 4.0.4 on 2022-05-06 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_alter_question_variant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operationitem',
            name='answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.answers'),
        ),
    ]