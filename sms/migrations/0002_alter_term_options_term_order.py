# Generated by Django 5.0.6 on 2024-11-13 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sms', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='term',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='term',
            name='order',
            field=models.PositiveIntegerField(default=1),
        ),
    ]