from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import RendezVous
from .forms import RendezVousForm
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError



class RendezVousListView(ListView):
    model = RendezVous
    template_name = 'RDV/liste_rdv.html'
    context_object_name = 'rdvs'
    ordering = ['date_rdv', 'heure_rdv']

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

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        # Supprimer le champ statut à l'ajout
        if 'statut' in form.fields:
            del form.fields['statut']
        return form

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


class RendezVousUpdateView(UpdateView):
    model = RendezVous
    form_class = RendezVousForm
    template_name = 'RDV/update_rdv.html'
    success_url = reverse_lazy('liste_rdv')

    def form_valid(self, form):
        try:
            # Validation des conflits en excluant l'objet actuel
            validate_rdv(form, instance=self.object)
        except ValidationError as e:
            # Ajoute les erreurs non liées au formulaire pour affichage
            form.add_error(None, e)
            return self.form_invalid(form)

        # Les validateurs de modèle (champ et clean()) s'appliquent automatiquement
        return super().form_valid(form)


