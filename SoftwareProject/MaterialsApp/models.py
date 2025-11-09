from django.db import models

class EtatMateriel(models.TextChoices):
    EN_SERVICE = 'EN_SERVICE', 'EN_SERVICE'
    EN_MAINTENANCE = 'EN_MAINTENANCE', 'EN_MAINTENANCE'
    HORS_SERVICE = 'HORS_SERVICE', 'HORS_SERVICE'
    EN_PRET = 'EN_PRET', 'EN_PRET'

class MaterielMedical(models.Model):
    IdMaterial = models.AutoField(primary_key=True)
    Nom = models.CharField(max_length=100)
    Type = models.CharField(max_length=50)
    Reference = models.CharField(max_length=50)
    Etat = models.CharField(
        max_length=20,
        choices=EtatMateriel.choices,
        default=EtatMateriel.EN_SERVICE
    )
    Quantite = models.PositiveIntegerField()
    PrixAchat = models.DecimalField(max_digits=10, decimal_places=2)
    DateAcquisition = models.DateField()
    DateExpiration = models.DateField()

    def __str__(self):
        return f"{self.Nom} ({self.Etat})"
