from django.shortcuts import render, redirect
from .forms import EmployeeForm
from django.contrib import messages
from .models import Employee

def ajouter_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            # Hasher le mot de passe si tu veux
            employe = form.save(commit=False)
            # from django.contrib.auth.hashers import make_password
            # employe.mot_de_passe = make_password(form.cleaned_data['mot_de_passe'])
            employe.save()
            messages.success(request, "Employé ajouté avec succès !")
            return redirect('liste_employes')
    else:
        form = EmployeeForm()
    return render(request, 'Employe/ajouter_employe.html', {'form': form})




def liste_employes(request):
    employes = Employee.objects.all()
    return render(request, 'Employe/liste_employes.html', {'employes': employes})
