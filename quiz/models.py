from django.db import models
# from student.models import Student
from users.models import Profile, NewUser
from cloudinary.models import CloudinaryField
from sms.models import Courses as smscourses
from tinymce.models import HTMLField
from sms.models import Courses, Topics


# assessment models 

class TopicsAssessment(models.Model):
#    course_name = models.CharField(max_length=50, unique= True)
   course_name = models.ForeignKey(Topics,on_delete=models.CASCADE, blank=True, null= True)
   question_number = models.PositiveIntegerField()
   total_marks = models.PositiveIntegerField()
   pass_mark = models.PositiveIntegerField(null=True)
   created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
   updated = models.DateTimeField(auto_now=True, blank=True, null= True)
   id = models.AutoField(primary_key=True)
   
   def __str__(self):
        return f'{self.course_name}'


from tinymce.models import HTMLField


class QuestionAssessment(models.Model):
    course=models.ForeignKey(TopicsAssessment,on_delete=models.CASCADE)
    marks=models.PositiveIntegerField()
    # question= models.TextField( blank=True, null= True)
    question= HTMLField( blank=True, null= True)
    img_quiz = CloudinaryField('image', blank=True, null= True)
    option1 = HTMLField(max_length=500, null= True)
    option2 = HTMLField(max_length=500, null= True)
    option3 = HTMLField(max_length=500, null= True)
    option4 = HTMLField(max_length=500, null= True)

    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.course} | {self.question}"
    
class ResultAssessment(models.Model):

    student = models.ForeignKey(Profile,on_delete=models.CASCADE)
    exam = models.ForeignKey(TopicsAssessment,on_delete=models.CASCADE)
    option = models.CharField(max_length=100,blank=True, null= True)
    # smscourses = models.ForeignKey(smscourses,on_delete=models.CASCADE, blank=True, null= True)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)
    # pass_mark = models.PositiveIntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    id = models.AutoField(primary_key=True)
    def __str__(self):
        return f"{self.student}---{self.exam.course_name}----{self.marks}"

# end


class Course(models.Model):


   room_name = models.CharField(max_length=100,blank=True, null= True)
   schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='course', blank=True, null=True)
   course_name = models.ForeignKey(Courses,on_delete=models.CASCADE, blank=True, null= True)
   question_number = models.PositiveIntegerField()
   course_pay = models.BooleanField(default=False)
   total_marks = models.PositiveIntegerField()
   num_attemps = models.PositiveIntegerField(default=4)
   pass_mark = models.PositiveIntegerField(null=True)
   show_questions = models.PositiveIntegerField(default=10)
   duration_minutes = models.PositiveIntegerField(default=10)  # Add this field for quiz duration
   created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
   updated = models.DateTimeField(auto_now=True, blank=True, null= True)
   id = models.AutoField(primary_key=True)

   class Meta:
        verbose_name = 'Exam'
        verbose_name_plural = 'Exams'

   def __str__(self):
        return f'{self.course_name}'
   
   def get_questions(self):
        return self.question_set.all()[:self.show_questions]


# class List_Subjects(models.Model):

#    name = models.CharField(max_length=225, blank=True, null= True)
#    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
#    updated = models.DateTimeField(auto_now=True, blank=True, null= True)

#    def __str__(self):
#         return f'{self.name}'

# from django.db import models


# class Subjects(models.Model):
#     schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='subjects', blank=True, null=True)
#     course_name = models.ForeignKey(List_Subjects,on_delete=models.CASCADE, blank=True, null= True) # Change ForeignKey to ManyToManyField
#     question_number = models.PositiveIntegerField(blank=True)
#     total_marks = models.PositiveIntegerField(blank=True)
#     pass_mark = models.PositiveIntegerField(blank=True, null=True)
#     duration_minutes = models.PositiveIntegerField(default=20, blank=True)
#     created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null=True)

#     def __str__(self):
#         return f'{self.course_name}' # Modify to join course names

    
# class Subjects(models.Model):
#     schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='subjects', blank=True, null=True)
#     course_name = models.ManyToManyField(List_Subjects, blank=True)
#     question_number = models.PositiveIntegerField(blank=True)
#     total_marks = models.PositiveIntegerField(blank=True)
#     pass_mark = models.PositiveIntegerField(blank=True, null=True)
#     duration_minutes = models.PositiveIntegerField(default=20, blank=True)  # Add this field for quiz duration
#     created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null=True)
#     id = models.AutoField(primary_key=True)

#     def __str__(self):
#         school_name = self.schools.school_name if self.schools else "Unknown School"
#         course_names = '\n'.join(str(course) for course in self.course_name.all())
#         return f"{course_names}"

# class AddSubject(models.Model):
#     schools = models.ForeignKey("quiz.School", on_delete=models.SET_NULL, related_name='addsubjects', blank=True, null=True)
#     course_name = models.ManyToManyField(List_Subjects, blank=True)
#     created = models.DateTimeField(auto_now_add=True, null=True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null=True)
#     id = models.AutoField(primary_key=True)

#     def __str__(self):
#         # Retrieve all course names associated with this AddSubject instance
#         course_names = '\n'.join(str(course) for course in self.course_name.all())
#         return course_names  # Return the concatenated course names separated by newlines

# Import your NewUser model here

class CourseGrade(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    students = models.ManyToManyField(NewUser, related_name='course_grades', blank= True)  # Change to ManyToManyField for multiple students
    subjects = models.ManyToManyField(Courses, related_name='course_grade', blank= True)
    
    class Meta:
        verbose_name = 'Student class'
        verbose_name_plural = 'student classes'
        
    def __str__(self):
        course_names = '\n'.join(str(course) for course in self.subjects.all())
        return f'{course_names}'


# class CourseGrade(models.Model):
#     name = models.CharField(max_length=200, blank=True, null=True)
#     email = models.OneToOneField(NewUser, on_delete=models.CASCADE, unique=True, related_name='student_groups', blank=True, null=True)
#     subjects = models.ManyToManyField(Courses, related_name='coursegrade')

#     def __str__(self):
#         course_names = '\n'.join(str(course) for course in self.subjects.all())
#         return f'{self.name} - {course_names}'


# class Group(models.Model):
#     name = models.CharField(max_length=200, blank=True, null=True)
#     # email = models.OneToOneField(NewUser, on_delete=models.CASCADE, unique=True, related_name='student_groups', blank=True, null=True)
#     subjects = models.ManyToManyField(AddSubject, related_name='groups')

#     def __str__(self):
#         course_names = '\n'.join(str(course) for course in self.subjects.all())
#         return f'{self.name} - {course_names}'
    




class School(models.Model):
    name = models.CharField(max_length=255)
    # students = models.ManyToManyField(Student, blank=True, related_name='school')
    # groups = models.ManyToManyField('quiz.Group', blank=True, null= True)
    school_name = models.CharField(max_length=255)
    course_pay = models.BooleanField(default=False)
    customer = models.BooleanField(default=True)
    portfolio = models.CharField(max_length=255, blank=True, null= True)
    logo = CloudinaryField('school_logos', blank=True, null= True)
    principal_signature = CloudinaryField('principal_signatures', blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)

    def __str__(self):
        return f"{self.school_name}"


# class Student(models.Model):
#     name = models.CharField(max_length=100, blank=True)
#     # email = models.CharField(max_length=100, blank=True)
#     email = models.OneToOneField(NewUser, on_delete=models.CASCADE, unique=True, related_name='student_profile', blank=True, null=True)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students', blank=True, null=True)
#     school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students', blank=True, null=True)
#     # subjects = models.ManyToManyField("quiz.Subjects" , related_name='students', blank=True)

#     def __str__(self):
#         return f'{self.name} - {self.email}'

# class Student(models.Model):
#     user = models.OneToOneField(Profile, on_delete=models.CASCADE, blank=True, null=True)
#     school = models.ForeignKey(School, on_delete=models.SET_NULL, blank=True, null=True)
#     name = models.CharField(max_length=255)
#     admission_no = models.CharField(max_length=20, unique=True)
#     date_of_birth = models.DateField()
#     address = models.CharField(max_length=255)
#     # course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)

#     def __str__(self):
#         school_name = getattr(self.school, 'school_name', '')
#         return f'{self.name} - {self.school.school_name} {self.id}'


class Question(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE,blank=True, null= True)
    marks=models.PositiveIntegerField(blank=True, null= True)
    # question= models.TextField( blank=True, null= True)
    question= HTMLField( blank=True, null= True)
    img_quiz = CloudinaryField('image', blank=True, null= True)
    option1 = HTMLField(max_length=500, blank=True, null= True)
    option2 = HTMLField(max_length=500, blank=True, null= True)
    option3 = HTMLField(max_length=500, blank=True, null= True)
    option4 = HTMLField(max_length=500, blank=True, null= True)

    cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
    answer=models.CharField(max_length=200,choices=cat,blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.course} | {self.question}"


# class Subject_Question(models.Model):
#     course=models.ForeignKey(Subjects,on_delete=models.CASCADE)
#     marks=models.PositiveIntegerField()
#     # question= models.TextField( blank=True, null= True)
#     question= HTMLField( blank=True, null= True)
#     img_quiz = CloudinaryField('image', blank=True, null= True)
#     option1 = HTMLField(max_length=500, null= True)
#     option2 = HTMLField(max_length=500, null= True)
#     option3 = HTMLField(max_length=500, null= True)
#     option4 = HTMLField(max_length=500, null= True)

#     cat=(('Option1','Option1'),('Option2','Option2'),('Option3','Option3'),('Option4','Option4'))
#     answer=models.CharField(max_length=200,choices=cat)
#     created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null= True)
#     id = models.AutoField(primary_key=True)

#     def __str__(self):
#         return f"{self.course} | {self.question}"


# class Subject_Result(models.Model):

#     student = models.ForeignKey(Profile,on_delete=models.CASCADE)
#     exam = models.ForeignKey(Subjects,on_delete=models.CASCADE)
#     # smscourses = models.ForeignKey(smscourses,on_delete=models.CASCADE, blank=True, null= True)
#     marks = models.PositiveIntegerField()
#     date = models.DateTimeField(auto_now=True)
#     # pass_mark = models.PositiveIntegerField(null=True)
#     created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
#     updated = models.DateTimeField(auto_now=True, blank=True, null= True)
#     id = models.AutoField(primary_key=True)
#     def __str__(self):
#         return f"{self.student}---{self.exam.course_name}----{self.marks}"


class Result(models.Model):

    student = models.ForeignKey(Profile,on_delete=models.CASCADE)
    exam = models.ForeignKey(Course,on_delete=models.CASCADE)
    # smscourses = models.ForeignKey(smscourses,on_delete=models.CASCADE, blank=True, null= True)
    marks = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now=True)
    # pass_mark = models.PositiveIntegerField(null=True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null= True)
    updated = models.DateTimeField(auto_now=True, blank=True, null= True)
    id = models.AutoField(primary_key=True)
    def __str__(self):
        return f"{self.student}---{self.exam.course_name}----{self.marks}"


class Certificate_note(models.Model):
    
    note = models.TextField(blank=True, null= True)
    created = models.DateTimeField(auto_now_add=True, blank=True, null= True)
    id = models.AutoField(primary_key=True)
    
    def __str__(self):
        return f"{self.note}"


