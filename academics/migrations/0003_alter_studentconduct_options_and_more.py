# Generated by Django 5.0.6 on 2024-11-26 11:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_studentconduct_student_class'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='studentconduct',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='studentconduct',
            unique_together=set(),
        ),
    ]
