# Generated by Django 5.0.6 on 2024-08-13 23:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0041_school_a_max_school_a_min_school_b_max_school_b_min_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='A_comment',
            field=models.CharField(blank=True, default='Excellent performance', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='B_comment',
            field=models.CharField(blank=True, default='Good', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='C_comment',
            field=models.CharField(blank=True, default='Gredit', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='F_comment',
            field=models.CharField(blank=True, default='Fail', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='school',
            name='P_comment',
            field=models.CharField(blank=True, default='Pass', max_length=255, null=True),
        ),
    ]