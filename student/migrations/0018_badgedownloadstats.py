# Generated by Django 5.0.6 on 2024-09-24 10:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0017_rename_badge_description_badge_badge_type_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeDownloadStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveIntegerField()),
                ('year', models.PositiveIntegerField()),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('badge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.badge')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['year', 'month'],
                'unique_together': {('student', 'badge', 'month', 'year')},
            },
        ),
    ]