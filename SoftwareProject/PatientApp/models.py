from django.db import models

# Create your models here.

class Patient(models.Model):
    SEXE_CHOICES = [
        ('Homme', 'Homme'),
        ('Femme', 'Femme'),
    ]

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    dateNaissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)
    dossier = models.FileField(upload_to='dossiers_patients/')  # <-- fichier uploadé

    def __str__(self):
        return f"{self.nom} {self.prenom}"