from django.db import models
# from student.models import Student
from users.models import Profile, NewUser
from cloudinary.models import CloudinaryField
from sms.models import Courses as smscourses
from tinymce.models import HTMLField
from sms.models import Courses
from sms.models import Session, Term

class ExamType(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    room_name = models.CharField(max_length=100, blank=True, null=True)
    schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='course', blank=True, null=True)
    course_name = models.ForeignKey(Courses, on_delete=models.CASCADE, blank=True, null=True)  # Ensure this is referencing the correct model
    question_number = models.PositiveIntegerField(blank=True, null=True)
    course_pay = models.BooleanField(default=False)
    total_marks = models.PositiveIntegerField(blank=True, null=True)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, blank=True, null=True)
    num_attemps = models.PositiveIntegerField(default=4)  # Fixed typo
    show_questions = models.PositiveIntegerField(default=10)
    duration_minutes = models.PositiveIntegerField(default=10)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    id = models.AutoField(primary_key=True)
 
    class Meta:
        # unique_together = ('course_name', 'session', 'term', 'schools')  # Combined Meta classes  
        unique_together = ('course_name', 'session', 'term', 'schools', 'exam_type')  # Combined Meta classes
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

    # def __str__(self):
    #     return f'{self.course_name or "No Course Name" }'
    
    def __str__(self):
        return f'{self.course_name} - {self.session} - {self.term} - {self.exam_type}'

    def get_questions(self):    
        return self.question_set.all()[:self.show_questions]



from django.core.exceptions import ValidationError

class CourseGrade(models.Model):
    schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='coursegrade', blank=True, null=True)
    name = models.CharField(max_length=140, blank=True, null=True)  # This is the class name like JSS1, JSS2, etc.
    students = models.ManyToManyField(NewUser, related_name='course_grades', blank=True)
    # subjects = models.ManyToManyField(Courses, related_name='course_grade')
    subjects = models.ManyToManyField(Course, related_name='course_grade')
    is_active = models.BooleanField(default=True)  # Add the checkbox field
    id = models.AutoField(primary_key=True)
    
    class Meta:
        verbose_name = 'Student class'
        verbose_name_plural = 'student classes'

    def __str__(self):
        # Return the class name (JSS1, JSS2, SS1, etc.) instead of subjects
        return self.name if self.name else 'Unnamed Class'
 

class School(models.Model):
    name = models.CharField(max_length=255)
    # students = models.ManyToManyField(Student, blank=True, related_name='school')
    # groups = models.ManyToManyField('quiz.Group', blank=True, null= True)
    school_name = models.CharField(max_length=255)
    course_pay = models.BooleanField(default=False)
    customer = models.BooleanField(default=True)
    school_motto = models.CharField(max_length=255, blank=True, null= True)
    school_address = models.CharField(max_length=355, blank=True, null= True)
    portfolio = models.CharField(max_length=255, blank=True, null= True)
    logo = CloudinaryField('school_logos', blank=True, null= True)
    principal_signature = CloudinaryField('principal_signatures', blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)

    # Grading system fields
    A_min = models.IntegerField(default=81)
    A_max = models.IntegerField(default=100)
    B_min = models.IntegerField(default=66)
    B_max = models.IntegerField(default=80)
    C_min = models.IntegerField(default=56)
    C_max = models.IntegerField(default=65)
    P_min = models.IntegerField(default=46)
    P_max = models.IntegerField(default=55)
    F_min = models.IntegerField(default=0)
    F_max = models.IntegerField(default=45)

    # Grading comments
    A_comment = models.CharField(max_length=255, blank=True, null=True, default='Excellent performance')
    B_comment = models.CharField(max_length=255, blank=True, null=True, default='Good')
    C_comment = models.CharField(max_length=255, blank=True, null=True, default='Gredit')
    P_comment = models.CharField(max_length=255, blank=True, null=True, default='Pass')
    F_comment = models.CharField(max_length=255, blank=True, null=True, default='Fail')


    def __str__(self):
        return f"{self.school_name}"


from django.db import models
from django.db.models import F
from django.db.models import Sum

           
from django.core.validators import MaxValueValidator, MinValueValidator


# real codes

class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
    marks = models.PositiveIntegerField(blank=True, null=True)
    question = HTMLField(blank=True, null=True)
    img_quiz = CloudinaryField('image', blank=True, null=True)
    option1 = HTMLField(max_length=500, blank=True, null=True)
    option2 = HTMLField(max_length=500, blank=True, null=True)
    option3 = HTMLField(max_length=500, blank=True, null=True)
    option4 = HTMLField(max_length=500, blank=True, null=True)

    cat = (('Option1', 'Option1'), ('Option2', 'Option2'), ('Option3', 'Option3'), ('Option4', 'Option4'))
    answer = models.CharField(max_length=200, choices=cat, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.course} | {self.question}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.course:
            total_marks = Question.objects.filter(course=self.course).aggregate(Sum('marks'))['marks__sum'] or 0
            self.course.total_marks = total_marks
            # Update the question_number in the related Course
            self.course.question_number = Question.objects.filter(course=self.course).count()
            # self.course.total_marks = Question.objects.filter(course = self.course).count()
            self.course.save()

    def delete(self, *args, **kwargs):
        course = self.course
        super().delete(*args, **kwargs)
        if course:
            # Update the question_number in the related Course
            total_marks = Question.objects.filter(course=course).aggregate(Sum('marks'))['marks__sum'] or 0
            course.total_marks = total_marks
            course.question_number = Question.objects.filter(course=course).count()
            # course.total_marks = Question.objects.filter(course=course).count()
            course.save()


from django.db import models

class Result(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, db_index=True)  # Adding index
    exam = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)  # Adding index
    schools = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='courseschool', blank=True, null=True)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)
    result_class = models.CharField(max_length=200, blank=True, null=True, db_index=True)  # Adding index
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True)  # ForeignKey to Session model
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)  # Adding index
    exam_type = models.ForeignKey(ExamType, on_delete=models.CASCADE, blank=True, null=True, db_index=True)  # Adding index
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_locked = models.BooleanField(default=False)  # Add this field
    id = models.AutoField(primary_key=True)

    class Meta:
        unique_together = ('student', 'exam', 'session', 'term', 'result_class', 'exam_type')

    def __str__(self):
        return f"{self.student}---{self.exam.course_name}---{self.exam_type}---{self.marks}"

