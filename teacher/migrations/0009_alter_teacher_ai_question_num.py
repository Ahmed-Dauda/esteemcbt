# Generated by Django 5.0.6 on 2025-05-21 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teacher', '0008_alter_teacher_classes_taught_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='ai_question_num',
            field=models.PositiveIntegerField(blank=True, default=600, null=True, verbose_name='Number of AI Questions'),
        ),
    ]
