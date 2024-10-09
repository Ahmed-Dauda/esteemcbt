from typing import cast
from django.contrib.contenttypes.fields import GenericRelation
from django.forms import Widget
from users.models import Profile  # Update this import
from django.db import models
from django.db.models.deletion import CASCADE
from users.models import NewUser
from cloudinary.models import CloudinaryField
from embed_video.fields import EmbedVideoField
from django.conf import settings
from hitcount.models import HitCount, HitCountMixin
from django.utils.text import slugify
from tinymce.models import HTMLField
import uuid
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


class Session(models.Model):
    name = models.CharField(max_length=20, unique=True)  # E.g., '2022-2023', '2023-2024'
    
    def __str__(self):
        return self.name

class Term(models.Model):
    name = models.CharField(max_length=20, unique=True)  # E.g., 'First Term', 'Second Term', 'Third Term'

    def __str__(self):
        return self.name


class Courses(models.Model):

    
    title = models.CharField(max_length=225, blank=True, null=True)
    schools = models.ManyToManyField("quiz.School" , related_name='courses', blank=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)  # ForeignKey to Session model
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True) 
    exam_type = models.ForeignKey('quiz.ExamType', on_delete=models.SET_NULL, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk', related_query_name='hit_count_generic_relation')
    
    class Meta:
        verbose_name = 'subject'
        verbose_name_plural = 'subjects'
        
    def __str__(self):
        
        school_name = '\n'.join(str(school) for school in self.schools.all())
        # return f'{self.title} - {self.session} - {self.term} - {self.exam_type}'
        return f'{self.title}'


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


     
class FrequentlyAskQuestions(models.Model):
    
    title = models.CharField(max_length=225,  null=True, blank =True )
    desc = models.TextField(blank=True, null= True)
    # course_type = models.CharField(max_length=500, blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    # id = models.BigAutoField(primary_key=True)

    def __str__(self):
        return f'{self.title}' 
    
       
class Gallery(models.Model):

    title = models.CharField(max_length=100, null=True)
    gallery = CloudinaryField('gallery image', blank=True, null= True)
 
    def __str__(self):
        return f'{self.title}'