from django.shortcuts import render, redirect, get_object_or_404
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group, AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from datetime import date, timedelta
from teacher import forms as QFORM
from users.models import NewUser
from quiz.models import Course, Result, Question
from django.utils.datastructures import MultiValueDictKeyError
from .models import SampleCodes, Teacher
from .forms import JSONForm, TeacherSignupForm, TeacherLoginForm, QuestionForm, UploadCSVForm
from django.views.decorators.cache import cache_page
import csv
import json
from sms.models import Courses
from django.forms import formset_factory
from import_export import resources
from tablib import Dataset
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO
from quiz.admin import QuestionResource
import codecs
import io
import logging
from django.contrib import messages
from docx import Document
import latex2mathml.converter

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from teacher import forms as QFORM
from quiz import models as QMODEL

# from django.shortcuts import render,redirect, get_object_or_404
# from . import forms,models
# from django.db.models import Sum
# from django.contrib.auth.models import Group
# from django.http import HttpResponseRedirect
# from django.contrib.auth.decorators import login_required,user_passes_test
# from django.conf import settings
# from datetime import date, timedelta
# from teacher import forms as QFORM
# from users.models import NewUser
# from django.contrib.auth.models import AnonymousUser
# from quiz.models import Course
# from django.utils.datastructures import MultiValueDictKeyError
# from .models import SampleCodes
# from .forms import JSONForm

# # views.py
# from quiz import models as QMODEL
# from student import models as SMODEL
# from django.shortcuts import render, redirect
# from django.contrib.auth import authenticate, login
# from .forms import TeacherSignupForm
# from .models import Teacher
# from .forms import TeacherLoginForm
# from .forms import TeacherSignupForm  # Import your form
# from django.views.decorators.cache import cache_page
# import csv
# import json
# from quiz.models import Result
# from sms.models import Courses
# from django.forms import formset_factory
# from django.http import HttpResponse
# from django.shortcuts import render, redirect
# from .forms import QuestionForm, UploadCSVForm
# from quiz.models import Question
# from import_export import resources
# from tablib import Dataset
# from django.forms import formset_factory
# from .forms import QuestionForm
# from .forms import QuestionForm
# from django.http import HttpResponse
# from quiz.models import Course
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
# from io import BytesIO
# from django.shortcuts import render
# from django.http import HttpResponse
# from quiz.admin import QuestionResource
# import codecs

# import io
# import logging
# from django.http import HttpResponse, HttpResponseRedirect
# from django.shortcuts import render
# from django.contrib import messages
# from tablib import Dataset
# from docx import Document
# import latex2mathml.converter
# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)




# def teacher_signup_view(request):
#     user = request.user

#     # Get the teacher instance associated with the user
#     try:
#         teacher = Teacher.objects.get(user=user)
#     except Teacher.DoesNotExist:
#         # Redirect to some error page or handle the case where the user is not a teacher
#         return redirect('teacher_login')

#     # Get the subjects taught by the teacher
#     subjects_taught = teacher.subjects_taught.all()
#     subjects_taught_titles = [course.course_name.title for course in subjects_taught]
#     print("subjects_taughty", subjects_taught_titles)


#     if request.method == 'POST':
#         form = TeacherSignupForm(request.POST, subjects_taught=subjects_taught_titles)

#         if form.is_valid():
#             user = form.save()
#             form.save_teacher(user)
#             return redirect('teacher_login')  # Redirect to teacher login page
#     else:
#         form = TeacherSignupForm(subjects_taught=subjects_taught_titles)

#     return render(request, 'teacher/dashboard/teacher_signup.html', {'form': form})

# def login_section_view(request):

#     context = {
#         'text':"testing"
#     }
  

#     return render(request, 'teacher/dashboard/login_section.html',context = context)

@cache_page(60 * 15)
def teacher_signup_view(request):
    if request.method == 'POST':
        form = TeacherSignupForm(request.POST)

        # form = TeacherSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            form.save_teacher(user)
            return redirect('teacher:teacher_login')  # Redirect to teacher login page
    else:
        form = TeacherSignupForm(request.POST)

    return render(request, 'teacher/dashboard/teacher_signup.html', {'form': form})


# def teacher_login_view(request):
#     if request.method == 'POST':
#         form = TeacherLoginForm(request, request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             # Retrieve all teachers
#             teachers = Teacher.objects.all()
#             # Print all teachers' email addresses
#             print("Teachers' emails:",teachers)
#             # for teacher in teachers:
#             #     print(teacher.username)
#             # Check if any teacher's email matches the entered email
#             for teacher in teachers:
#                 print(teacher.username)
#                 # If the entered email matches a teacher's email, proceed with authentication
#                 if teacher.username.lower():
#                     user = authenticate(request, username=teacher.username, password=password)
#                     if user is not None:
#                         login(request, user)
#                         # Redirect to a success page or dashboard
#                         return redirect('teacher:teacher-dashboard')
#                 else:
#                     # If authentication fails, render the login form with an error message
#                     return render(request, 'teacher/teacher_login.html', {'form': form, 'error_message': 'Invalid username or password'})
#             else:
#                 # If no teacher with the entered email exists, render the login form with an error message
#                 return render(request, 'teacher/dashboard/teacher_login.html', {'form': form, 'error_message': 'Invalid username or password'})
#     else:
#         form = TeacherLoginForm()
#     return render(request, 'teacher/dashboard/teacher_login.html', {'form': form})

@cache_page(60 * 15)
def teacher_logout_view(request):

    return render(request, 'teacher/dashboard/teacher_logout.html')

@cache_page(60 * 15)
def student_logout_view(request):

    return render(request, 'teacher/dashboard/student_logout.html')

@cache_page(60 * 15)
def teacher_login_view(request):
    teachers = Teacher.objects.all()
    print('teachers:',teachers)
    if request.method == 'POST':
       
        form = TeacherLoginForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # print('username:',username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                # Redirect to a success page or dashboard
                return redirect('teacher:teacher-dashboard')
            else:
                # Handle invalid login credentials
                # For example, you can render a message to the user indicating that the login credentials are incorrect
                return render(request, 'teacher_login.html', {'form': form, 'error_message': 'Invalid username or password'})
    else:
        form = TeacherLoginForm()
    return render(request, 'teacher/dashboard/teacher_login.html', {'form': form, 'teachers': teachers})

from teacher.models import School

# @login_required(login_url='teacher:teacher_login')
# def teacher_dashboard_view(request):
    
#     username = request.user.username
#     print("useridd:", username)
#     teacher = Teacher.objects.get(username=username)
#     print("teacher:",  teacher)
#     teacher_subjects = teacher.subjects_taught.all()

# # Now you can iterate over the subjects or perform further operations as needed
#     for subject in teacher_subjects:
#         print('sub',subject)
    
#     dict={
#     'total_course':'testing',
#     }
#     return render(request,'teacher/dashboard/teacher_dashboard.html',context=dict)

@cache_page(60 * 15)
@login_required(login_url='teacher:teacher_login')
def teacher_dashboard_view(request):

    username = request.user.username
    print('user',username)
    try:
        teacher = Teacher.objects.get(username=username)
        teacher_subjects = teacher.subjects_taught.all()
        teacher_class = teacher.classes_taught.all()
        print('teacher',teacher)
        print('teacher_subjects',teacher_subjects)
        # Your further logic here
        dict = {
            'username': username,
            'teacher_class': teacher_class,
             'teacher_subjects': teacher_subjects,

            }
        return render(request, 'teacher/dashboard/teacher_dashboard.html', context=dict)
    except Teacher.DoesNotExist:
        # Handle case where Teacher instance does not exist
        return redirect('account_login')
        # return render(request, 'teacher/dashboard/teacher_login.html')

@cache_page(60 * 15)
@login_required(login_url='account_login')
def student_dashboard_view(request):

    user = request.user
    # print("useridd:", user)

    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    
    }
    return render(request,'teacher/dashboard/student_dashboard.html',context=dict)



@cache_page(60 * 15)
def add_question_view(request):
    # Retrieve the currently logged-in user
    user = request.user
    # Get the teacher instance associated with the user
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        # Redirect to some error page or handle the case where the user is not a teacher
        return redirect('teacher_login')

    # Get the subjects taught by the teacher
    subjects_taught = teacher.subjects_taught.all()

    subjects_taught_titles = [course.course_name.title for course in subjects_taught]
    print("subjects_taughty", subjects_taught_titles)
    courses = Courses.objects.filter(title__in=subjects_taught_titles)
    print("ccc", courses)
    # Filter courses based on the subjects taught by the teacher
    # courses = Courses.objects.filter(title__in=subjects_taught)
    # print("ccc", courses)
    # Create a formset with QuestionForm
    QuestionFormSet = formset_factory(QuestionForm, extra=1)

    if request.method == 'POST':
        formset = QuestionFormSet(request.POST, request.FILES)
        if formset.is_valid():
            for form in formset:
                form.save()
            return redirect('teacher:teacher-dashboard')  # Redirect to teacher dashboard after successfully adding questions
    else:
        # Pass the courses queryset to each form in the formset
        formset = QuestionFormSet(form_kwargs={'courses': courses})

    context = {
        'formset': formset,
        'subjects_taught': subjects_taught,
    }
    return render(request, 'teacher/dashboard/teacher_add_question.html', context)




@cache_page(60 * 15)
def teacher_results_view(request):
    # Retrieve the currently logged-in user
    user = request.user

    # Get the teacher instance associated with the user
    try:
        teacher = Teacher.objects.get(user=user)
    except Teacher.DoesNotExist:
        # Handle the case where the user is not a teacher
        # Redirect to an error page or return an appropriate response
        return render(request, 'error_page.html', {'message': 'You are not a teacher'})

    # Get the subjects taught by the teacher
    subjects_taught = teacher.subjects_taught.all()
    
    subjects_taught_titles = [course.course_name for course in subjects_taught]
    print("subjects_taught66", subjects_taught_titles)
    # Retrieve the results associated with the subjects taught by the teacher
    results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
    print('results', results)

    context = {
        'teacher': teacher,
        'results': results,
    }
    return render(request, 'teacher/dashboard/teacher_results.html', context)



@cache_page(60 * 15)
def export_results_csv(request):
    if request.method == 'POST':
        file_type = request.POST.get('file-type')
        selected_course_id = request.POST.get('course')

        # Retrieve the selected course object
        selected_course = Course.objects.get(id=selected_course_id)

        results = Result.objects.filter(exam=selected_course)

        if file_type == 'csv':
            # Export to CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'

            writer = csv.writer(response)
            writer.writerow(['Student Name', 'Exam Score', 'Exam Subject'])

            for result in results:
                writer.writerow([result.student, result.marks, result.exam.course_name])

            return response

        elif file_type == 'pdf':
            # Export to PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="exam_results.pdf"'

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Create table data
            data = [['Student Name', 'Exam Score', 'Exam Subject']]
            for result in results:
                data.append([result.student, result.marks, result.exam.course_name])

            # Create table and add style
            table = Table(data)
            style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)])
            table.setStyle(style)

            elements.append(table)

            # Build PDF
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response

    else:
        user = request.user
        # Get the teacher instance associated with the user
        teacher = Teacher.objects.get(user=user)
        # Get the subjects taught by the teacher
        subjects_taught = teacher.subjects_taught.all()

        return render(request, 'teacher/dashboard/export_results.html', {'subjects_taught': subjects_taught})

    return redirect('export_results_csv')

# from django.http import HttpResponse
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
# from io import BytesIO

# def export_results_csv(request):
#     if request.method == 'POST':
#         file_type = request.POST.get('file-type')
        
#         user = request.user
#         teacher = Teacher.objects.get(user=user)
#         subjects_taught = teacher.subjects_taught.all()
#         subjects_taught_titles = [course.course_name for course in subjects_taught]
#         results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
        
#         if file_type == 'csv':
#             # Export to CSV
#             response = HttpResponse(content_type='text/csv')
#             response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'

#             writer = csv.writer(response)
#             writer.writerow(['Student Name', 'Exam Score', 'Exam Subject'])

#             for result in results:
#                 writer.writerow([result.student, result.marks, result.exam.course_name])

#             return response

#         elif file_type == 'pdf':
#             # Export to PDF
#             response = HttpResponse(content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="exam_results.pdf"'
            
#             buffer = BytesIO()
#             doc = SimpleDocTemplate(buffer, pagesize=letter)
#             elements = []

#             # Create table data
#             data = [['Student Name', 'Exam Score', 'Exam Subject']]
#             for result in results:
#                 data.append([result.student, result.marks, result.exam.course_name])

#             # Create table and add style
#             table = Table(data)
#             style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                                 ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                                 ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                                 ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                                 ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                                 ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                                 ('GRID', (0, 0), (-1, -1), 1, colors.black)])
#             table.setStyle(style)
            
#             elements.append(table)

#             # Build PDF
#             doc.build(elements)
#             pdf = buffer.getvalue()
#             buffer.close()
#             response.write(pdf)
#             return response
        
#     return render(request, 'teacher/dashboard/export_results.html')


# def export_results_csv(request):
#     user = request.user
#     teacher = Teacher.objects.get(user=user)
#     # Retrieve results from the database or any other source
#     subjects_taught = teacher.subjects_taught.all()
    
#     subjects_taught_titles = [course.course_name for course in subjects_taught]
#     print("subjects_taught66", subjects_taught_titles)
#     # Retrieve the results associated with the subjects taught by the teacher
#     results = Result.objects.filter(exam__course_name__in=subjects_taught_titles)
#     print('results', results)
#     # results = Result.objects.all()

#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="exam_results.csv"'

#     writer = csv.writer(response)
#     writer.writerow(['Student Name', 'Exam Score', 'Exam Subject'])

#     for result in results:
#         writer.writerow([result.student, result.marks, result.exam.course_name])

#     return response

# def add_question_view(request):
#     # Retrieve the currently logged-in user
#     user = request.user

#     # Get the teacher instance associated with the user
#     try:
#         teacher = Teacher.objects.get(user=user)
#     except Teacher.DoesNotExist:
#         # Redirect to some error page or handle the case where the user is not a teacher
#         return redirect('teacher_login')

#     # Get the subjects taught by the teacher
#     subjects_taught = teacher.subjects_taught.all()

#     # Filter courses based on the subjects taught by the teacher
#     courses = Courses.objects.filter(title__in=subjects_taught)

#     QuestionFormSet = formset_factory(QuestionForm, extra=1)  # Create a formset with 5 extra forms

#     if request.method == 'POST':
#         formset = QuestionFormSet(request.POST, request.FILES)
#         if formset.is_valid():
#             for form in formset:
#                 form.save()
#             return redirect('teacher-dashboard')  # Redirect to teacher dashboard after successfully adding questions
#     else:
#         formset = QuestionFormSet()

#     context = {
#         'formset': formset,
#         'subjects_taught': subjects_taught,
#     }
#     return render(request, 'teacher/dashboard/teacher_add_question.html', context)



def tex_to_mathml(tex_input):
    try:
        # Log the input being converted
        logger.debug(f"Converting TeX input: {tex_input}")
        # Attempt to convert only if input likely contains TeX
        if '$' in tex_input or '\\' in tex_input:
            mathml_output = latex2mathml.converter.convert(tex_input)
            logger.debug(f"Converted MathML output: {mathml_output}")
            return mathml_output
        return tex_input
    except Exception as e:
        logger.error(f"Error converting TeX to MathML: {e}, Input: {tex_input}")
        return tex_input  # If conversion fails, return the original TeX input



# original codes
@cache_page(60 * 15)
def import_data(request):
    if request.method == 'POST':
        dataset = Dataset()
        new_file = request.FILES['myfile']

        # Check if the uploaded file format is supported
        allowed_formats = ['xlsx', 'xls', 'csv', 'docx']
        file_extension = new_file.name.split('.')[-1]
        if file_extension not in allowed_formats:
            return HttpResponse('File format not supported. Supported formats: XLSX, XLS, CSV, DOCX')

        imported_data = None

        try:
            if file_extension == 'csv':
                # Handle CSV
                data = io.TextIOWrapper(new_file, encoding='utf-8')
                imported_data = dataset.load(data, format=file_extension)
                # Convert TeX to MathML for CSV data
                for row in imported_data.dict:
                    for key in ['question','img_quiz' ,'option1', 'option2', 'option3', 'option4', 'answer']:
                        if key in row:
                            original_value = row[key]
                            row[key] = tex_to_mathml(row[key])
                            logger.debug(f"Converted {key} from {original_value} to {row[key]}")
                messages.success(request, "Data imported successfully.")
            elif file_extension in ['xlsx', 'xls']:
                # Handle Excel files
                imported_data = dataset.load(new_file.read(), format=file_extension)
                # Convert TeX to MathML for Excel data
                for row in imported_data.dict:
                    for key in ['question','img_quiz' ,'option1', 'option2', 'option3', 'option4', 'answer']:
                        if key in row:
                            original_value = row[key]
                            row[key] = tex_to_mathml(row[key])
                            logger.debug(f"Converted {key} from {original_value} to {row[key]}")
                messages.success(request, "Data imported successfully.")
            elif file_extension == 'docx':
                # Handle Word documents
                document = Document(new_file)
                rows = []
                for table in document.tables:
                    for row in table.rows:
                        row_data = [tex_to_mathml(cell.text) for cell in row.cells]  # Convert TeX to MathML
                        rows.append(row_data)
                # Convert to CSV-like format
                csv_data = io.StringIO()
                writer = csv.writer(csv_data)
                writer.writerows(rows)
                csv_data.seek(0)
                imported_data = dataset.load(csv_data, format='csv')
                # messages.success(request, "Data imported successfully.")
            else:
                messages.error(request, f"An error occurred while importing {file_extension} file.")
                return render(request, 'teacher/dashboard/import.html')

            # Import data using the resource
            resource = QuestionResource()
            result = resource.import_data(imported_data, dry_run=True)  # Dry run first

            if result.has_errors():
                messages.error(request, "Errors occurred during import: {}".format(result.errors))
                logger.error("Errors occurred during import: {}".format(result.errors))
            else:
                # Perform the actual import
                result = resource.import_data(imported_data, dry_run=False)
                if result.has_errors():
                    messages.error(request, "Errors occurred during saving: {}".format(result.errors))
                    logger.error("Errors occurred during saving: {}".format(result.errors))
                else:
                    messages.success(request, "Data saved successfully.")
                    logger.info("Data saved successfully.")

            # Redirect back to the import page after processing
            return HttpResponseRedirect(request.path_info)

        except Exception as e:
            messages.error(request, f"You have no permission to import this subject. Check dashboard for your assigned subjects")
            # print('resu', result)
            # messages.error(request, f"An error occurred: {e}")
            logger.error(f"An error occurred while processing the file: {e}")
            return render(request, 'teacher/dashboard/import.html')

    return render(request, 'teacher/dashboard/import.html')


# views.py
# def import_data(request):
#     if request.method == 'POST':
#         dataset = Dataset()
#         new_questions = request.FILES['myfile']

#         # Check if the uploaded file format is supported
#         allowed_formats = ['xlsx', 'xls', 'csv']
#         file_extension = new_questions.name.split('.')[-1]
#         if file_extension not in allowed_formats:
#             return HttpResponse('File format not supported. Supported formats: XLSX, XLS, CSV')

#         # Load and import data based on the file format
#         if file_extension == 'csv':
#             # Open the file in text mode and decode bytes into a string
#             data = codecs.iterdecode(new_questions, 'utf-8')
#             imported_data = dataset.load(data, format=file_extension)
#             messages.success(request, "Questions imported successfully.")
#         else:
#             messages.error(request, f"An error occurred")
#             imported_data = dataset.load(new_questions.read(), format=file_extension)

#         resource = QuestionResource()
#         result = resource.import_data(imported_data, dry_run=True)  # Dry run first
#         if not result.has_errors():
#             resource.import_data(imported_data, dry_run=False)

#     return render(request, 'teacher/dashboard/import.html')



from docx import Document
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
import csv

@cache_page(60 * 15)
def import_word(request):
    if request.method == 'POST':
        # Check if the uploaded file format is supported
        allowed_formats = ['docx']
        uploaded_file = request.FILES.get('myfile')
        if not uploaded_file:
            return HttpResponse('No file uploaded.')

        file_extension = uploaded_file.name.split('.')[-1]
        if file_extension not in allowed_formats:
            return HttpResponse('File format not supported. Supported format: DOCX')

        # Handle Word document file
        document = Document(uploaded_file)
        questions = []

        for table_idx, table in enumerate(document.tables):
            for row_idx, row in enumerate(table.rows):
                question = [cell.text.strip() for cell in row.cells]
                if len(question) == 9:  # Assuming answer is included
                    questions.append(question)
                else:
                    messages.warning(request, f"Ignored invalid line in table {table_idx + 1}, row {row_idx + 1}: {', '.join(question)}")

        if questions:
            # Create CSV content
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="imported_questions.csv"'

            writer = csv.writer(response)
            # writer.writerow(['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer'])

            for question in questions:
                writer.writerow(question)

            messages.success(request, "Data imported successfully.")
            
            return response
        else:
            messages.warning(request, "No valid data found in the document.")

    return render(request, 'teacher/dashboard/importdocs.html')


# def import_data(request):
#     if request.method == 'POST':
#         dataset = Dataset()
#         new_questions = request.FILES['myfile']

#         # Check if the uploaded file format is supported
#         allowed_formats = ['xlsx', 'xls', 'csv']
#         file_extension = new_questions.name.split('.')[-1]
#         if file_extension not in allowed_formats:
#             return HttpResponse('File format not supported. Supported formats: XLSX, XLS, CSV')

#         # Load and import data based on the file format
#         if file_extension == 'csv':
#             # Open the file in text mode and decode bytes into a string
#             data = codecs.iterdecode(new_questions, 'utf-8')
#             imported_data = dataset.load(data, format=file_extension)
#             messages.success(request, "Questions imported successfully.")
#         else:
#             messages.error(request, f"An error occurred")
#             imported_data = dataset.load(new_questions.read(), format=file_extension)

#         resource = QuestionResource()
#         result = resource.import_data(imported_data, dry_run=True)  # Dry run first
#         if not result.has_errors():
#             resource.import_data(imported_data, dry_run=False)

#     return render(request, 'teacher/dashboard/import.html')


# utils.py



def write_to_csv(data, filename):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['course', 'marks', 'question', 'img_quiz', 'option1', 'option2', 'option3', 'option4', 'answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for response in data:
            row = {
                'course': response.get('course', ''),
                'marks': response.get('marks', ''),
                'question': response.get('question', ''),
                'img_quiz': response.get('img_quiz', ''),
                'option1': response.get('option1', '').strip('"'),
                'option2': response.get('option2', '').strip('"'),
                'option3': response.get('option3', '').strip('"'),
                'option4': response.get('option4', '').strip('"'),
                'answer': response.get('answer', '')
            }
            
            correct_option = row['answer'].upper()
            if correct_option == "A":
                row['answer'] = "Option1"
            elif correct_option == "B":
                row['answer'] = "Option2"
            elif correct_option == "C":
                row['answer'] = "Option3"
            elif correct_option == "D":
                row['answer'] = "Option4"
            
            writer.writerow(row)

# Example usage:
json_data = '''
[
    {
        "course": "MATH JSS2",
        "marks": "1",
        "question": "Which of the following factors should developers consider when selecting an IDE?",
        "img_quiz": "",
        "option1": "Coffee quality in the office",
        "option2": "Number of likes on IDE's Facebook page",
        "option3": "Language support, feature set, customization options, and performance",
        "option4": "The color of the IDE's logo",
        "answer": "C"
    },
    {
        "course": "MATH JSS2",
        "marks": "1",
        "question": "What is one of the benefits of using IDEs?",
        "img_quiz": "",
        "option1": "Access to free snacks in the break room",
        "option2": "Increased productivity due to streamlined development workflows",
        "option3": "Chance to win a vacation package",
        "option4": "Ability to pet the office dog",
        "answer": "B"
    }
]
'''

# Parse JSON string into a list of dictionaries
questions_data = json.loads(json_data)
# Write generated data to CSV file
write_to_csv(questions_data, 'generated_questions8.csv')


def generate_csv(request):

    sample_codes = SampleCodes.objects.all()
    # print('sample',sample_codes)
    if request.method == 'POST':
        form = JSONForm(request.POST)
        if form.is_valid():
            # Parse JSON data
            json_data = form.cleaned_data['json_data']
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError:
                return render(request, 'teacher/dashboard/error.html', {'message': 'Invalid JSON data'})

            # Generate CSV
            try:
                write_to_csv(data, 'generated_questions.csv')
            except Exception as e:
                return render(request, 'teacher/dashboard/error.html', {'message': str(e)})

            return render(request, 'teacher/dashboard/success.html')
    else:
        form = JSONForm()
        
    return render(request, 'teacher/dashboard/generate_csv.html', {'form': form, 'sample_codes':sample_codes})


@cache_page(60 * 15)
def download_csv(request):
    # Assuming the CSV file is generated and saved as 'generated_questions.csv'
    filename = 'generated_questions.csv'

    # Open the CSV file and read its contents
    with open(filename, 'rb') as csv_file:
        response = HttpResponse(csv_file.read(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        return response
    

def export_data(request):
    if request.method == 'POST':
        try:
            selected_courses_ids = request.POST.getlist('courses')
        except MultiValueDictKeyError:
            # Handle the case when 'courses' key is not found in the POST data
            selected_courses_ids = []

        resource = QuestionResource()
        # Query questions using the selected course IDs
        queryset = Question.objects.filter(course__id__in=selected_courses_ids)
        
        dataset = resource.export(request=request, queryset=queryset)
        response = HttpResponse(dataset.csv, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="questions.csv"'
        return response
    else:
        user = request.user
        # Get the teacher instance associated with the user
        teacher = Teacher.objects.get(user=user)
        # Get the subjects taught by the teacher
        subjects_taught = teacher.subjects_taught.all()
        # Extract course IDs from the list of course objects
        selected_courses_ids = [course.id for course in subjects_taught]
        # Query courses using the extracted IDs
        courses = Course.objects.filter(id__in=selected_courses_ids)
        return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})

# def export_data(request):
#     if request.method == 'POST':
#         selected_courses = request.POST.getlist('courses')
#         resource = QuestionResource()
#         dataset = resource.export(request=request, queryset=Question.objects.filter(course__in=selected_courses))
#         response = HttpResponse(dataset.csv, content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="questions.csv"'
#         return response
#     else:
#         user = request.user
#         # Get the teacher instance associated with the user
#         teacher = Teacher.objects.get(user=user)
#         # Get the subjects taught by the teacher
#         subjects_taught = teacher.subjects_taught.all()
#         subjects_taught_titles = [course.course_name for course in subjects_taught]
#         print("subjects_taught66", subjects_taught_titles)
#         courses = Course.objects.filter(course_name = subjects_taught_titles)
#         print('cor',courses)
#         return render(request, 'teacher/dashboard/export_questions.html', {'courses': courses})



@cache_page(60 * 15)
def view_questions(request):
    # Check if user is authenticated
    if not request.user.is_authenticated:
        # Redirect to login page or handle authentication
        return redirect('teacher:teacher_login')
    
    # Check if user is a teacher
    if not isinstance(request.user, AnonymousUser):
        # Get the teacher instance associated with the user
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            # Handle the case where the user is not a teacher
            return redirect('teacher:teacher_login')  # or any other appropriate action
    
    # Filter questions based on the subjects taught by the teacher
    questions = Question.objects.filter(course__in=teacher.subjects_taught.all())
    print('q',questions)
    context = {
        'questions': questions
    }

    # Render the template with the questions
    return render(request, 'teacher/dashboard/view_questions.html', context)


@cache_page(60 * 15)
def edit_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES,instance=question)
        if form.is_valid():
            form.save()
            return redirect('teacher:view_questions')  # Redirect to the view questions page
    else:
        form = QuestionForm(instance=question)
    return render(request, 'teacher/dashboard/edit_questions.html', {'form': form})



@cache_page(60 * 15)
def delete_question_view(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        # Handle form submission for deleting the question
        question.delete()
        return redirect('teacher:view_questions')  # Redirect to the teacher dashboard after deleting
    else:
        # Render a confirmation page before deleting the question
        return render(request, 'teacher/dashboard/delete_question.html', {'question': question})
    
# def export_data(request):
#     question_resource = QuestionResource()
#     dataset = question_resource.export()
#     response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
#     response['Content-Disposition'] = 'attachment; filename="questions.xls"'
#     return response

# def teacher_signup_view(request):
#     if request.method == 'POST':
#         form = TeacherSignupForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('dashboard')  # Redirect to the dashboard after signup
#     else:
#         form = TeacherSignupForm()
#     return render(request, 'teacher/teacher_signup.html', {'form': form})

# def teacher_login_view(request):
#     if request.method == 'POST':
#         form = TeacherLoginForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             user = authenticate(request, email=email, password=password)
#             if user is not None:
#                 login(request, user)
#                 # Redirect to a success page or dashboard
#                 return redirect('dashboard')
#     else:
#         form = TeacherLoginForm()
#     return render(request, 'teacher_login.html', {'form': form})


#for showing signup/login button for teacher
# def teacherclick_view(request):
#     if request.user.is_authenticated:
#         return HttpResponseRedirect('afterlogin')
#     return render(request,'teacher/teacherclick.html')

# def teacher_signup_view(request):
#     if request.method == 'POST':
#         userForm = forms.TeacherUserForm(request.POST)
#         teacherForm = forms.TeacherForm(request.POST)
#         if userForm.is_valid() and teacherForm.is_valid():
#             # Save user data
#             user = userForm.save(commit=False)
#             user.set_password(user.password)
#             user.save()
#             # Save teacher data
#             teacher = teacherForm.save(commit=False)
#             teacher.user = user
#             teacher.save()
#             # Add user to the 'TEACHER' group
#             my_teacher_group, created = Group.objects.get_or_create(name='TEACHER')
#             my_teacher_group.user_set.add(user)
#             return HttpResponseRedirect('teacherlogin')
#     else:
#         userForm = forms.TeacherUserForm()
#         teacherForm = forms.TeacherForm()
#     mydict = {'userForm': userForm, 'teacherForm': teacherForm}
#     return render(request, 'teacher/teachersignup.html', context=mydict)


# def is_teacher(user):
#     return user.groups.filter(name='TEACHER').exists()

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_dashboard_view(request):
#     dict={
    
#     'total_course':QMODEL.Course.objects.all().count(),
#     'total_question':QMODEL.Question.objects.all().count(),
#     'total_student':SMODEL.Student.objects.all().count()
#     }
#     return render(request,'teacher/teacher_dashboard.html',context=dict)

# from .forms import TeacherRegistrationForm

# def register_teacher(request):
#     if request.method == 'POST':
#         form = TeacherRegistrationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('login')  # Redirect to login page after registration
#     else:
#         form = TeacherRegistrationForm()
#     return render(request, 'teacher/register_teacher.html', {'form': form})


# # views.py

# @login_required
# def teacher_dashboard(request):
#     return render(request, 'teacher/teacher_dashboard.html')

# #for showing signup/login button for teacher
# def teacherclick_view(request):
#     if request.user.is_authenticated:
#         return HttpResponseRedirect('afterlogin')
#     return render(request,'teacher/teacherclick.html')

# def teacher_signup_view(request):
#     userForm=forms.TeacherUserForm()
#     teacherForm=forms.TeacherForm()
#     mydict={'teacherForm':teacherForm}
#     if request.method=='POST':
#         # userForm=forms.TeacherUserForm(request.POST)
#         teacherForm=forms.TeacherForm(request.POST,request.FILES)
#         if teacherForm.is_valid():
#             teacherForm.save()
        
#         return HttpResponseRedirect('teacherlogin')
#     return render(request,'teacher/teachersignup.html',context=mydict)



# def is_teacher(user):
#     return user.groups.filter(name='TEACHER').exists()

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_dashboard_view(request):
#     dict={
    
#     'total_course':QMODEL.Course.objects.all().count(),
#     'total_question':QMODEL.Question.objects.all().count(),
#     'total_student':SMODEL.Student.objects.all().count()
#     }
#     return render(request,'teacher/teacher_dashboard.html',context=dict)

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_exam_view(request):
#     return render(request,'teacher/teacher_exam.html')


# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_add_exam_view(request):
#     courseForm=QFORM.CourseForm()
#     if request.method=='POST':
#         courseForm=QFORM.CourseForm(request.POST)
#         if courseForm.is_valid():        
#             courseForm.save()
#         else:
#             print("form is invalid")
#         return HttpResponseRedirect('/teacher/teacher-view-exam')
#     return render(request,'teacher/teacher_add_exam.html',{'courseForm':courseForm})

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_view_exam_view(request):
#     courses = QMODEL.Course.objects.all()
#     return render(request,'teacher/teacher_view_exam.html',{'courses':courses})

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def delete_exam_view(request,pk):
#     course=QMODEL.Course.objects.get(id=pk)
#     course.delete()
#     return HttpResponseRedirect('/teacher/teacher-view-exam')

# @login_required(login_url='adminlogin')
# def teacher_question_view(request):
#     return render(request,'teacher/teacher_question.html')

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_add_question_view(request):
#     questionForm=QFORM.QuestionForm()
#     if request.method=='POST':
#         questionForm=QFORM.QuestionForm(request.POST)
#         if questionForm.is_valid():
#             question=questionForm.save(commit=False)
#             course=QMODEL.Course.objects.get(id=request.POST.get('courseID'))
#             question.course=course
#             question.save()       
#         else:
#             print("form is invalid")
#         return HttpResponseRedirect('/teacher/teacher-view-question')
#     return render(request,'teacher/teacher_add_question.html',{'questionForm':questionForm})

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def teacher_view_question_view(request):
#     courses= QMODEL.Course.objects.all()
#     return render(request,'teacher/teacher_view_question.html',{'courses':courses})

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def see_question_view(request,pk):
#     questions=QMODEL.Question.objects.all().filter(course_id=pk)
#     return render(request,'teacher/see_question.html',{'questions':questions})

# @login_required(login_url='teacherlogin')
# @user_passes_test(is_teacher)
# def remove_question_view(request,pk):
#     question=QMODEL.Question.objects.get(id=pk)
#     question.delete()
#     return HttpResponseRedirect('/teacher/teacher-view-question')
