# Generated by Django 5.0.6 on 2025-06-20 09:33

import cloudinary.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('quiz', '0003_initial'),
        ('sms', '0002_initial'),
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvertisementImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='advertisement_images')),
                ('desc', models.TextField(blank=True, null=True)),
                ('link', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Clubs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('desc', models.TextField()),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='Clubs images')),
                ('price', models.DecimalField(blank=True, decimal_places=0, default='500', max_digits=10, max_length=225, null=True)),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Directors',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('desc', models.TextField()),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='directors images')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Management',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('desc', models.TextField()),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='management images')),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PDFDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('desc', models.TextField()),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='Ebook images')),
                ('price', models.DecimalField(blank=True, decimal_places=0, default='500', max_digits=10, max_length=225, null=True)),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='PDFGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('desc', models.TextField()),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='gallery images')),
                ('pdf_url', models.URLField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.CharField(blank=True, max_length=120, null=True)),
                ('term', models.CharField(blank=True, max_length=120, null=True)),
                ('badge_type', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('final_average', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('final_grade', models.CharField(blank=True, max_length=2, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
            ],
        ),
        migrations.CreateModel(
            name='CertificatePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(null=True)),
                ('ref', models.CharField(max_length=250, null=True)),
                ('f_code', models.CharField(blank=True, max_length=200, null=True)),
                ('first_name', models.CharField(max_length=250, null=True)),
                ('last_name', models.CharField(max_length=200, null=True)),
                ('content_type', models.CharField(max_length=200, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('courses', models.ManyToManyField(blank=True, related_name='certificates', to='quiz.course')),
                ('payment_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
            ],
        ),
        migrations.CreateModel(
            name='ExamStatistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_exams_conducted', models.PositiveIntegerField(default=0)),
                ('session', models.CharField(blank=True, max_length=20, null=True)),
                ('term', models.CharField(blank=True, max_length=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quiz.school')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(null=True)),
                ('ref', models.CharField(max_length=250, null=True)),
                ('first_name', models.CharField(max_length=200, null=True)),
                ('last_name', models.CharField(max_length=200, null=True)),
                ('content_type', models.CharField(max_length=200, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('courses', models.ManyToManyField(blank=True, related_name='payments', to='sms.courses')),
                ('payment_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
            ],
        ),
        migrations.CreateModel(
            name='EbooksPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(null=True)),
                ('ref', models.CharField(max_length=250, null=True)),
                ('first_name', models.CharField(max_length=250, null=True)),
                ('last_name', models.CharField(max_length=200, null=True)),
                ('content_type', models.CharField(max_length=200, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('payment_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
                ('courses', models.ManyToManyField(related_name='ebooks', to='student.pdfdocument')),
            ],
        ),
        migrations.CreateModel(
            name='DocPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(null=True)),
                ('ref', models.CharField(max_length=250, null=True)),
                ('first_name', models.CharField(max_length=250, null=True)),
                ('last_name', models.CharField(max_length=200, null=True)),
                ('email', models.EmailField(max_length=254, null=True)),
                ('verified', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('payment_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.profile')),
                ('pdfdocument', models.ManyToManyField(related_name='docpayments', to='student.pdfdocument')),
            ],
        ),
        migrations.CreateModel(
            name='ReferrerMentor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=20, null=True)),
                ('referrer_code', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('account_number', models.CharField(blank=True, max_length=20, null=True)),
                ('bank', models.CharField(blank=True, max_length=50, null=True)),
                ('phone_no', models.CharField(blank=True, max_length=50, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('courses', models.ManyToManyField(blank=True, related_name='referrercourses', to='sms.courses')),
                ('referred_students', models.ManyToManyField(blank=True, related_name='referrer_profiles', to=settings.AUTH_USER_MODEL)),
                ('referrer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referred_users', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BadgeDownloadStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveIntegerField(blank=True, null=True)),
                ('year', models.PositiveIntegerField(blank=True, null=True)),
                ('download_count', models.PositiveIntegerField(default=0)),
                ('badge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='student.badge')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quiz.school')),
            ],
            options={
                'ordering': ['year', 'month'],
                'unique_together': {('school', 'badge', 'month', 'year')},
            },
        ),
    ]
