from django.db import models
from django.core.validators import RegexValidator

class Patient(models.Model):
    SEXE_CHOICES = [
        ('Homme', 'Homme'),
        ('Femme', 'Femme'),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    dateNaissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    num_tel = models.CharField(
        max_length=8,
        validators=[
            RegexValidator(
                regex=r'^[2-9]\d{7}$',
                message='Le numéro de téléphone doit être un numéro tunisien valide à 8 chiffres.'
            )
        ],
        blank=True,  # formulaire peut rester vide
        null=True    # permet NULL en base pour anciens patients
    )
    dossier = models.FileField(upload_to='dossiers_patients/')

    def __str__(self):
        return f"{self.nom} {self.prenom}"
