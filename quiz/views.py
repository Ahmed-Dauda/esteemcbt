
from pyexpat.errors import messages
from sms.models import Courses
from django.shortcuts import redirect, render, get_object_or_404
from urllib.parse import unquote
from string import ascii_uppercase  # Import uppercase letters
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from .models import CourseGrade
from users.models import Profile, NewUser
from .forms import MoveGroupForm

# from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Subquery, OuterRef
from quiz.models import  Course
from django.http import HttpResponseRedirect
from django.views.decorators.cache import cache_page
from django.shortcuts import render, get_object_or_404, redirect
from .models import Question
from teacher.forms import QuestionForm
from django.contrib import messages


def examiner_course_list(request):
    school = request.user.school
    courses = Course.objects.filter(schools=school)
    return render(request, 'quiz/dashboard/examiner_course_list.html', {'courses': courses})

def examiner_course_questions(request, course_id):
    school = request.user.school
    course = get_object_or_404(Course, pk=course_id, schools=school)
    questions = Question.objects.filter(course=course)
    return render(request, 'quiz/dashboard/examiner_course_questions.html', {'course': course, 'questions': questions})



def examiner_question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk, course__schools=request.user.school)
    if request.method == "POST":
        form = QuestionForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            form.save()
            # Redirect to the course-specific question list after editing
            return redirect('quiz:examiner_course_questions', course_id=question.course.pk)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'quiz/dashboard/examiner_question_edit.html', {'form': form})

def examiner_question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk, course__schools=request.user.school)
    course_id = question.course.pk
    if request.method == "POST":
        question.delete()
        return redirect('quiz:examiner_course_questions', course_id=course_id)
    return render(request, 'quiz/dashboard/examiner_question_confirm_delete.html', {'question': question})


@login_required(login_url='teacher:teacher_login')
def move_group(request):
    user_school = request.user.school

    if request.method == 'POST':
        form = MoveGroupForm(request.POST, user_school=user_school)
        if form.is_valid():
            from_group = form.cleaned_data['from_group']
            to_group = form.cleaned_data['to_group']

            # Double-check target class is empty
            if to_group.students.exists():
                messages.error(request, f"Target class '{to_group.name}' is not empty! Please select an empty class.")
                return redirect('quiz:move_group')

            # Move students
            students_to_move = NewUser.objects.filter(student_class=from_group.name, school=user_school)
            count = students_to_move.count()

            for student in students_to_move:
                student.student_class = to_group.name
                student.save()

            # Update ManyToManyField
            to_group.students.add(*from_group.students.all())
            from_group.students.clear()

            messages.success(request, f"{count} student(s) successfully moved from '{from_group.name}' to '{to_group.name}'.")
            return redirect('quiz:move_group')
    else:
        form = MoveGroupForm(user_school=user_school)

    return render(request, 'quiz/dashboard/move_group_form.html', {'form': form})



def success_page_view(request):
    return render(request, 'quiz/dashboard/success_page.html')


