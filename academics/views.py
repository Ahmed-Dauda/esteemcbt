from django.shortcuts import render, redirect
from .models import StudentConduct
from .forms import StudentConductForm
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def add_conduct(request):
    if request.method == 'POST':
        form = StudentConductForm(request.POST, user=request.user)  # Pass `user` explicitly
        if form.is_valid():
            form.save()  # Save the form
            # Add a success message
            messages.success(request, 'Conduct record added successfully!')
            return redirect('academics:add_conduct')  # Redirect to the same page or another page
    else:
        form = StudentConductForm(user=request.user)  # Pass `user` explicitly for GET request
    
    return render(request, 'academics/add_conduct.html', {'form': form})

# def add_conduct(request):
#     if request.method == 'POST':
#         form = StudentConductForm(request.POST, user=request.user)  # Pass `user` explicitly
#         if form.is_valid():
#             form.save()
#             return redirect('academics:add_conduct')
#     else:
#         form = StudentConductForm(user=request.user)  # Pass `user` explicitly
    
#     return render(request, 'academics/add_conduct.html', {'form': form})


from dal import autocomplete
from .models import NewUser

class StudentAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return NewUser.objects.none()
        
        qs = NewUser.objects.filter(school=user.school)
        
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        
        return qs



from django.shortcuts import render
from .models import StudentConduct

from django.shortcuts import render
from .models import StudentConduct



from django.db.models import Count
from django.contrib.auth.decorators import login_required

@login_required
def list_conducts(request):
    # Get the teacher's school
    user_school = request.user.school

    # Get the school name where the teacher is assigned
    teacher_school = StudentConduct.objects.filter(school_id=user_school.id).values_list('school__school_name', flat=True).first()
    
    # print(request.user.email, 'sc')

    """List all student conduct records with counts, restricted to the logged-in teacher unless superuser."""
    if request.user.is_superuser:
        # If superuser, show all conducts for all teachers and students
        conducts = StudentConduct.objects.all()
    else:
        # Only show the conduct records for the logged-in teacher's students
        conducts = StudentConduct.objects.filter(teacher=request.user)

    # Use select_related to optimize queries for related objects, then annotate conduct count
    conducts = conducts.select_related('student', 'student_class', 'session', 'term', 'category') \
        .annotate(conduct_count=Count('id'))

    conducts = {
        'conducts': conducts,
        'user_school': user_school,
        'teacher_school': teacher_school
    }

    return render(request, 'academics/list_conducts.html', context=conducts)



@login_required
def edit_conduct(request, pk):
    """Edit a specific student conduct record."""
    if request.user.is_superuser:
        conduct = get_object_or_404(StudentConduct, pk=pk)
    else:
        conduct = get_object_or_404(StudentConduct, pk=pk, teacher=request.user)
    
    if request.method == 'POST':
        form = StudentConductForm(request.POST, instance=conduct)
        if form.is_valid():
            form.save()
            return redirect('academics:list_conducts')
    else:
        form = StudentConductForm(instance=conduct)
    
    return render(request, 'academics/edit_conduct.html', {'form': form})

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def delete_conduct(request, pk):
    """Delete a specific student conduct record."""
    if request.user.is_superuser:
        conduct = get_object_or_404(StudentConduct, pk=pk)
    else:
        conduct = get_object_or_404(StudentConduct, pk=pk, teacher=request.user)
    
    if request.method == 'POST':
        conduct.delete()
        return HttpResponseRedirect(reverse('academics:list_conducts'))
    
    return render(request, 'academics/delete_conduct.html', {'conduct': conduct})


from django.http import JsonResponse
from users.models import NewUser

def student_search(request):
    if 'q' in request.GET:      
        query = request.GET['q']
        students = NewUser.objects.filter(name__icontains=query)  # Filter students by name
        results = [{'id': student.id, 'text': student.name} for student in students]
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})

# views.py

# views.py

from dal import autocomplete
from .models import NewUser

class StudentAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        queryset = NewUser.objects.all()
        if self.q:
            queryset = queryset.filter(first_name__icontains=self.q)  # Example: filter by first name
        return queryset

