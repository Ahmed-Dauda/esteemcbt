# Generated by Django 5.0.6 on 2024-09-22 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_profile_admission_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newuser',
            name='admission_no',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='date_joined',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='first_name',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='last_name',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='student_class',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='newuser',
            name='username',
            field=models.CharField(blank=True, db_index=True, max_length=35),
        ),
        migrations.AlterField(
            model_name='profile',
            name='admission_no',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='countries',
            field=models.CharField(blank=True, db_index=True, max_length=225, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='created',
            field=models.DateTimeField(auto_now_add=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='first_name',
            field=models.CharField(blank=True, db_index=True, max_length=225, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_name',
            field=models.CharField(blank=True, db_index=True, max_length=225, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='phone_number',
            field=models.CharField(blank=True, db_index=True, max_length=225, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='status_type',
            field=models.CharField(choices=[('Premium', 'PREMIUM'), ('Free', 'FREE'), ('Sponsored', 'SPONSORED')], db_index=True, default='Free', max_length=225),
        ),
        migrations.AlterField(
            model_name='profile',
            name='student_class',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='updated',
            field=models.DateTimeField(auto_now=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='username',
            field=models.CharField(blank=True, db_index=True, max_length=225, null=True),
        ),
    ]