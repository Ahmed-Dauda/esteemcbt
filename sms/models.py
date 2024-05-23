from typing import cast
from django.contrib.contenttypes.fields import GenericRelation
from django.forms import Widget
from users.models import Profile  # Update this import
from django.db import models
from django.db.models.deletion import CASCADE
from users.models import NewUser
from cloudinary.models import CloudinaryField
from django.db import models
from embed_video.fields import EmbedVideoField
from django.conf import settings
from hitcount.models import HitCount, HitCountMixin
from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField

# models.py

class Awards(models.Model):

    title = models.CharField(max_length=100, blank=True, null= True)
    img_about_us = CloudinaryField('about_us', blank=True, null= True)
    content = HTMLField(null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True) 

    def __str__(self):
        return self.title

class AboutUs(models.Model):

    title = models.CharField(max_length=100, blank=True, null= True)
    img_about_us = CloudinaryField('about_us', blank=True, null= True)
    content = HTMLField(null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True) 

    def __str__(self):
        return self.title

class FrontPageVideo(models.Model):

    title = models.CharField(max_length=500, blank=True, null=True)
    video = EmbedVideoField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True) 
    id = models.BigAutoField(primary_key=True)
    hit_count_generic = GenericRelation(HitCount, object_id_field='object_pk', related_query_name='hit_count_generic_relation')

    def __str__(self):
        return f'{self.title}'

class CarouselImage(models.Model):
    image_carousel = CloudinaryField('carousel_images/', blank=True, null= True)
    caption = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.caption


class Categories(models.Model, HitCountMixin):
   
    
    name = models.CharField(max_length=225, blank=True, null= True, unique=True)
    desc = models.TextField( blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    img_cat = CloudinaryField('image', blank=True, null= True)
    # object_pk = models.PositiveIntegerField(default=True)
    hit_count_generic = GenericRelation(
    HitCount, object_id_field='object_pk',
    related_query_name='hit_count_generic_relation')

# 
    def __str__(self):
        return f'{self.name}'


import uuid

class Courses(models.Model):
    COURSE_TYPE = [
        ('Course', 'COURSE'),
        ('Professional Certificate', 'PROFESSIONAL CERTIFICATE'),
        ('Specialization', 'SPECIALIZATION'),
        ('Degree', 'DEGREE'),
        ('Diploma', 'DIPLOMA'),
    ]

    PAYMENT_CHOICES = [
        ('Premium', 'PREMIUM'),
        ('Free', 'FREE'),
        ('Sponsored', 'SPONSORED'),
    ]

    img_course = CloudinaryField('image', blank=True, null=True)
     # Add a ForeignKey field to represent the course a student is enrolled in.
    schools = models.ManyToManyField("quiz.School" , related_name='courses', blank=True)
    # prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False)
    # categories = models.ForeignKey(Categories, blank=True, null=True ,default=1, on_delete=models.SET_NULL, related_name='categories')
    title = models.CharField(max_length=225, blank=True, null=True)
    # course_logo = CloudinaryField('course_logo', blank=True, null=True)
    # course_owner = models.CharField(max_length=225, blank=True, null=True)
    # course_type = models.CharField(choices=COURSE_TYPE, default='course', max_length=225, blank=True, null=True)
    # status_type = models.CharField(choices=PAYMENT_CHOICES, default='Free', max_length=225, blank=True, null=True)
    # price = models.DecimalField(max_digits=10, decimal_places=0, default='500', max_length=225, blank=True, null=True)
    # cert_price = models.DecimalField(max_digits=10, decimal_places=0, default='1000', max_length=225, blank=True, null=True)
    # desc = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk', related_query_name='hit_count_generic_relation')
    

    def __str__(self):
        
        school_name = '\n'.join(str(school) for school in self.schools.all())
        return f'{self.title} - {school_name}'


# payment models and logics 

 

class CourseFrequentlyAskQuestions(models.Model):
    

    title = models.CharField(max_length=225,  null=True, blank =True )
    desc = models.TextField(blank=True, null= True)
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True)
    # course_type = models.CharField(max_length=400, blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    # updated = models.DateTimeField(auto_now=True, blank=True, null= True)
   

    def __str__(self):
        return f'{self.courses} - {self.title}' 
    



class CourseLearnerReviews(models.Model):
    title = models.CharField(max_length=225,  null=True, blank=True)
    desc = models.TextField(null=True)
    courses_review = models.ForeignKey(Courses, on_delete=models.CASCADE, null= True ,related_name= 'courselearner')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.title} - {self.courses_review.title}'


     

class CareerOpportunities(models.Model):
    

    # title = models.CharField(max_length=225,  null=True, blank =True )
    # desc = models.TextField(blank=True, null= True)
    desc = models.TextField( blank=True, null= True)
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True) 
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.desc} -{self.courses.title}' 
      


class Skillyouwillgain(models.Model):
    

    title = models.TextField(max_length=900,null=True, blank =True )
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True) 
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.courses.title}' 

class Whatyouwilllearn(models.Model):
    
    desc = models.TextField(max_length=900,null=True, blank =True )
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True) 
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.desc} -{self.courses.title}' 
    
    
class Whatyouwillbuild(models.Model):
    
    desc = models.CharField(max_length=900,null=True, blank =True )
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True) 
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)
    def __str__(self):
        return f'{self.desc} {self.courses.title}' 


class AboutCourseOwner(models.Model):
    
    desc = models.TextField(null=True, blank =True )
    courses = models.ForeignKey(Courses, on_delete= models.CASCADE, null= True) 
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.courses.title}' 
    


# models.py

from tinymce.widgets import TinyMCE

class CustomTinyMCEWidget(TinyMCE):
    def __init__(self, *args, **kwargs):
        kwargs['attrs'] = {'cols': '40', 'rows': '4'}  # Set the desired width and height here
        super().__init__(*args, **kwargs)


class Topics(models.Model):
    categories = models.ForeignKey(Categories, on_delete=models.CASCADE)
    courses = models.ForeignKey(Courses, on_delete=models.CASCADE) 
    title = models.CharField(max_length=500, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ManyToManyField('users.Profile', through='CompletedTopics')
    desc = HTMLField(null=True)
    transcript = models.TextField(blank=True, null=True)  # New field for transcript
    img_topic = CloudinaryField('topic image', blank=True, null=True)
    video = EmbedVideoField(blank=True, null=True)
    topics_url = models.CharField(max_length=500, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True) 
    id = models.BigAutoField(primary_key=True)
    hit_count_generic = GenericRelation(HitCount, object_id_field='object_pk', related_query_name='hit_count_generic_relation')



    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} - {self.courses}'


class CompletedTopics(models.Model):

    user= models.ForeignKey(Profile, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topics, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} - {self.topic.title}'

class FrequentlyAskQuestions(models.Model):
    

    title = models.CharField(max_length=225,  null=True, blank =True )
    desc = models.TextField(blank=True, null= True)
    # course_type = models.CharField(max_length=500, blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.title}' 
    
class Comment(models.Model):
    
    username = models.CharField(default='fff', max_length=225, blank=True, null= True, unique=True)
    first_name = models.CharField(default='fff', max_length=225, blank=True, null= True)
    last_name = models.CharField(max_length=225, blank=True, null= True)
    title = models.CharField(max_length=225,  null=True, blank =True )
    desc = models.TextField(max_length=500, blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.title}'

class Blog(models.Model):

    author=models.ForeignKey(Profile,on_delete=models.CASCADE, blank=True, null= True)
    poster = models.CharField(max_length=225,  null=True, blank =True )
    title = models.CharField(max_length=225,  null=True, blank =True )
    img_source = models.CharField(max_length=225, null= True)
    slug = models.SlugField(null=False, unique=True) 
    img_blog = CloudinaryField('blog image', blank=True, null= True)
    desc = models.TextField( blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    hit_count_generic = GenericRelation(
    HitCount, object_id_field='object_pk',
    related_query_name='hit_count_generic_relation')
    def __str__(self):
        return f'{self.title}'

from django.utils import timezone
from django.urls import reverse
# MainApp/models.py
class Blogcomment(models.Model):
    post = models.ForeignKey(Blog,related_name='comments' ,on_delete=models.SET_NULL, null=True)
    # author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True)
    # subtitle = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
   
    img_blogcomment = CloudinaryField('comment image', blank=True, null= True)
    
    def __str__(self):
        return f'{self.post}'

class Alert(models.Model):

    title = models.CharField(max_length=100, null=True)
    content = models.TextField(blank=True, null= True)
    img_ebook = CloudinaryField('Ebook images', blank=True, null= True)
    price = models.DecimalField (max_digits=10, decimal_places=2, default= '1500' ,max_length=225, blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
 
    def __str__(self):
        return f'{self.title}'
    
class Partners(models.Model):

    title = models.CharField(max_length=100, null=True)
   
    img_partner = CloudinaryField('partner images', blank=True, null= True)
 
    def __str__(self):
        return f'{self.title}'
       
class Gallery(models.Model):

    title = models.CharField(max_length=100, null=True)
    gallery = CloudinaryField('gallery image', blank=True, null= True)
 
    def __str__(self):
        return f'{self.title}'