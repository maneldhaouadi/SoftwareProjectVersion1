from django.db import models
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from EmployeApp.models import Employe
from .models import RendezVous
from .forms import RendezVousForm
from django.shortcuts import get_object_or_404,redirect
from django.core.exceptions import ValidationError
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from .models import RendezVous, Employe





#Liste des RDV prévu


class RendezVousListView(ListView):
    model = RendezVous
    template_name = 'RDV/liste_rdv.html'
    context_object_name = 'rdvs'
    paginate_by = 5

    def get_queryset(self):
        qs = super().get_queryset().filter(statut='prévu').order_by('date_rdv', 'heure_rdv')

        search = self.request.GET.get('search')

        if search:
            search = search.strip()
            terms = search.split()

            if len(terms) == 1:
                qs = qs.filter(
                    Q(medecin_id__nom__icontains=terms[0]) |
                    Q(medecin_id__prenom__icontains=terms[0]) |
                    Q(patient_id__nom__icontains=terms[0]) |
                    Q(patient_id__prenom__icontains=terms[0])
                )

            elif len(terms) >= 2:
                first = terms[0]
                second = terms[1]

                qs = qs.filter(
                    Q(medecin_id__nom__icontains=first, medecin_id__prenom__icontains=second) |
                    Q(medecin_id__nom__icontains=second, medecin_id__prenom__icontains=first) |
                    Q(patient_id__nom__icontains=first, patient_id__prenom__icontains=second) |
                    Q(patient_id__nom__icontains=second, patient_id__prenom__icontains=first)
                )

        return qs



#Liste des RDV historique
# views.py
class RendezVousHistoriqueListView(ListView):
    model = RendezVous
    template_name = 'RDV/historique_rdv.html'
    context_object_name = 'rdvs'
    paginate_by = 5

    def get_queryset(self):
        # D'abord, filtrer les RDV terminés ou annulés
        qs = super().get_queryset().filter(statut__in=['annulé', 'terminé']).order_by('-date_rdv', '-heure_rdv')
        
        # Ajouter le filtre par statut
        statut_filter = self.request.GET.get('statut')
        if statut_filter:
            qs = qs.filter(statut=statut_filter)
        
        # Recherche par nom/prenom
        search = self.request.GET.get('search')
        if search:
            search = search.strip()
            terms = search.split()

            if len(terms) == 1:
                qs = qs.filter(
                    Q(medecin_id__nom__icontains=terms[0]) |
                    Q(medecin_id__prenom__icontains=terms[0]) |
                    Q(patient_id__nom__icontains=terms[0]) |
                    Q(patient_id__prenom__icontains=terms[0])
                )
            elif len(terms) >= 2:
                first = terms[0]
                second = terms[1]
                qs = qs.filter(
                    Q(medecin_id__nom__icontains=first, medecin_id__prenom__icontains=second) |
                    Q(medecin_id__nom__icontains=second, medecin_id__prenom__icontains=first) |
                    Q(patient_id__nom__icontains=first, patient_id__prenom__icontains=second) |
                    Q(patient_id__nom__icontains=second, patient_id__prenom__icontains=first)
                )
        
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer le queryset de base (sans pagination)
        base_qs = RendezVous.objects.filter(statut__in=['annulé', 'terminé'])
        
        # Calculer les compteurs totaux
        context['total_count'] = base_qs.count()
        context['terminated_count'] = base_qs.filter(statut='terminé').count()
        context['cancelled_count'] = base_qs.filter(statut='annulé').count()
        
        # Ajouter la recherche courante
        context['search_query'] = self.request.GET.get('search', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        
        return context

def validate_rdv(form, instance=None):
    """
    Vérifie les conflits pour un rendez-vous.
    `instance` = l'objet existant à exclure lors de l'update
    Lève ValidationError si conflit détecté.
    """
    patient = form.cleaned_data['patient_id']
    medecin = form.cleaned_data['medecin_id']
    date_rdv = form.cleaned_data['date_rdv']
    heure_rdv = form.cleaned_data['heure_rdv']

    qs = RendezVous.objects.all().exclude(statut='annulé')
    if instance:
        qs = qs.exclude(pk=instance.pk)

    conflict_medecin = qs.filter(medecin_id=medecin, date_rdv=date_rdv, heure_rdv=heure_rdv).exists()
    conflict_patient = qs.filter(patient_id=patient, date_rdv=date_rdv, heure_rdv=heure_rdv).exists()
    conflict_rdv = qs.filter(patient_id=patient, medecin_id=medecin, date_rdv=date_rdv, heure_rdv=heure_rdv).exists()

    errors = []
    if conflict_medecin:
        errors.append("❌ Le médecin a déjà un rendez-vous à cette date et heure.")
    if conflict_patient:
        errors.append("⚠️ Le patient a déjà un rendez-vous à cette date et heure.")
    if conflict_rdv:
        errors.append("⚠️ Le patient a déjà un rendez-vous avec ce médecin à cette date et heure.")

    if errors:
        raise ValidationError(errors)

class RendezVousCreateView(CreateView):
    model = RendezVous
    form_class = RendezVousForm
    template_name = 'RDV/ajouter_rdv.html'
    success_url = reverse_lazy('liste_rdv')


    def form_valid(self, form):
        # Validation des conflits
        try:
            validate_rdv(form)
        except ValidationError as e:
            form.add_error(None, e)  # None = erreur non liée à un champ spécifique
            return self.form_invalid(form)

        # Définir le statut par défaut
        form.instance.statut = 'prévu'
        return super().form_valid(form)


class RendezVousUpdateView(UpdateView):#automatiquement faire un update
    model = RendezVous
    #equivalente a self.object = RendezVous.objects.get(id=12)

    form_class = RendezVousForm
    
    #Yasna3 formulaire
    template_name = 'RDV/update_rdv.html'
    success_url = reverse_lazy('liste_rdv')

    #  désactiver patient_id dans le formulaire
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)

        # rendre patient_id non modifiable
        if 'patient_id' in form.fields:
            form.fields['patient_id'].disabled = True  # read-only

        return form

    def form_valid(self, form):
        try:
            validate_rdv(form, instance=self.object)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)

        return super().form_valid(form)

def annuler_rdv(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    if rdv.statut not in ['annulé', 'terminé']:
        rdv.statut = 'annulé'
        rdv.save()
        messages.success(request, "✅ Le rendez-vous a été annulé avec succès.")
    else:
        messages.warning(request, "⚠️ Impossible d'annuler ce rendez-vous.")
    return redirect('liste_rdv')


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .models import RendezVous, Employe

def historique_medecin(request, medecin_id):
    # Récupérer le médecin
    medecin = get_object_or_404(Employe, id=medecin_id, role='medecin')
    
    # Récupérer tous les rendez-vous du médecin (sauf 'prévu')
    rendezvous_list = RendezVous.objects.filter(
        medecin_id=medecin
    ).exclude(
        statut='prévu'
    ).order_by('-date_rdv', '-heure_rdv')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        search = search.strip()
        terms = search.split()
        
        if len(terms) == 1:
            rendezvous_list = rendezvous_list.filter(
                Q(patient_id__nom__icontains=terms[0]) |
                Q(patient_id__prenom__icontains=terms[0])
            )
        elif len(terms) >= 2:
            first = terms[0]
            second = terms[1]
            rendezvous_list = rendezvous_list.filter(
                Q(patient_id__nom__icontains=first, patient_id__prenom__icontains=second) |
                Q(patient_id__nom__icontains=second, patient_id__prenom__icontains=first)
            )
    
    # Filtre par statut
    statut = request.GET.get('statut')
    if statut:
        rendezvous_list = rendezvous_list.filter(statut=statut)
    
    # Pagination - 5 éléments par page
    paginator = Paginator(rendezvous_list, 5)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Si page n'est pas un entier, afficher la première page
        page_obj = paginator.page(1)
    except EmptyPage:
        # Si page est hors limites, afficher la dernière page
        page_obj = paginator.page(paginator.num_pages)
    
    context = {
        'medecin': medecin,
        'rendezvous': page_obj,  # L'objet page, pas la liste complète
        'page_obj': page_obj,    # Pour la pagination
        'paginator': paginator,  # Pour la pagination
        'is_paginated': paginator.num_pages > 1,  # Vérifier si pagination nécessaire
    }
    
    return render(request, 'RDV/historique_medecin.html', context)
