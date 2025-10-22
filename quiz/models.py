from django.db import models
# from student.models import Student
from users.models import Profile, NewUser
from cloudinary.models import CloudinaryField
# from sms.models import Courses as smscourses
from tinymce.models import HTMLField
# from sms.models import Courses
from sms.models import Session, Term, ExamType


class Course(models.Model):


    learning_objectives = models.TextField(blank=True,null=True,default='Input your learning objectives')
    ai_question_num = models.PositiveIntegerField(default=500,verbose_name="Number of AI Questions", blank=True, null=True)
    
    room_name = models.CharField(max_length=100, blank=True, null=True)
    schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='course', blank=True, null=True, db_index=True)
    course_name = models.ForeignKey("sms.Courses", on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    question_number = models.PositiveIntegerField(blank=True, null=True)
    course_pay = models.BooleanField(default=False)
    full_screen = models.BooleanField(default=False)
    total_marks = models.PositiveIntegerField(blank=True, null=True)
    session = models.ForeignKey("sms.Session", on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    term = models.ForeignKey("sms.Term", on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    exam_type = models.ForeignKey("sms.ExamType", on_delete=models.CASCADE, blank=True, null=True, db_index=True)
    num_attemps = models.PositiveIntegerField(default=4)
    show_questions = models.PositiveIntegerField(default=10)
    duration_minutes = models.PositiveIntegerField(default=10)
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    id = models.AutoField(primary_key=True)

    class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'
        ordering = ['course_name__title']
        indexes = [
            models.Index(fields=['schools']),
            models.Index(fields=['course_name']),
            models.Index(fields=['session']),
            models.Index(fields=['term']),
            models.Index(fields=['exam_type']),
        ]
        # unique_together can be uncommented and applied if needed for preventing duplicates:
        # unique_together = ('course_name', 'session', 'term', 'schools', 'exam_type')

    def save(self, *args, **kwargs):
        if self.total_marks != self.show_questions:
            self.show_questions = self.total_marks
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.schools} - {self.course_name} - {self.session} - {self.term} - {self.exam_type}'

    def get_questions(self):
        return self.question_set.all()[:self.show_questions]


from django.core.exceptions import ValidationError

class CourseGrade(models.Model):
    schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='coursegrade', blank=True, null=True, db_index=True)  # 🔍 Faster lookup by school
    name = models.CharField(max_length=140, blank=True, null=True, db_index=True)  # 🔍 Faster filtering/searching by class name
    students = models.ManyToManyField(NewUser, related_name='course_grades', blank=True)
    # session = models.ForeignKey(Session, on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    subjects = models.ManyToManyField(Course, related_name='course_grade')
    is_active = models.BooleanField(default=True, db_index=True)  # 🔍 Fast filtering of active classes
    id = models.AutoField(primary_key=True)

    class Meta:
        verbose_name = 'Student class'
        verbose_name_plural = 'student classes'
        indexes = [
            models.Index(fields=['schools']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name if self.name else 'Unnamed Class'


class School(models.Model):
    name = models.CharField(max_length=255, db_index=True)  # Indexed for fast lookup
    school_name = models.CharField(max_length=255, db_index=True)  # Often filtered/joined

    course_pay = models.BooleanField(default=False, db_index=True)  # Useful for filtering
    customer = models.BooleanField(default=True, db_index=True)     # Useful if used in business logic

    school_motto = models.CharField(max_length=255, blank=True, null=True)
    school_address = models.CharField(max_length=355, blank=True, null=True)
    portfolio = models.CharField(max_length=255, blank=True, null=True)

    logo = CloudinaryField('school_logos', blank=True, null=True)
    principal_signature = CloudinaryField('principal_signatures', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

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

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['school_name']),
            models.Index(fields=['course_pay']),
            models.Index(fields=['customer']),
        ]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create defaults only when the school is new
        if is_new:
            Session.create_defaults_for_school(self)
            Term.create_defaults_for_school(self)
            ExamType.create_defaults_for_school(self)    


from django.db import models
from django.db.models import F
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete

            
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class StudentExamSession(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    question_order = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.course}"
    


class Question(models.Model):
    course = models.ForeignKey(
        'Course', on_delete=models.CASCADE, blank=True, null=True, db_index=True
    )  # ✅ index added

    marks = models.PositiveIntegerField(null=True,default=1,validators=[MinValueValidator(1), MaxValueValidator(1)],
        help_text="This field is locked to 1 mark."
    )

    question = HTMLField(blank=True, null=True)
    img_quiz = CloudinaryField('image', blank=True, null=True)

    option1 = HTMLField(max_length=500, blank=True, null=True)
    option2 = HTMLField(max_length=500, blank=True, null=True)
    option3 = HTMLField(max_length=500, blank=True, null=True)
    option4 = HTMLField(max_length=500, blank=True, null=True)

    OPTION_CHOICES = [
        ('Option1', 'Option1'),
        ('Option2', 'Option2'),
        ('Option3', 'Option3'),
        ('Option4', 'Option4'),
    ]
    answer = models.CharField(
        max_length=200, choices=OPTION_CHOICES, blank=True, null=True
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.course} | {self.question[:30]}"

    def save(self, *args, **kwargs):
        self.marks = 1  # Ensure marks is always set to 1
        super().save(*args, **kwargs)
        if self.course:
            total_marks = Question.objects.filter(course=self.course).aggregate(Sum('marks'))['marks__sum'] or 0
           
            self.course.question_number = Question.objects.filter(course=self.course).count()
            # self.course.total_marks = Question.objects.filter(course = self.course).count()
            self.course.save()

    def delete(self, *args, **kwargs):
        course = self.course
        super().delete(*args, **kwargs)
        if course:
            # Update question_number after deletion
            course.question_number = Question.objects.filter(course=course).count()
            course.save()

@receiver(post_delete, sender=Question)
def update_course_on_question_delete(sender, instance, **kwargs):
    if instance.course:
        update_course_fields(instance.course)

def update_course_fields(course):
    questions_count = Question.objects.filter(course=course).count()
    course.question_number = questions_count
    course.save()



from django.db import models


class Result(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, db_index=True)
    exam = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    schools = models.ForeignKey(School, on_delete=models.SET_NULL, related_name='courseschool', blank=True, null=True)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)

    result_class = models.CharField(max_length=300, blank=True, null=True, db_index=True)
    session = models.ForeignKey("sms.Session", on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    term = models.ForeignKey("sms.Term", on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    exam_type = models.ForeignKey("sms.ExamType", on_delete=models.CASCADE, blank=True, null=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'exam', 'session', 'term', 'result_class', 'exam_type')
        ordering = ['student__first_name','student__last_name', 'exam__course_name']  
  
    def __str__(self):
        return f"{self.student}---{self.exam.course_name}---{self.exam_type}---{self.marks}"


# models.py

class StudentAnswer(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=200)
    is_correct = models.BooleanField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.result.student.user.username} | Q{self.question.id} | {self.selected_answer}"


# class ExamsRules(models.Model):
#     # school_name = models.ForeignKey(
#     #     School, on_delete=models.SET_NULL,
#     #     related_name='examrules', blank=True, null=True
#     # )
#     rules = models.TextField(blank=True, null=True)
#     action = models.TextField(blank=True, null=True)
#     created = models.DateTimeField(auto_now_add=True, null=True)
#     updated = models.DateTimeField(auto_now=True, null=True)
#     id = models.AutoField(primary_key=True)
