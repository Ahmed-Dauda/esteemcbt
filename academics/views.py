from django.shortcuts import render, redirect
from .models import StudentConduct
from .forms import StudentConductForm
from django.db.models import Count
from django.contrib.auth.decorators import login_required

def add_conduct(request):
    if request.method == 'POST':
        form = StudentConductForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('list_conducts')
    else:      
        form = StudentConductForm(user=request.user)
    
    return render(request, 'academics/add_conduct.html', {'form': form})
     

@login_required
def list_conducts(request):
    """List all student conduct records with counts, restricted to the logged-in teacher unless superuser."""
    if request.user.is_superuser:
        conducts = StudentConduct.objects.all()
    else:
        conducts = StudentConduct.objects.filter(teacher=request.user)
    
    conducts = conducts.select_related('student', 'student_class', 'session', 'term', 'category') \
        .annotate(conduct_count=Count('id'))
    
    return render(request, 'academics/list_conducts.html', {'conducts': conducts})

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
            return redirect('list_conducts')
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
        return HttpResponseRedirect(reverse('list_conducts'))
    
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

