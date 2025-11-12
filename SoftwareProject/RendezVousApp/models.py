# Create your models here.
from django.shortcuts import render
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime


class RendezVous(models.Model):
    patient_id = models.IntegerField()   # ID du patient
    medecin_id = models.IntegerField()   # ID du médecin
    date_rdv = models.DateField()        # Date du rendez-vous
    heure_rdv = models.TimeField()       # Heure du rendez-vous
    statut = models.CharField(
        max_length=20,
        choices=[
            ('prévu', 'Prévu'),
            ('annulé', 'Annulé'),
            ('terminé', 'Terminé')
        ],
        default='prévu'
    )

    # Vérifier si le rendez-vous est dans le passé
    #validation globale sur l’objet entier

    def clean(self):
        # Combine date et heure du rendez-vous
        rdv_datetime = datetime.datetime.combine(self.date_rdv, self.heure_rdv)
        
        # Rendre le datetime aware avec le fuseau courant
        rdv_datetime = timezone.make_aware(rdv_datetime, timezone.get_current_timezone())
        
        # Obtenir la date et l'heure actuelles (aware)
        now = timezone.now()
        
        # Vérifier si le rendez-vous est dans le passé
        if rdv_datetime < now:
            raise ValidationError("Le rendez-vous ne peut pas être dans le passé.")

    
    def __str__(self):
        return f"Rdv {self.id}: Patient {self.patient_id} avec Médecin {self.medecin_id} le {self.date_rdv} à {self.heure_rdv} ({self.statut})"

