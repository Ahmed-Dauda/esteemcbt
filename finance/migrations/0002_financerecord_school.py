# Generated by Django 5.0.6 on 2024-11-12 13:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        ('quiz', '0010_alter_course_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='financerecord',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='financerecord', to='quiz.school'),
        ),
    ]
