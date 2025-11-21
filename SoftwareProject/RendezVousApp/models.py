from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from PatientApp.models import Patient
from EmployeApp.models import Employe
# Fonctions validateurs

def validate_date_future(value):
    """Valide que la date du rendez-vous n'est pas dans le passé."""
    if value < timezone.localdate():
        raise ValidationError("La date du rendez-vous ne peut pas être dans le passé.")
    
       # 2 Interdire samedi (5) et dimanche (6)
    # weekday() : lundi=0 ... dimanche=6
    if value.weekday() in [5, 6]:
        raise ValidationError("Les rendez-vous ne sont pas autorisés le samedi et le dimanche.")

def validate_heure(value):
    """Valide que l'heure est dans la plage 08:00 - 18:00"""
    if value < datetime.time(8, 0) or value > datetime.time(18, 0):
        raise ValidationError("L'heure du rendez-vous doit être entre 08:00 et 18:00.")

def validate_patient_id(value):
    """Valide que l'ID patient est positif."""
    if value <= 0:
        raise ValidationError("L'ID du patient doit être un entier positif.")

def validate_medecin_id(value):
    """Valide que l'ID médecin est positif."""
    if value <= 0:
        raise ValidationError("L'ID du médecin doit être un entier positif.")


class RendezVous(models.Model):
    
    patient_id = models.ForeignKey(Patient,on_delete=models.CASCADE,related_name='rendezvous',db_column='patient_id' )
    medecin_id = models.ForeignKey(Employe, on_delete=models.CASCADE, limit_choices_to={'role': 'medecin'}, #Seuls les médecins seront affichés dans le formulaire
    related_name='rendezvous_medecin',db_column='medecin_id')
    date_rdv = models.DateField(validators=[validate_date_future])
    heure_rdv = models.TimeField(validators=[validate_heure])
    statut = models.CharField(
        max_length=20,
        choices=[
            ('prévu', 'Prévu'),
            ('annulé', 'Annulé'),
            ('terminé', 'Terminé')
        ],
        default='prévu'
    )
    def clean(self):
        """Validation globale sur l'objet entier"""
        if self.date_rdv and self.heure_rdv:  # <-- vérifier qu'ils ne sont pas None
            rdv_datetime = datetime.datetime.combine(self.date_rdv, self.heure_rdv)
            rdv_datetime = timezone.make_aware(rdv_datetime, timezone.get_current_timezone())
            now = timezone.now()
            if rdv_datetime < now:
                raise ValidationError("Le rendez-vous ne peut pas être dans le passé.")
    # sinon on ne fait rien, car les validateurs individuels géreront les champs vides


    def __str__(self):
        return f"Rdv {self.id}: Patient {self.nom} {self.prenom} avec Médecin {self.nom} {self.prenom} le {self.date_rdv} à {self.heure_rdv} ({self.statut})"
