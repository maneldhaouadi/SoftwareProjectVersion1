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



#Liste des RDV prévu
class RendezVousListView(ListView):
    model = RendezVous
    template_name = 'RDV/liste_rdv.html'
    context_object_name = 'rdvs'

    def get_queryset(self):
        # On ne récupère que les RDV "prévu"
        qs = super().get_queryset().filter(statut='prévu')
        # Tri par date et heure
        return qs.order_by('date_rdv', 'heure_rdv')

#Liste des RDV historique
class RendezVousHistoriqueListView(ListView):
    model = RendezVous
    template_name = 'RDV/historique_rdv.html'  # nouveau template
    context_object_name = 'rdvs'

    def get_queryset(self):
        # On récupère uniquement les RDV annulés ou terminés
        return super().get_queryset().filter(statut__in=['annulé', 'terminé']).order_by('-date_rdv', '-heure_rdv')

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
        messages.success(request, "Le rendez-vous a été annulé avec succès.")
    else:
        messages.warning(request, "Impossible d'annuler ce rendez-vous.")
    return redirect('liste_rdv')


def historique_medecin(request, medecin_id):
    # Récupérer le médecin ou retourner 404 s'il n'existe pas
    medecin = get_object_or_404(Employe, id=medecin_id, role='medecin')

    # Récupérer les rendez-vous sauf ceux avec statut 'prévu'
    rendezvous = (
        RendezVous.objects
        .filter(medecin_id=medecin)
        .exclude(statut='prévu')        # <-- ICI
        .order_by('-date_rdv', '-heure_rdv')
    )

    context = {
        'medecin': medecin,
        'rendezvous': rendezvous
    }#tb3th lil template

    return render(request, 'RDV/historique_medecin.html', context)
