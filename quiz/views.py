
from sms.models import Courses
from django.shortcuts import redirect, render, get_object_or_404
from urllib.parse import unquote
from string import ascii_uppercase  # Import uppercase letters
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from .models import CourseGrade
from users.models import Profile
from .forms import MoveGroupForm
from .models import NewUser
# from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Subquery, OuterRef
from quiz.models import  Course
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_page


   
# @cache_page(60 * 15)
def move_group(request, from_group_name=None, to_group_name=None):
    user = request.user
    user_school = user.school  # Assuming `school` is related to the `NewUser` model

    if request.method == 'POST':
        form = MoveGroupForm(request.POST, user_school=user_school)
        if form.is_valid():
            from_group = form.cleaned_data['from_group']
            to_group = form.cleaned_data['to_group']

            # Logic for moving students between groups
            if to_group is None:
                # No target group specified, just re-assign within the same group
                users_to_update = NewUser.objects.filter(student_class=from_group.name, school=user_school)
                
                users_to_update.update(student_class=from_group.name)
                return redirect('quiz:move_group', from_group_name=from_group.name, to_group_name=from_group.name)
            else:
                # Move students from one group to another
                users_to_update = NewUser.objects.filter(student_class=from_group.name, school=user_school)
                users_to_update.update(student_class=to_group.name)
                print(users_to_update)
                to_group.students.add(*from_group.students.all())
                from_group.students.clear()
                return redirect('quiz:success_page')
    else:
        form = MoveGroupForm(user_school=user_school)

    return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})

# def move_group(request, from_group_name=None, to_group_name=None):
#     user = request.user
#     user_school = user.school  # Assuming `school` is related to the `NewUser` model

#     if request.method == 'POST':
#         form = MoveGroupForm(request.POST, user_school=user_school)
#         if form.is_valid():
#             from_group = form.cleaned_data['from_group']
#             to_group = form.cleaned_data['to_group']

#             if to_group is None:
#                 users_to_update = NewUser.objects.filter(student_class=from_group.name, school=user_school)
#                 users_to_update.update(student_class=from_group.name)
#                 return redirect('quiz:move_group', from_group_name=from_group.name, to_group_name=from_group.name)
#             else:
#                 users_to_update = NewUser.objects.filter(student_class=from_group.name, school=user_school)
#                 users_to_update.update(student_class=to_group.name)
#                 to_group.students.add(*from_group.students.all())
#                 from_group.students.clear()
#                 return redirect('quiz:success_page')
#     else:
#         form = MoveGroupForm(user_school=user_school)
    
#     return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})


# def move_group(request, from_group_name=None, to_group_name=None):
#     if request.method == 'POST':
#         form = MoveGroupForm(request.POST)
#         if form.is_valid():
#             from_group = form.cleaned_data['from_group']
#             to_group = form.cleaned_data['to_group']
           
#             if to_group is None:
#                 # Handle moving the group itself (from_group)
                
#                 users_to_update = NewUser.objects.filter(student_class=from_group.name)
#                 users_to_update.update(student_class=from_group.name)
#                 return redirect('quiz:move_group', from_group_name=from_group.name, to_group_name=from_group.name)
#             else:
               
#                 # Update student_class field for users in the from_group to the new group name
#                 users_to_update = NewUser.objects.filter(student_class=from_group.name)
#                 users_to_update.update(student_class=to_group.name)
#                 # Add all students from the source group to the destination group
#                 to_group.students.add(*from_group.students.all())
#                 # Optional: Clear the students from the source group
#                 from_group.students.clear()
#                 return redirect('quiz:success_page')
#     else:
#         form = MoveGroupForm()
#     return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})



def success_page_view(request):
    return render(request, 'quiz/dashboard/success_page.html')


# @cache_page(60 * 15)
# @login_required
# def take_exams_view(request):
#     course = TopicsAssessment.objects.get_queryset().order_by('id')
#     print("Course Title:", course.title)
#     for ta in TopicsAssessment.objects.all():
#         print("TopicsAssessment Course Name Title:", ta.course_name.title)
#         print("TopicsAssessment topic Name:", ta.course_name)
#     context = {
#         'courses':course,
#         'courses_title':ta.course_name.title,
#         'courses_name':ta.course_name
#     }
#     return render(request, 'quiz/dashboard/take_exams.html', context=context)

# def students_list(request):
#     students = Student.objects.all()
#     return render(request, 'quiz/dashboard/students_list.html', {'students': students})

# def create_group(request):
#     if request.method == 'POST':
#         form = GroupForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('quiz:group_list')
#     else:
#         form = GroupForm()
#     return render(request, 'quiz/dashboard/create_group.html', {'form': form})

# def promote_students(request, from_grade, to_grade):
#     students_to_promote = Student.objects.filter(grade=from_grade)
#     group, created = Group.objects.get_or_create(name=to_grade)
#     group.students.add(*students_to_promote)
#     return redirect('quiz:students_list')


# views.py

# from django.shortcuts import render, redirect
# from .forms import PromoteStudentsForm
# from .models import Student, Group

# def promote_students(request):
#     if request.method == 'POST':
#         form = PromoteStudentsForm(request.POST)
#         if form.is_valid():
#             students = form.cleaned_data['students']
#             destination_group_name = form.cleaned_data['destination_group']
#             print("Selected Students:", students)
#             print("Destination Group:", destination_group_name)
#             # Retrieve or create the destination group
#             destination_group, _ = Group.objects.get_or_create(name=destination_group_name)
#             for student in students:
#                 # Remove the student from their current groups
#                 student.group_set.clear()
#                 # Assign the selected students to the destination group
#                 destination_group.students.add(student)
#             print("Students assigned to group:", destination_group.students.all())
#             return redirect('quiz:success_page')  # Redirect to the success page
#     else:
#         form = PromoteStudentsForm()
#     return render(request, 'quiz/dashboard/promote_students.html', {'form': form})

# from django.shortcuts import render, redirect
# from .forms import PromoteStudentsForm
# from .models import Student, Group

# def promote_students(request, from_grade, to_grade):
#     if request.method == 'POST':
#         form = PromoteStudentsForm(request.POST)
#         if form.is_valid():
#             students = form.cleaned_data['students']
#             destination_group_name = form.cleaned_data['destination_group']
#             print("Selected Students:", students)
#             print("Destination Group:", destination_group_name)
#             destination_group, _ = Group.objects.get_or_create(name=destination_group_name)
#             for student in students:
#                 student.group_set.clear()
#                 destination_group.students.add(student)
#             print("Students assigned to group:", destination_group.students.all())
#             return redirect('quiz:success_page')
#     else:
#         # Fetch students from the specified grade
#         students_from_grade = Student.objects.filter(grade=from_grade)
#         # Pass initial data to the form
#         initial_data = {
#             'students': students_from_grade,  # Pre-select students
#             'destination_group': to_grade
#         }
#         form = PromoteStudentsForm(initial=initial_data)
    
#     # Pass from_grade and to_grade to the template context
#     context = {
#         'form': form,
#         'from_grade': from_grade,
#         'to_grade': to_grade,
#     }
#     return render(request, 'quiz/dashboard/promote_students.html', context)


# move to Group
# views.py

# views.py



# def move_group(request, from_group_name=None, to_group_name=None):
#     if request.method == 'POST':
#         form = MoveGroupForm(request.POST)
#         if form.is_valid():
#             from_group = form.cleaned_data['from_group']
#             to_group = form.cleaned_data['to_group']
#             if to_group is None:
#                 # Handle moving the group itself (from_group)
#                 return redirect('quiz:move_group', from_group_name=from_group.name, to_group_name=from_group.name)
#             else:
#                 # Add all students from the source group to the destination group
#                 to_group.students.add(*from_group.students.all())
#                 # Optional: Clear the students from the source group
#                 from_group.students.clear()
#                 # Redirect to success page or another view
#                 return redirect('quiz:success_page')
#     else:
#         form = MoveGroupForm()
#     return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})


# def move_group(request, from_group_name=None, to_group_name=None):
#     if request.method == 'POST':
#         form = MoveGroupForm(request.POST)
#         if form.is_valid():
#             from_group = form.cleaned_data['from_group']
#             to_group = form.cleaned_data['to_group']
#             if to_group is None:
#                 # Handle moving the group itself (from_group)
#                 return redirect('quiz:move_group', from_group_name=from_group.name, to_group_name=from_group.name)
#             else:
#                 # Add all students from the source group to the destination group
#                 to_group.students.add(*from_group.students.all())
#                 # Optional: Clear the students from the source group
#                 from_group.students.clear()
#                 # Redirect to success page or another view
#                 return redirect('quiz:success_page')
#     else:
#         form = MoveGroupForm()
#     return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})



# def add_student(request):
#     if request.method == 'POST':
#         form = StudentForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('quiz:add_student_success')  # Redirect to a success page
#     else:
#         form = StudentForm()
#     return render(request, 'quiz/dashboard/add_student.html', {'form': form})

# def add_student_success(request):
#     return render(request, 'quiz/dashboard/add_student_success.html')

# from django.shortcuts import render, redirect
# from .forms import PromoteStudentsForm
# from .models import Student, Group

# def promote_students(request):
#     if request.method == 'POST':
#         form = PromoteStudentsForm(request.POST)
#         if form.is_valid():
#             students = form.cleaned_data['students']
#             destination_group_name = form.cleaned_data['destination_group']
#             print("Selected Students:", students)
#             print("Destination Group:", destination_group_name)
#             # Retrieve or create the destination group
#             destination_group, _ = Group.objects.get_or_create(name=destination_group_name)
#             # Assign the selected students to the destination group
#             destination_group.students.add(*students)
#             print("Students assigned to group:", destination_group.students.all())
#             return redirect('quiz:success_page')  # Redirect to the success page
#     else:
#         form = PromoteStudentsForm()
#     return render(request, 'quiz/dashboard/promote_students.html', {'form': form})


# @cache_page(60 * 15)
# def success_page(request):
#     return render(request, 'quiz/dashboard/success_page.html')


# @login_required
# def start_exams_view(request, pk):
    
#     course = TopicsAssessment.objects.get(id = pk)
#     questions = QuestionAssessment.objects.filter(course = course).order_by('id')
#     topics = Topics.objects.all()
#     q_count = QuestionAssessment.objects.all().filter(course = course).count()
#     student = request.user.profile
#     results = ResultAssessment.objects.filter(exam = course, student = student).order_by('id')
#     paginator = Paginator(questions, 1000) # Show 25 contacts per page.
#     paginator_comp = Paginator(questions, 1) # Show 25 contacts per page.
#     page_number = request.GET.get('page')
    
#     page_obj = paginator.get_page(page_number)
   
#     page_obj_comp = paginator_comp.get_page(page_number)
#     letters = list(ascii_uppercase)

#     context = {
#         'course':course,
#         'questions':questions,
#         'q_count':q_count,
#         'page_obj':page_obj,
#         'page_obj_comp':page_obj_comp,
#         'results':results,
#         'letters':letters,
#         'completed':"letters",
      
#     }
#     if request.method == 'POST':
#         pass
#     response = render(request, 'quiz/dashboard/start_exams paginat.html', context=context)
#     response.set_cookie('course_id', course.id)
#     return response
     
# end of dashboard view


# @login_required
# def calculate_marks_view(request):
#     if request.COOKIES.get('course_id') is not None:
#         course_id = request.COOKIES.get('course_id')
#         course= TopicsAssessment.objects.get(id=course_id)
#         options = []  # List to store the selected options
#         total_marks=0
#         questions= QuestionAssessment.objects.get_queryset().filter(course=course).order_by('id')
#         for i in range(len(questions)):
            
#             # selected_ans = request.COOKIES.get(str(i+1))
#             selected_ans = request.POST.get(str(i+1))
#             options.append(selected_ans)  # Add selected option to the list
#             print("answers", selected_ans)
            
#             actual_answer = questions[i].answer
#             if selected_ans == actual_answer:
#                 total_marks = total_marks + questions[i].marks
#         student = Profile.objects.get(user_id=request.user.id)
#         result =ResultAssessment()
        
#         result.marks=total_marks 
#         result.exam=course
#         result.student=student
#         # options_str = ", ".join(str(option) if option is not None else "None" for option in options)
#         result.option = options  # Save selected options as a comma-separated string
        
#         # print("result2", options)
        
#         # m = ResultAssessment.objects.aggregate(Max('marks'))
#         # max_q = ResultAssessment.objects.filter(student_id = OuterRef('student_id'),exam_id = OuterRef('exam_id'),).order_by('-marks').values('id')
#         # max_result = ResultAssessment.objects.filter(id__in = Subquery(max_q[:1]), exam=course, student=student)
#         # score = 0
#         # print("t mark", total_marks)
#         print("result", result)
#         print("pass mar", course.pass_mark)
        
#         result.save()
#         # if result.marks >= course.pass_mark:
#         #     result.save()

#         # if total_marks > score:

#         # if request.method == 'POST':
#         #     Option1 = request.POST.get('1')
#         #     Option2 = request.POST.get('2')
#         #     Option3 = request.POST.get('3')
#         #     Option4 = request.POST.get('4')
       
#         return HttpResponseRedirect(reverse('quiz:start-exam', kwargs={'pk': course.pk}))
#     else:
#         return HttpResponseRedirect('take-exam')



# @login_required
# def view_result_view(request):
#     courses= TopicsAssessment.objects.get_queryset().order_by('id')
#     return render(request,'quiz/dashboard/view_result.html',{'courses':courses})


# from django.db.models import Count

# @login_required
# def check_marks_view(request,pk):
#     course= TopicsAssessment.objects.get(id=pk)
#     student = Profile.objects.get_queryset().order_by('id')
 
#     context = {
#         'results':student,
#         'course':course,
#         'st':request.user,
        
#     }
#     return render(request,'quiz/dashboard/check_marks.html', context)


# end

# views.py


# from .forms import StudentRegistrationForm

# def register_student(request):
#     if request.method == 'POST':
#         form = StudentRegistrationForm(request.user, request.POST)
#         if form.is_valid():
#             form.save()
#             # return redirect('quiz:school_dashboard')
#     else:
#         form = StudentRegistrationForm()

#     return render(request, 'quiz/dashboard/student_registration.html', {'form': form})


# def school_dashboard(request, pk):

#         # Example usage (in a view or wherever you generate the certificate)
#     course = Course.objects.get(pk=pk)  # Replace with the actual course instance
#     student = Student.objects.get(pk=pk)  # Replace with the actual student instance
#     # Get the relevant information for the certificate
#     student_info = course.get_student_info_for_certificate(student)

#     # Now you can use student_info in your certificate generation logic
#     if student_info:
#         school_name = student_info['school_name']
#         logo_url = student_info['logo_url']
#         signature_url = student_info['signature_url']
#         # Add more fields as needed
 
#     context = {
#         'course': course,
#         'student': student,
#         'student_info': student_info,
#     }
#     # context =  {
#     #     'school_name': school_name,
#     #     'logo_url': logo_url,
#     #     'signature_url': signature_url,
#     #     }

#     return render(request, 'quiz/dashboard/school_dashboard.html', context)
# from django.shortcuts import render
# from .models import Course
# from .models import Student

# from .models import Student

# def get_student_for_user(user):
#     try:
#         # Assuming there is a one-to-one relationship between User and Student
#         return Student.objects.get(user=user.profile)
#     except Student.DoesNotExist:
#         return None


# def school_dashboard(request, course_id):
#     # Assuming you have a function to get the current student based on the logged-in user
#     student = get_student_for_user(request.user)

#     if student:
#         course = get_object_or_404(Course, id=course_id)

#         # Get the relevant information for the certificate
#         student_info = course.get_student_info_for_certificate(student)

#         # Pass the information to the template
#         context = {
#             'course': course,
#             'student': student,
#             'student_info': student_info,
#         }

#         return render(request, 'quiz/dashboard/school_dashboard.html', context)
#     else:
#         # Handle the case where the user is not associated with a student
#         return render(request, 'error_template.html', {'error_message': 'User is not associated with a student'})
