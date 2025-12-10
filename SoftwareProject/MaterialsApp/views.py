from django.shortcuts import render, get_object_or_404, redirect
from .models import MaterielMedical
from .forms import MaterielMedicalForm
from django.contrib import messages
from datetime import date
from django.utils import timezone




def liste_materiels(request):
    type_filter = request.GET.get('type', '')
    etat_filter = request.GET.get('etat', '')
    search_query = request.GET.get('search', '')

    # Commencez par exclure les matériels hors service
    materiels = MaterielMedical.objects.exclude(Etat='HORS_SERVICE')

    if search_query:
        materiels = materiels.filter(Nom__icontains=search_query)
    if type_filter:
        materiels = materiels.filter(Type__icontains=type_filter)
    if etat_filter:
        materiels = materiels.filter(Etat__iexact=etat_filter)

    today = timezone.now().date()
    
    # Récupérer uniquement les types qui ont des matériels disponibles (non hors service)
    types = MaterielMedical.objects.exclude(Etat='HORS_SERVICE').values_list('Type', flat=True).distinct()
    
    # Récupérer séparément les matériels hors service pour l'affichage
    materiels_hors_service = MaterielMedical.objects.filter(Etat='HORS_SERVICE')

    context = {
        'materiels': materiels,
        'materiels_hors_service': materiels_hors_service,
        'today': today,
        'types': types,
        'selected_type': type_filter,
        'selected_etat': etat_filter,
        'search_query': search_query,
    }
    return render(request, 'materiel/elements.html', context)
def ajouter_materiel(request):
    if request.method == 'POST':
        form = MaterielMedicalForm(request.POST)
        if form.is_valid():
            materiel = form.save(commit=False)
            if not materiel.Reference.startswith('REF-'):
                materiel.Reference = f"REF-{materiel.Reference}"
            materiel.save()
            return redirect('liste_materiels')
    else:
        # Initialiser le champ Reference avec 'REF-'
        form = MaterielMedicalForm(initial={'Reference': 'REF-'})
    return render(request, 'materiel/form_materiel.html', {'form': form})


def modifier_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    ancienne_quantite = materiel.Quantite  # garder la quantité actuelle
    ancien_etat = materiel.Etat  # garder l'état actuel

    if request.method == 'POST':
        form = MaterielMedicalForm(request.POST, instance=materiel)
        if form.is_valid():
            materiel_modifie = form.save(commit=False)

            # Si on passe à "EN_PRET", on diminue la quantité
            if ancien_etat != 'EN_PRET' and materiel_modifie.Etat == 'EN_PRET':
                materiel_modifie.Quantite = max(materiel_modifie.Quantite - 1, 0)

            # Si on revient à "EN_SERVICE" depuis "EN_PRET", on restaure la quantité
            elif ancien_etat == 'EN_PRET' and materiel_modifie.Etat == 'EN_SERVICE':
                materiel_modifie.Quantite = ancienne_quantite

            materiel_modifie.save()
            return redirect('liste_materiels')
    else:
        form = MaterielMedicalForm(instance=materiel)
    
    return render(request, 'materiel/form_materiel.html', {
        'form': form,
        'is_edit': True
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


def mettre_en_maintenance(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_MAINTENANCE'
    materiel.save()
    messages.success(request, f"{materiel.Nom} est maintenant en maintenance.")
    return redirect('liste_materiels')

def remettre_en_service(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_SERVICE'
    materiel.save()
    messages.success(request, f"{materiel.Nom} est de nouveau en service.")
    return redirect('liste_materiels')

def reparer_materiel(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_MAINTENANCE'
    materiel.save()
    messages.success(request, f"{materiel.Nom} est envoyé en réparation.")
    return redirect('liste_materiels')

def retour_pret(request, pk):
    materiel = get_object_or_404(MaterielMedical, pk=pk)
    materiel.Etat = 'EN_SERVICE'
    materiel.save()
    messages.success(request, f"{materiel.Nom} est retourné et remis en service.")
    return redirect('liste_materiels')
