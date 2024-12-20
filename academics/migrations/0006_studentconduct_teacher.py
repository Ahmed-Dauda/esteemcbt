# Generated by Django 5.0.6 on 2024-11-26 14:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0005_alter_studentconduct_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='studentconduct',
            name='teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conducted_records', to=settings.AUTH_USER_MODEL),
        ),
    ]
