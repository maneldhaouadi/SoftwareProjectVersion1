from django.shortcuts import render, redirect
from .forms import PatientForm
from .models import Patient

def ajouter_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('liste_patients')  # redirige vers la liste
    else:
        form = PatientForm()
    return render(request, 'Patient/ajouter_patient.html', {'form': form})

def liste_patients(request):
    patients = Patient.objects.all()  # récupère tous les patients
    return render(request, 'Patient/liste_patients.html', {'patients': patients})
