# Generated by Django 5.0.4 on 2024-05-08 17:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0008_remove_frequentlyaskquestions_course_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courses',
            name='categories',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='categories', to='sms.categories'),
        ),
    ]