# Generated by Django 5.0.4 on 2024-05-12 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0008_alter_teacher_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='SampleCodes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField()),
            ],
        ),
    ]
