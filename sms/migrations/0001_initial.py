# Generated by Django 4.1 on 2024-03-29 14:58

import cloudinary.models
from django.db import migrations, models
import django.db.models.deletion
import embed_video.fields
import hitcount.models
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AboutCourseOwner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, null=True)),
                ('content', models.TextField(blank=True, null=True)),
                ('img_ebook', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='Ebook images')),
                ('price', models.DecimalField(blank=True, decimal_places=2, default='1500', max_digits=10, max_length=225, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('poster', models.CharField(blank=True, max_length=225, null=True)),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('img_source', models.CharField(max_length=225, null=True)),
                ('slug', models.SlugField(unique=True)),
                ('img_blog', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='blog image')),
                ('desc', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Blogcomment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('img_blogcomment', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='comment image')),
            ],
        ),
        migrations.CreateModel(
            name='CareerOpportunities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Categories',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=225, null=True, unique=True)),
                ('desc', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('img_cat', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image')),
            ],
            bases=(models.Model, hitcount.models.HitCountMixin),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, default='fff', max_length=225, null=True, unique=True)),
                ('first_name', models.CharField(blank=True, default='fff', max_length=225, null=True)),
                ('last_name', models.CharField(blank=True, max_length=225, null=True)),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('desc', models.TextField(blank=True, max_length=500, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CompletedTopics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='CourseFrequentlyAskQuestions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('desc', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseLearnerReviews',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('desc', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Courses',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('img_course', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image')),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('course_logo', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='course_logo')),
                ('course_owner', models.CharField(blank=True, max_length=225, null=True)),
                ('course_type', models.CharField(blank=True, choices=[('Course', 'COURSE'), ('Professional Certificate', 'PROFESSIONAL CERTIFICATE'), ('Specialization', 'SPECIALIZATION'), ('Degree', 'DEGREE'), ('Diploma', 'DIPLOMA')], default='course', max_length=225, null=True)),
                ('status_type', models.CharField(blank=True, choices=[('Premium', 'PREMIUM'), ('Free', 'FREE'), ('Sponsored', 'SPONSORED')], default='Free', max_length=225, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=0, default='500', max_digits=10, max_length=225, null=True)),
                ('cert_price', models.DecimalField(blank=True, decimal_places=0, default='1000', max_digits=10, max_length=225, null=True)),
                ('desc', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='FrequentlyAskQuestions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=225, null=True)),
                ('desc', models.TextField(blank=True, null=True)),
                ('course_type', models.CharField(blank=True, max_length=500, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, null=True)),
                ('gallery', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='gallery image')),
            ],
        ),
        migrations.CreateModel(
            name='Partners',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, null=True)),
                ('img_partner', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='partner images')),
            ],
        ),
        migrations.CreateModel(
            name='Skillyouwillgain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField(blank=True, max_length=900, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Whatyouwilllearn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.TextField(blank=True, max_length=900, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('courses', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sms.courses')),
            ],
        ),
        migrations.CreateModel(
            name='Whatyouwillbuild',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('desc', models.CharField(blank=True, max_length=900, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('courses', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='sms.courses')),
            ],
        ),
        migrations.CreateModel(
            name='Topics',
            fields=[
                ('title', models.CharField(blank=True, max_length=500, null=True)),
                ('slug', models.SlugField(blank=True, null=True, unique=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('desc', tinymce.models.HTMLField(null=True)),
                ('transcript', models.TextField(blank=True, null=True)),
                ('img_topic', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='topic image')),
                ('video', embed_video.fields.EmbedVideoField(blank=True, null=True)),
                ('topics_url', models.CharField(blank=True, max_length=500, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('categories', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sms.categories')),
            ],
        ),
    ]
