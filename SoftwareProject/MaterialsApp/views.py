from django.shortcuts import render, get_object_or_404, redirect
from .models import MaterielMedical
from .forms import MaterielMedicalForm

def liste_materiels(request):
    materiels = MaterielMedical.objects.all()
    return render(request, 'materiel/elements.html', {'materiels': materiels})

def ajouter_materiel(request):
    if request.method == 'POST':
        form = MaterielMedicalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_materiels')
    else:
        form = MaterielMedicalForm()
    return render(request, 'materiel/form_materiel.html', {'form': form})

def modifier_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    if request.method == 'POST':
        form = MaterielMedicalForm(request.POST, instance=materiel)
        if form.is_valid():
            form.save()
            return redirect('liste_materiels')
    else:
        form = MaterielMedicalForm(instance=materiel)
    
    return render(request, 'materiel/form_materiel.html', {
        'form': form,
        'is_edit': True  # Indique qu'on est en modification
    })


def supprimer_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    if request.method == 'POST':
        materiel.delete()
        return redirect('liste_materiels')
    return render(request, 'materiel/confirmer_suppression.html', {'materiel': materiel})

# 🔹 Nouvelle méthode : afficher les détails d’un matériel
def materiel_detail(request, pk):
    materiel = get_object_or_404(MaterielMedical, IdMaterial=pk)
    return render(request, 'materiel/detail_materiel.html', {'materiel': materiel})
