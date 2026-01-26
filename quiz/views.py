
import os
from pyexpat.errors import messages
import re

from django.conf import settings

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

from .forms import BulkExamUpdateForm


@login_required
def update_school_exam_settings(request):
    school = getattr(request.user, "school", None)

    # If user has no school assigned
    if not school:
        messages.error(request, "You are not assigned to any school.")
        return redirect("dashboard")  # Change to your correct dashboard URL

    if request.method == "POST":
        form = BulkExamUpdateForm(request.POST)

        if form.is_valid():
            session = form.cleaned_data.get("session")
            term = form.cleaned_data.get("term")
            exam_type = form.cleaned_data.get("exam_type")

            courses = Course.objects.filter(schools=school)

            # Build data dict only with selected fields
            update_data = {}
            if session:
                update_data["session"] = session
            if term:
                update_data["term"] = term
            if exam_type:
                update_data["exam_type"] = exam_type

            # If user selected something, update
            if update_data:
                courses.update(**update_data)

                messages.success(
                    request,
                    "Exam settings updated successfully for all courses in your school."
                )
            else:
                messages.warning(
                    request,
                    "No changes were made because no fields were selected."
                )

            return redirect("quiz:update_school_exam_settings")

    else:
        form = BulkExamUpdateForm()

    return render(request, "quiz/dashboard/update_school_exam_settings.html", {
        "form": form,
        "school": school,
    })


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


# views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import School
from .forms import SchoolForm
@login_required(login_url='teacher:teacher_login')
def edit_school(request):
    # Get the examiner's school
    school = getattr(request.user, 'school', None)

    if not school:
        return HttpResponseForbidden("You are not assigned to any school.")

    if request.method == 'POST':
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School updated successfully!")
            return redirect('quiz:edit_school')  # stay on the same page
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SchoolForm(instance=school)

    context = {
        'form': form,
        'school': school,
    }
    return render(request, 'quiz/dashboard/edit_school.html', context)


import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from openai import OpenAI
# --- TEMPORARY: Use API key directly for testing ---

# quiz/views.py
import uuid
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from .models import GenerationJob
from .tasks import generate_ai_questions_task

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

@login_required
def ai_summative_assessment(request):
    # Ensure teacher exists
    try:
        teacher = request.user.teacher
    except:
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Teacher account not found.'})
        messages.error(request, "Teacher account not found.")
        return redirect("dashboard")

    courses = teacher.subjects_taught.all()

    if request.method == "POST" and request.POST.get("confirm_save") == "1":
        total_questions = int(request.POST.get("total_questions", 0))
        course_id = request.POST.get("course_id")
        marks = int(request.POST.get("marks", 1))

        try:
            course_detail = Course.objects.get(id=course_id, teachers=teacher)
        except Course.DoesNotExist:
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'You do not have permission to add questions to this course.'})
            messages.error(request, "You do not have permission to add questions to this course.")
            return redirect("quiz:ai_summative_assessment")

        saved = 0
        for i in range(1, total_questions + 1):
            question_text = request.POST.get(f"question_{i}", "").strip()
            options = [
                request.POST.get(f"option1_{i}", "").strip(),
                request.POST.get(f"option2_{i}", "").strip(),
                request.POST.get(f"option3_{i}", "").strip(),
                request.POST.get(f"option4_{i}", "").strip(),
            ]
            answer = request.POST.get(f"answer_{i}", "Option1").strip()

            if question_text and all(options):
                Question.objects.create(
                    course=course_detail,
                    marks=marks,
                    question=question_text,
                    option1=options[0],
                    option2=options[1],
                    option3=options[2],
                    option4=options[3],
                    answer=answer
                )
                saved += 1

        message_text = f"{saved} question{'s' if saved != 1 else ''} saved successfully." if saved > 0 else "No questions were saved. Please check your entries."

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success' if saved > 0 else 'warning',
                'message': message_text
            })

        if saved > 0:
            messages.success(request, message_text)
        else:
            messages.warning(request, message_text)

        return redirect("quiz:ai_summative_assessment")

    return render(request, "quiz/dashboard/ai_summative_assessment.html", {
        "courses": courses,
    })


@login_required
def start_generation(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    # Parse POST data (supporting both form-data and JSON)
    try:
        body_data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body_data = {}

    course_id = request.POST.get("course") or body_data.get("course")
    num_questions = request.POST.get("num_questions") or body_data.get("num_questions")
    difficulty = request.POST.get("difficulty") or body_data.get("difficulty", "medium")
    marks = request.POST.get("marks") or body_data.get("marks", 1)
    learning_objectives = request.POST.get("learning_objectives") or body_data.get("learning_objectives", "")

    if not course_id or not num_questions or not learning_objectives:
        return JsonResponse({"error": "Missing course, num_questions, or learning objectives"}, status=400)

    # Create a new generation job
    job_id = str(uuid.uuid4())
    GenerationJob.objects.create(job_id=job_id, status="pending")

    # Launch Celery task with learning objectives
    generate_ai_questions_task.delay(
        job_id, 
        int(course_id), 
        int(num_questions), 
        difficulty, 
        int(marks),
        learning_objectives
    )

    return JsonResponse({"job_id": job_id, "message": "Generation started"})


# @login_required
# def ai_summative_assessment(request):

#     # Get teacher object
#     try:
#         teacher = request.user.teacher
#     except:
#         messages.error(request, "Teacher account not found.")
#         return redirect("dashboard")

#     # Teacher sees only the quiz Courses he teaches (subjects_taught)
#     courses = teacher.subjects_taught.all()

#     if request.method == "POST" and request.POST.get("confirm_save") == "1":
#         total_questions = int(request.POST.get("total_questions", 0))
#         course_id = request.POST.get("course_id")
#         marks = int(request.POST.get("marks", 1))

#         # Teacher must only save questions for HIS courses
#         try:
#             course_detail = Course.objects.get(id=course_id, teachers=teacher)
#         except Course.DoesNotExist:
#             messages.error(request, "You do not have permission to add questions to this course.")
#             return redirect('quiz:ai_summative_assessment')

#         saved = 0

#         for i in range(1, total_questions + 1):
#             question_text = request.POST.get(f"question_{i}", "").strip()
#             options = [
#                 request.POST.get(f"option1_{i}", "").strip(),
#                 request.POST.get(f"option2_{i}", "").strip(),
#                 request.POST.get(f"option3_{i}", "").strip(),
#                 request.POST.get(f"option4_{i}", "").strip(),
#             ]
#             answer = request.POST.get(f"answer_{i}", "Option1").strip()

#             if question_text and all(options):
#                 Question.objects.create(
#                     course=course_detail,
#                     marks=marks,
#                     question=question_text,
#                     option1=options[0],
#                     option2=options[1],
#                     option3=options[2],
#                     option4=options[3],
#                     answer=answer
#                 )
#                 saved += 1

#         # SUCCESS MESSAGE
#         if saved > 0:
#             messages.success(request, f"{saved} questions saved successfully.")
#         else:
#             messages.warning(request, "No questions were saved. Please check your entries.")

#         return redirect('quiz:ai_summative_assessment')

#     return render(request, "quiz/dashboard/ai_summative_assessment.html", {
#         "courses": courses
#     })



#working for all subjects

# @login_required
# def ai_summative_assessment(request):
#     # Renders the page (the generation is triggered via AJAX)
#     courses = Courses.objects.all()

#     # Handle confirm_save post (user confirmed preview and wants to persist)
#     if request.method == "POST" and request.POST.get("confirm_save") == "1":
#         total_questions = int(request.POST.get("total_questions", 0))
#         course_id = request.POST.get("course_id")
#         marks = int(request.POST.get("marks", 1))
#         try:
#             course_obj = Courses.objects.get(id=course_id)
#         except Courses.DoesNotExist:
#             messages.error(request, "Invalid course selected.")
#             return redirect('quiz:ai_summative_assessment')

#         course_detail = Course.objects.filter(course_name=course_obj).first()
#         saved = 0
#         for i in range(1, total_questions + 1):
#             question_text = request.POST.get(f"question_{i}", "").strip()
#             options = [
#                 request.POST.get(f"option1_{i}", "").strip(),
#                 request.POST.get(f"option2_{i}", "").strip(),
#                 request.POST.get(f"option3_{i}", "").strip(),
#                 request.POST.get(f"option4_{i}", "").strip(),
#             ]
#             answer = request.POST.get(f"answer_{i}", "Option1").strip()
#             if question_text and all(options):
#                 Question.objects.create(
#                     course=course_detail,
#                     marks=marks,
#                     question=question_text,
#                     option1=options[0],
#                     option2=options[1],
#                     option3=options[2],
#                     option4=options[3],
#                     answer=answer
#                 )
#                 saved += 1

#         messages.success(request, f"{saved} questions saved successfully.")
#         return redirect('quiz:ai_summative_assessment')

#     return render(request, "quiz/dashboard/ai_summative_assessment.html", {
#         "courses": courses
#     })

# @login_required
# def start_generation(request):
#     if request.method != "POST":
#         return HttpResponseBadRequest("Invalid method")

#     data = request.POST or request.body
#     # If fetch uses form data, read POST; if JSON, parse body
#     course_id = request.POST.get("course") or json.loads(request.body).get("course")
#     num_questions = request.POST.get("num_questions") or json.loads(request.body).get("num_questions")
#     difficulty = request.POST.get("difficulty") or json.loads(request.body).get("difficulty", "medium")
#     marks = request.POST.get("marks") or json.loads(request.body).get("marks", 1)

#     if not course_id or not num_questions:
#         return JsonResponse({"error":"Missing course or num_questions"}, status=400)

#     job_id = str(uuid.uuid4())
#     GenerationJob.objects.create(job_id=job_id, status="pending")
#     # launch celery task
#     generate_ai_questions_task.delay(job_id, int(course_id), int(num_questions), difficulty, int(marks))

#     return JsonResponse({"job_id": job_id, "message": "Generation started"})



@login_required
def job_status(request, job_id):
    try:
        job = GenerationJob.objects.get(job_id=job_id)
    except GenerationJob.DoesNotExist:
        return JsonResponse({"error":"Job not found"}, status=404)

    return JsonResponse({
        "job_id": job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error
    })


# @login_required
# def ai_summative_assessment(request):
#     courses = Courses.objects.all()

#     if request.method == 'POST' and request.POST.get("confirm_save") == "1":
#         # --- save manually entered questions (same as before) ---
#         total_questions = int(request.POST.get("total_questions", 0))
#         course_id = request.POST.get("course_id")
#         marks = int(request.POST.get("marks", 1))

#         try:
#             course_obj = Courses.objects.get(id=course_id)
#         except Courses.DoesNotExist:
#             messages.error(request, "Invalid course selected.")
#             return redirect('quiz:ai_summative_assessment')

#         course_detail = Course.objects.filter(course_name=course_obj).first()
#         if not course_detail:
#             messages.error(request, "No course details found for the selected course.")
#             return redirect('quiz:ai_summative_assessment')

#         saved = 0
#         for i in range(1, total_questions + 1):
#             question_text = request.POST.get(f"question_{i}", "").strip()
#             options = [
#                 request.POST.get(f"option1_{i}", "").strip(),
#                 request.POST.get(f"option2_{i}", "").strip(),
#                 request.POST.get(f"option3_{i}", "").strip(),
#                 request.POST.get(f"option4_{i}", "").strip(),
#             ]
#             answer = request.POST.get(f"answer_{i}", "Option1").strip()

#             if question_text and all(options):
#                 Question.objects.create(
#                     course=course_detail,
#                     marks=marks,
#                     question=question_text,
#                     option1=options[0],
#                     option2=options[1],
#                     option3=options[2],
#                     option4=options[3],
#                     answer=answer
#                 )
#                 saved += 1

#         messages.success(request, f"{saved} questions saved successfully.")
#         return redirect('quiz:ai_summative_assessment')

#     elif request.method == 'POST':
#         # --- AI generated questions ---
#         course_id = request.POST.get('course')
#         num_questions = int(request.POST.get('num_questions', 5))
#         marks = int(request.POST.get('marks', 1))
#         difficulty = request.POST.get('difficulty', 'medium').lower()

#         try:
#             course_obj = Courses.objects.get(id=course_id)
#         except Courses.DoesNotExist:
#             messages.error(request, "Invalid course selected.")
#             return redirect('quiz:ai_summative_assessment')

#         course_title = course_obj.title or ""
#         course_detail = Course.objects.filter(course_name=course_obj).first()
#         if not course_detail:
#             messages.error(request, "No course details found for this course.")
#             return redirect('quiz:ai_summative_assessment')

#         prompt = f"""
#         You are an expert in learning assessment.

#         Generate {num_questions} {difficulty}-level multiple-choice questions based strictly on the topic '{course_title}'.
#         Strictly follow this format (no explanations, no numbering):

#         Question: <question text>
#         A. <option>
#         B. <option>
#         C. <option>
#         D. <option>
#         Answer: <correct option letter>
#         """

#         try:
#             response = client.chat.completions.create(
#                 model="gpt-4o-mini",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant that generates professional learning quiz questions."},
#                     {"role": "user", "content": prompt},
#                 ],
#                 max_tokens=6000,
#                 temperature=0,
#             )

#             if not response.choices:
#                 messages.error(request, "OpenAI returned no content.")
#                 return redirect('quiz:ai_summative_assessment')

#             questions_text = response.choices[0].message.content.strip()
#             blocks = re.split(r'\n\s*\n', questions_text)

#             preview_questions = []
#             skipped_blocks = 0

#             for block in blocks:
#                 lines = [line.strip() for line in block.split("\n") if line.strip()]
#                 if len(lines) == 6:
#                     question_text = lines[0].replace("Question:", "").strip()
#                     options = [line.split('. ', 1)[1].strip() for line in lines[1:5]]
#                     answer_letter = lines[5].split(':')[-1].strip().upper()
#                     answer_map = {'A': 'Option1', 'B': 'Option2', 'C': 'Option3', 'D': 'Option4'}
#                     answer = answer_map.get(answer_letter, 'Option1')

#                     preview_questions.append({
#                         'question': question_text,
#                         'option1': options[0],
#                         'option2': options[1],
#                         'option3': options[2],
#                         'option4': options[3],
#                         'answer': answer
#                     })
#                 else:
#                     skipped_blocks += 1

#             if skipped_blocks > 0:
#                 messages.warning(request, f"Skipped {skipped_blocks} malformed question blocks from AI response.")

#             return render(request, 'quiz/dashboard/ai_summative_assessment.html', {
#                 'courses': courses,
#                 'preview_questions': preview_questions,
#                 'course_id': course_id,
#                 'marks': marks,
#             })

#         except Exception as e:
#             messages.error(request, f"OpenAI error: {str(e)}")
#             return redirect('quiz:ai_summative_assessment')

#     # GET request
#     return render(request, 'quiz/dashboard/ai_summative_assessment.html', {'courses': courses})
