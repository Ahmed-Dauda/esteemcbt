# Generated by Django 5.0.6 on 2024-08-13 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0040_rename_school_moto_school_school_motto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='A_max',
            field=models.IntegerField(default=100),
        ),
        migrations.AddField(
            model_name='school',
            name='A_min',
            field=models.IntegerField(default=81),
        ),
        migrations.AddField(
            model_name='school',
            name='B_max',
            field=models.IntegerField(default=80),
        ),
        migrations.AddField(
            model_name='school',
            name='B_min',
            field=models.IntegerField(default=66),
        ),
        migrations.AddField(
            model_name='school',
            name='C_max',
            field=models.IntegerField(default=65),
        ),
        migrations.AddField(
            model_name='school',
            name='C_min',
            field=models.IntegerField(default=56),
        ),
        migrations.AddField(
            model_name='school',
            name='F_max',
            field=models.IntegerField(default=45),
        ),
        migrations.AddField(
            model_name='school',
            name='F_min',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='school',
            name='P_max',
            field=models.IntegerField(default=55),
        ),
        migrations.AddField(
            model_name='school',
            name='P_min',
            field=models.IntegerField(default=46),
        ),
    ]